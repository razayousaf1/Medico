"""
Import the Pakistan medicines and Lahore pharmacy datasets into Firestore.

Usage:
    cd backend
    pip install -r requirements.txt
    python scripts/import_dataset.py

What it does:
    1. Reads Pakistan_Medicines_Reference_List.xlsx -> medicines collection
    2. Reads Lahore_Pharmacy_Branches.xlsx -> pharmacies collection
       (geocodes each address via Nominatim, cached in .geocache.json)
    3. Generates synthetic inventory linking medicines to pharmacies
    4. Upserts everything into Firestore

Safe to re-run: documents are upserted with deterministic IDs.
"""

import argparse
import base64
import json
import logging
import os
import random
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import openpyxl  # noqa: E402
import requests  # noqa: E402
from slugify import slugify  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.utils.geo import _parse_strength  # noqa: E402

logger = logging.getLogger("import_dataset")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

DATASET_DIR = Path.home() / "Desktop"
MEDICINES_FILE = DATASET_DIR / "Pakistan_Medicines_Reference_List.xlsx"
PHARMACIES_FILE = DATASET_DIR / "Lahore_Pharmacy_Branches.xlsx"
GEOCACHE_FILE = Path(__file__).resolve().parent / ".geocache.json"

BATCH_SIZE = 10
INTER_BATCH_DELAY = 3.0  # seconds between Firestore write batches
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_DELAY = 1.1  # seconds between requests

_GENERIC_STOPWORDS = {
    "acid",
    "sodium",
    "potassium",
    "hydrochloride",
    "trihydrate",
    "benzoate",
    "butylbromide",
}

_RANDOM_SEED = 42


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_geocache() -> dict[str, tuple[float, float]]:
    if GEOCACHE_FILE.exists():
        try:
            data = json.loads(GEOCACHE_FILE.read_text(encoding="utf-8"))
            return {k: tuple(v) for k, v in data.items()}  # type: ignore[misc]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Could not read geocache, starting fresh")
    return {}


