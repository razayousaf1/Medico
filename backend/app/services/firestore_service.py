"""
Data access layer for the `pharmacies`, `medicines` and `inventory`
Firestore collections.

Two interchangeable implementations live here:

* `FirestoreStore`  — the real thing, backed by Firebase Firestore.
* `DemoStore`       — the built-in Lahore demo dataset, used when Firebase
  credentials are absent (or fail to initialise) so the whole platform can
  run locally with zero setup.
"""

import base64
import json
import logging
from datetime import datetime, timezone
from difflib import get_close_matches
from typing import Optional

from app.core.config import get_settings
from app.services import demo_data

logger = logging.getLogger(__name__)

_IN_CHUNK = 30  # Firestore `in` queries accept at most 30 values

# Real dataset imports started in September 2026. Demo seed data is stamped
# 2026-08-29, so this cutoff hides stale demo documents until we can delete them.
_FRESH_SINCE = datetime(2026, 9, 1, tzinfo=timezone.utc)


def _is_fresh(doc: dict) -> bool:
    ts = doc.get("updated_at")
    if not ts:
        return False
    try:
        return datetime.fromisoformat(ts) >= _FRESH_SINCE
    except (ValueError, TypeError):
        return False


def _generic_keywords(generic: str | None) -> list[str]:
    stop = {"acid", "sodium", "potassium", "hydrochloride", "trihydrate", "benzoate", "butylbromide"}
    if not generic:
        return []
    tokens = [t.strip().lower() for t in generic.replace("/", " + ").replace("+", " ").split()]
    return [t for t in tokens if t and t not in stop]


class DataStore:
    """Interface both stores implement."""

    is_demo = False

    def search_medicines(self, brand: Optional[str], generic: Optional[str]) -> list[dict]:
        raise NotImplementedError

    def get_inventory(self, medicine_ids: list[str]) -> list[dict]:
        raise NotImplementedError

    def get_pharmacies(self, pharmacy_ids: list[str]) -> dict[str, dict]:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Demo (in-memory) store
# ---------------------------------------------------------------------------

class DemoStore(DataStore):
    is_demo = True

    def __init__(self) -> None:
        self._pharmacies = {p["id"]: dict(p) for p in demo_data.PHARMACIES}
        self._medicines = demo_data.enriched_medicines()
        self._inventory = demo_data.INVENTORY

    def search_medicines(self, brand: Optional[str], generic: Optional[str]) -> list[dict]:
        results: dict[str, dict] = {}

        if brand and brand.strip():
            wanted = brand.strip().lower()
            for med in self._medicines:
                if med["brand_lower"] == wanted:
                    results[med["id"]] = med

        if generic and generic.strip() and not results:
            keywords = _generic_keywords(generic)
            for med in self._medicines:
                if any(k in med["generic_keywords"] for k in keywords):
                    results[med["id"]] = med

        # Fuzzy fallback so slightly-off OCR/brand names still match
        if brand and brand.strip() and not results:
            wanted = brand.strip().lower()
            candidates = [med["brand_lower"] for med in self._medicines]
            close = get_close_matches(wanted, candidates, n=3, cutoff=0.72)
            for med in self._medicines:
                if med["brand_lower"] in close:
                    results[med["id"]] = med

        return list(results.values())

    def get_inventory(self, medicine_ids: list[str]) -> list[dict]:
        wanted = set(medicine_ids)
        return [dict(row) for row in self._inventory if row["medicine_id"] in wanted]

    def get_pharmacies(self, pharmacy_ids: list[str]) -> dict[str, dict]:
        return {pid: dict(self._pharmacies[pid]) for pid in pharmacy_ids if pid in self._pharmacies}


# ---------------------------------------------------------------------------
# Firestore store
# ---------------------------------------------------------------------------

class FirestoreStore(DataStore):
    is_demo = False

    def __init__(self) -> None:
        import firebase_admin
        from firebase_admin import credentials, firestore  # noqa: F401  (import binds versions)

        settings = get_settings()

        cred = None
        if settings.firebase_credentials_b64.strip():
            info = json.loads(base64.b64decode(settings.firebase_credentials_b64))
            cred = credentials.Certificate(info)
        elif settings.firebase_credentials_path.strip():
            cred = credentials.Certificate(settings.firebase_credentials_path)

        app_options = {}
        if settings.firestore_project_id.strip():
            app_options["projectId"] = settings.firestore_project_id

        if "medico" not in firebase_admin._apps:
            if cred is not None:
                firebase_admin.initialize_app(cred, name="medico")
            else:
                # Application Default Credentials (Cloud Run, GCE, gcloud CLI …)
                firebase_admin.initialize_app(options=app_options or None, name="medico")

        self._db = firestore.client(app=firebase_admin.get_app(name="medico"))

    def search_medicines(self, brand: Optional[str], generic: Optional[str]) -> list[dict]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        results: dict[str, dict] = {}

        if brand and brand.strip():
            query = (
                self._db.collection("medicines")
                .where(filter=FieldFilter("brand_lower", "==", brand.strip().lower()))
                .limit(10)
            )
            for snap in query.stream():
                doc = {"id": snap.id, **(snap.to_dict() or {})}
                if _is_fresh(doc):
                    results[snap.id] = doc

        if generic and generic.strip() and not results:
            keywords = _generic_keywords(generic)
            for keyword in keywords[:3]:  # try the main INN tokens
                query = (
                    self._db.collection("medicines")
                    .where(filter=FieldFilter("generic_keywords", "array_contains", keyword))
                    .limit(10)
                )
                for snap in query.stream():
                    doc = {"id": snap.id, **(snap.to_dict() or {})}
                    if _is_fresh(doc):
                        results[snap.id] = doc

        return list(results.values())

    def get_inventory(self, medicine_ids: list[str]) -> list[dict]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        unique = list(dict.fromkeys(medicine_ids))
        rows: list[dict] = []
        for start in range(0, len(unique), _IN_CHUNK):
            chunk = unique[start : start + _IN_CHUNK]
            query = (
                self._db.collection("inventory")
                .where(filter=FieldFilter("medicine_id", "in", chunk))
                .limit(300)
            )
            for snap in query.stream():
                doc = {"id": snap.id, **(snap.to_dict() or {})}
                if _is_fresh(doc):
                    rows.append(doc)
        return rows

    def get_pharmacies(self, pharmacy_ids: list[str]) -> dict[str, dict]:
        unique = list(dict.fromkeys(pharmacy_ids))
        out: dict[str, dict] = {}
        for start in range(0, len(unique), _IN_CHUNK):
            chunk = unique[start : start + _IN_CHUNK]
            refs = [self._db.collection("pharmacies").document(pid) for pid in chunk]
            for snap in self._db.get_all(refs):
                if snap.exists:
                    doc = {"id": snap.id, **(snap.to_dict() or {})}
                    if _is_fresh(doc):
                        out[snap.id] = doc
        return out


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_store: Optional[DataStore] = None


def get_store() -> DataStore:
    """Return the process-wide store, initialising it on first use."""
    global _store
    if _store is not None:
        return _store

    settings = get_settings()
    if settings.firebase_configured:
        try:
            _store = FirestoreStore()
            logger.info("Firestore connected — serving live pharmacy data")
            return _store
        except Exception as exc:  # noqa: BLE001 — degrade gracefully, never crash
            logger.warning("Firestore init failed (%s). Falling back to demo data.", exc)

    logger.warning("Firebase not configured — using the built-in demo dataset")
    _store = DemoStore()
    return _store