def save_geocache(cache: dict[str, tuple[float, float]]) -> None:
    GEOCACHE_FILE.write_text(
        json.dumps({k: list(v) for k, v in cache.items()}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def generic_keywords(generic: Optional[str]) -> list[str]:
    if not generic:
        return []
    tokens = [
        t.strip().lower()
        for t in re.split(r"[\s/]+", generic.replace("+", " "))
        if t.strip()
    ]
    return [t for t in tokens if t and t not in _GENERIC_STOPWORDS]


def parse_price(value: Optional[str]) -> Optional[float]:
    """Extract a single representative PKR price from strings like 'Rs. 150-220/strip'."""
    if not value:
        return None
    text = str(value).lower().replace(",", "")
    # Look for the first numeric range e.g. 150-220
    range_match = re.search(r"(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)", text)
    if range_match:
        low, high = float(range_match.group(1)), float(range_match.group(2))
        return round((low + high) / 2.0)
    # Otherwise first standalone number
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if numbers:
        return round(float(numbers[0]))
    return None


def split_brand_strength(brand_text: Optional[str]) -> tuple[str, Optional[str]]:
    if not brand_text:
        return "Unknown", None
    text = str(brand_text).strip()
    parsed = _parse_strength(text)
    if parsed is None:
        return text, None
    number, unit = parsed
    unit = unit or ""
    # Find where the strength begins in the original string
    pattern = re.compile(r"(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|%|)?", re.IGNORECASE)
    match = pattern.search(text)
    if not match:
        return text, None
    brand = text[: match.start()].strip()
    strength = f"{int(number) if number == int(number) else number}{unit}".strip()
    if not brand:
        return text, None
    return brand, strength or None


def make_id(prefix: str, *parts: str, seen: Optional[set[str]] = None) -> str:
    base = "_".join(slugify(p, lowercase=True, separator="_") for p in parts if p)
    base = re.sub(r"_+", "_", base).strip("_")
    candidate = f"{prefix}_{base}" if prefix else base
    if not seen:
        return candidate
    if candidate not in seen:
        seen.add(candidate)
        return candidate
    for i in range(2, 1000):
        numbered = f"{candidate}_{i}"
        if numbered not in seen:
            seen.add(numbered)
            return numbered
    return candidate


# ---------------------------------------------------------------------------
# Firestore connection
# ---------------------------------------------------------------------------


def get_firestore_client() -> "firestore.Client":
    import firebase_admin
    from firebase_admin import credentials, firestore

    settings = get_settings()
    cred = None
    if settings.firebase_credentials_b64.strip():
        info = json.loads(base64.b64decode(settings.firebase_credentials_b64))
        cred = credentials.Certificate(info)
    elif settings.firebase_credentials_path.strip():
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        logger.error("No Firebase credentials configured. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_B64 in backend/.env")
        sys.exit(1)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    return firestore.client()


def write_batch(db: "firestore.Client", collection: str, docs: list[dict[str, Any]]) -> None:
    """Upsert documents in small batches with explicit pacing and retries.

    Firestore's client has its own 60s retry loop that swallows 429s and makes
    rate-limiting hard to reason about, so we disable it and handle backoff
    ourselves.
    """
    import google.api_core.exceptions

    for start in range(0, len(docs), BATCH_SIZE):
        chunk = docs[start : start + BATCH_SIZE]
        _commit_batch_with_retry(db, collection, chunk)
        if start + BATCH_SIZE < len(docs):
            time.sleep(INTER_BATCH_DELAY)
    logger.info("  %s: %d documents written", collection, len(docs))


def _commit_batch_with_retry(
    db: "firestore.Client", collection: str, chunk: list[dict[str, Any]], max_attempts: int = 5
) -> None:
    import google.api_core.exceptions

    for attempt in range(1, max_attempts + 1):
        batch = db.batch()
        for doc in chunk:
            doc_id = doc["id"]
            payload = {k: v for k, v in doc.items() if k != "id"}
            batch.set(db.collection(collection).document(doc_id), payload, merge=True)
        try:
            # Disable the client-level retry so we get 429s immediately and can
            # back off without holding the RPC open for 60 seconds.
            batch.commit(retry=None)
            return
        except (
            google.api_core.exceptions.ResourceExhausted,
            google.api_core.exceptions.RetryError,
            google.api_core.exceptions.DeadlineExceeded,
        ) as exc:
            if attempt == max_attempts:
                raise
            sleep = (2 ** attempt) + random.uniform(0, 1)
            reason = type(exc).__name__
            logger.warning("Firestore %s (attempt %d/%d), retrying in %.1fs", reason, attempt, max_attempts, sleep)
            time.sleep(sleep)
        except Exception:
            raise


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------


def parse_medicines() -> list[dict[str, Any]]:
    logger.info("Reading medicines from %s", MEDICINES_FILE)
    wb = openpyxl.load_workbook(MEDICINES_FILE, read_only=True, data_only=True)
    ws = wb["Medicines List"]

    medicines: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[1]:
            continue

        brand_raw = str(row[1]).strip()
        generic = str(row[2]).strip() if row[2] else None
        category = str(row[3]).strip() if row[3] else None
        notes = str(row[7]).strip() if row[7] else None

        brand, strength = split_brand_strength(brand_raw)
        if not strength and generic:
            _, strength = split_brand_strength(generic)
        price = parse_price(row[5])

        doc_id = make_id("md", brand, strength or "", seen=seen_ids)
        medicines.append(
            {
                "id": doc_id,
                "brand": brand,
                "brand_lower": brand.lower(),
                "generic": generic,
                "generic_lower": (generic or "").lower(),
                "generic_keywords": generic_keywords(generic),
                "strength": strength,
                "category": category,
                "base_price": price,
                "notes": notes,
            }
        )

    logger.info("Parsed %d medicines", len(medicines))
    return medicines


def parse_pharmacies(
    geocode: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, tuple[float, float]]]:
    logger.info("Reading pharmacies from %s", PHARMACIES_FILE)
    wb = openpyxl.load_workbook(PHARMACIES_FILE, read_only=True, data_only=True)

    cache = load_geocache()
    default_lat, default_lng = get_settings().default_lat, get_settings().default_lng
    pharmacies: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # Sheet-specific column mappings
    # (sheet_name, default_chain_name, ignored_phone_col_hint, open_hours_col_index or None)
    sheet_configs: list[tuple[str, str, Optional[str], Optional[int]]] = [
        ("Fazal Din's Pharma Plus", "Fazal Din's Pharma Plus", None, None),
        ("Servaid Pharmacy", "Servaid Pharmacy", None, 3),
        ("D.Watson & Other Chains", None, None, None),
    ]

    for sheet_name, default_chain, _, open_hours_idx in sheet_configs:
        if sheet_name not in wb.sheetnames:
            logger.warning("Sheet '%s' not found, skipping", sheet_name)
            continue

        ws = wb[sheet_name]
        header = [str(c).strip() if c else "" for c in next(ws.iter_rows(values_only=True))]

        # Resolve column indices from headers for the variable D.Watson sheet
        if sheet_name == "D.Watson & Other Chains":
            chain_col = header.index("Pharmacy Chain") if "Pharmacy Chain" in header else None
            branch_col = header.index("Branch / Area") if "Branch / Area" in header else None
            address_col = header.index("Address") if "Address" in header else None
            phone_col = None
        else:
            chain_col = None
            branch_col = header.index("Branch Name / Area") if "Branch Name / Area" in header else 1
            address_col = header.index("Address") if "Address" in header else 2
            phone_col = header.index("Phone") if "Phone" in header else 3

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or all(v is None or str(v).strip() == "" for v in row):
                continue

            if sheet_name == "D.Watson & Other Chains":
                chain = str(row[chain_col]).strip() if chain_col is not None and row[chain_col] else None
                branch = str(row[branch_col]).strip() if branch_col is not None and row[branch_col] else None
                address = str(row[address_col]).strip() if address_col is not None and row[address_col] else None
                phone = None
                open_hours = None
                # Skip generic/multi-city rows
                if not chain or chain.lower() in {"fazal din's / servaid / d.watson - other cities", "multiple"}:
                    continue
                if not branch or branch.lower() == "multiple":
                    continue
            else:
                chain = default_chain
                branch = str(row[branch_col]).strip() if branch_col is not None and row[branch_col] else None
                address = str(row[address_col]).strip() if address_col is not None and row[address_col] else None
                phone = str(row[phone_col]).strip() if phone_col is not None and row[phone_col] else None
                open_hours = (
                    str(row[open_hours_idx]).strip()
                    if open_hours_idx is not None and len(row) > open_hours_idx and row[open_hours_idx]
                    else None
                )

            if not address:
                continue

            # Try simplified area-based queries first; Nominatim struggles with
            # granular shop/unit numbers but usually resolves neighbourhoods.
            queries = []
            if branch:
                queries.append(f"{branch}, Lahore, Pakistan")
            queries.append(f"{address}, Lahore, Pakistan")

            lat, lng = _geocode_address(
                queries, cache, geocode=geocode, default=(default_lat, default_lng)
            )

            doc_id = make_id("ph", chain or "Pharmacy", branch or "Branch", seen=seen_ids)
            pharmacies.append(
                {
                    "id": doc_id,
                    "name": chain or "Pharmacy",
                    "branch": branch,
                    "address": address,
                    "city": "Lahore",
                    "phone": phone,
                    "rating": None,
                    "open_hours": open_hours,
                    "lat": lat,
                    "lng": lng,
                }
            )

    # Spread any unresolved pharmacies around Lahore centre so the map isn't
    # a single stacked pin. ~0.15° gives a city-wide spread.
    rng = random.Random(_RANDOM_SEED)
    for pharmacy in pharmacies:
        if pharmacy["lat"] == default_lat and pharmacy["lng"] == default_lng:
            pharmacy["lat"] = round(default_lat + rng.uniform(-0.12, 0.12), 6)
            pharmacy["lng"] = round(default_lng + rng.uniform(-0.12, 0.12), 6)

    logger.info("Parsed %d pharmacies", len(pharmacies))
    save_geocache(cache)
    return pharmacies, cache


def _geocode_address(
    queries: list[str],
    cache: dict[str, tuple[float, float]],
    geocode: bool,
    default: tuple[float, float],
) -> tuple[float, float]:
    cache_key = " | ".join(queries)
    if cache_key in cache:
        return cache[cache_key]
    if not geocode:
        return default

    for query in queries:
        try:
            response = requests.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1},
                headers={"User-Agent": "medico-importer/1.0 (medico-project)"},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                cache[cache_key] = (lat, lng)
                time.sleep(NOMINATIM_DELAY)
                return lat, lng
        except Exception as exc:
            logger.warning("Geocoding failed for '%s': %s", query, exc)

    logger.warning("Could not geocode %s, using Lahore centre fallback", queries)
    cache[cache_key] = default
    time.sleep(NOMINATIM_DELAY)
    return default


def generate_inventory(
    medicines: list[dict[str, Any]], pharmacies: list[dict[str, Any]], seed: int = _RANDOM_SEED
) -> list[dict[str, Any]]:
    logger.info("Generating synthetic inventory for %d medicines x %d pharmacies", len(medicines), len(pharmacies))
    rng = random.Random(seed)
    now = datetime.now(timezone.utc).isoformat()
    inventory: list[dict[str, Any]] = []

    for med in medicines:
        base_price = med.get("base_price")
        # Keep the synthetic inventory modest to stay within Firestore Spark
        # daily write quotas (~20k). ~35% coverage still gives plenty of results.
        target_count = max(1, int(len(pharmacies) * 0.35))
        selected = rng.sample(pharmacies, k=min(target_count, len(pharmacies)))
        for pharmacy in selected:
            if base_price is not None:
                price = round(base_price * rng.uniform(0.85, 1.15) / 5) * 5
            else:
                price = None
            stock = rng.randint(0, 100)
            inventory.append(
                {
                    "id": f"inv_{len(inventory) + 1:06d}",
                    "medicine_id": med["id"],
                    "pharmacy_id": pharmacy["id"],
                    "price": price,
                    "stock": stock,
                    "updated_at": now,
                }
            )

    logger.info("Generated %d inventory rows", len(inventory))
    return inventory


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Medico dataset into Firestore")
    parser.add_argument("--no-geocode", action="store_true", help="Skip Nominatim geocoding and use Lahore centre")
    parser.add_argument("--reset", action="store_true", help="Delete existing collections before import")
    args = parser.parse_args()

    if not MEDICINES_FILE.exists() or not PHARMACIES_FILE.exists():
        logger.error("Dataset files not found in %s", DATASET_DIR)
        sys.exit(1)

    db = get_firestore_client()
    now = datetime.now(timezone.utc).isoformat()

    medicines = parse_medicines()
    pharmacies, _ = parse_pharmacies(geocode=not args.no_geocode)
    inventory = generate_inventory(medicines, pharmacies)

    # Stamp updated_at
    for doc in medicines + pharmacies:
        doc["updated_at"] = now

    if args.reset:
        logger.info("Reset flag set — deleting existing collections")
        for collection in ("medicines", "pharmacies", "inventory"):
            _delete_collection(db.collection(collection))

    logger.info("Writing to Firestore...")
    write_batch(db, "pharmacies", pharmacies)
    write_batch(db, "medicines", medicines)
    write_batch(db, "inventory", inventory)
    logger.info("Done.")


def _delete_collection(collection_ref: "firestore.CollectionReference") -> None:
    docs = list(collection_ref.limit(BATCH_SIZE).stream())
    while docs:
        for doc in docs:
            doc.reference.delete()
        docs = list(collection_ref.limit(BATCH_SIZE).stream())
    logger.info("  Deleted existing %s documents", collection_ref.id)


if __name__ == "__main__":
    main()
