"""
Availability service — orchestrates the full analysis pipeline:

    upload -> PaddleOCR -> Gemini (structured JSON) -> Firestore search
           -> alternatives for unavailable medicines -> dashboard payload
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.models.schemas import (
    AbbreviationMeaning,
    AlternativeResult,
    FrequencyInfo,
    InventoryMatch,
    MapPharmacy,
    MapPharmacyMedicine,
    MedicineResult,
    Pharmacy,
    PrescriptionAnalysis,
    UserLocation,
)
from app.services.firestore_service import DataStore, get_store
from app.services.llm_service import LLMError, LLMService
from app.services.ocr_service import OCRResult, OCRService
from app.utils.geo import haversine_km, strengths_match

logger = logging.getLogger(__name__)

_LOW_STOCK_THRESHOLD = 10     # below this the medicine is flagged "limited"
_MAX_MATCHES_PER_MEDICINE = 8
_MAX_MAP_PHARMACIES = 25


class AvailabilityService:
    def __init__(self) -> None:
        self._ocr = OCRService()
        self._llm = LLMService()

    # ------------------------------------------------------------------
    # Pipeline entry point
    # ------------------------------------------------------------------

    async def analyze(
        self,
        data: bytes,
        content_type: Optional[str],
        filename: str,
        lat: Optional[float],
        lng: Optional[float],
    ) -> PrescriptionAnalysis:
        started = time.perf_counter()
        store = get_store()

        # 1) OCR or direct Gemini Vision -----------------------------------
        from app.services.ocr_service import paddle_available
        ocr_text: str = ""
        ocr_confidence: float = 0.0
        ocr_pages: int = 1

        if paddle_available():
            ocr_result: OCRResult = await asyncio.to_thread(
                self._ocr.extract_text, data, content_type, filename
            )
            ocr_text = ocr_result.text
            ocr_confidence = ocr_result.confidence
            ocr_pages = ocr_result.pages
            logger.info("OCR extracted %d characters (confidence %.2f)", len(ocr_text), ocr_confidence)
            extraction = await self._llm.extract_prescription(ocr_text)
        else:
            logger.info("PaddleOCR unavailable — sending image directly to Gemini Vision")
            extraction = await self._llm.extract_prescription_from_image(data, content_type)
            ocr_text = "[direct image analysis — OCR not installed]"
            ocr_confidence = float(extraction.get("overall_confidence") or 0.0)
        medicines_in: list[dict[str, Any]] = extraction.get("medicines", [])

        # 3) Firestore availability for each medicine ----------------------
        results: list[MedicineResult] = []
        for med in medicines_in:
            matches = await self._search_matches(store, med, lat, lng)
            best = self._pick_best(matches)
            availability = self._availability_status(matches, best)
            results.append(
                MedicineResult(
                    name=str(med.get("name") or "").strip() or "Unknown medicine",
                    generic_name=med.get("generic_name"),
                    strength=med.get("strength"),
                    form=med.get("form"),
                    frequency=self._build_frequency(med),
                    duration=med.get("duration"),
                    instructions=med.get("instructions"),
                    confidence=float(med.get("confidence") or 0.0),
                    available=best is not None and best.in_stock,
                    availability=availability,
                    best_match=best,
                    matches=matches[:_MAX_MATCHES_PER_MEDICINE],
                )
            )

        # 4) Alternatives for medicines that could not be found ------------
        unavailable: list[dict[str, Any]] = []
        for index, result in enumerate(results):
            if not result.available:
                unavailable.append(
                    {
                        "index": index,
                        "name": result.name,
                        "generic": result.generic_name,
                        "strength": result.strength,
                        "preset": [a for a in (medicines_in[index].get("alternative_brands") or []) if a],
                    }
                )

        if unavailable:
            await self._attach_alternatives(store, results, unavailable, lat, lng)

        # 5) Assemble the dashboard payload --------------------------------
        pharmacies = self._build_map_pharmacies(results, lat, lng)
        overall_confidence = self._overall_confidence(extraction, results)

        warnings = [str(w) for w in (extraction.get("warnings") or []) if w]
        if not results:
            warnings.append(
                "No medicines could be identified on this prescription. "
                "Try a sharper, well-lit photo of the medication section."
            )

        return PrescriptionAnalysis(
            id=uuid.uuid4().hex[:12],
            created_at=datetime.now(timezone.utc),
            summary=str(extraction.get("summary") or ""),
            overall_confidence=overall_confidence,
            patient_name=extraction.get("patient_name"),
            doctor_name=extraction.get("doctor_name"),
            prescribed_date=extraction.get("prescribed_date"),
            warnings=warnings,
            medicines=results,
            pharmacies=pharmacies,
            user_location=UserLocation(lat=lat, lng=lng) if lat is not None and lng is not None else None,
            ocr_text=ocr_text,
            ocr_confidence=ocr_confidence,
            processing_ms=int((time.perf_counter() - started) * 1000),
            demo_mode=store.is_demo,
        )

    # ------------------------------------------------------------------
    # Firestore search
    # ------------------------------------------------------------------

    async def _search_matches(
        self,
        store: DataStore,
        med: dict[str, Any] | MedicineResult,
        lat: Optional[float],
        lng: Optional[float],
    ) -> list[InventoryMatch]:
        """Search the data store by brand (then generic) and hydrate inventory rows."""
        if isinstance(med, MedicineResult):
            brand, generic = med.name, med.generic_name
        else:
            brand, generic = med.get("name"), med.get("generic_name")

        medicine_docs = await asyncio.to_thread(store.search_medicines, brand, generic)
        if not medicine_docs:
            return []

        docs_by_id = {doc["id"]: doc for doc in medicine_docs}
        inventory_rows = await asyncio.to_thread(store.get_inventory, list(docs_by_id))
        if not inventory_rows:
            return []

        pharmacies = await asyncio.to_thread(
            store.get_pharmacies, list({row["pharmacy_id"] for row in inventory_rows})
        )

        matches: list[InventoryMatch] = []
        for row in inventory_rows:
            pharmacy_data = pharmacies.get(row["pharmacy_id"])
            if not pharmacy_data:
                continue
            medicine_doc = docs_by_id.get(row["medicine_id"], {})
            stock = int(row.get("stock") or 0)

            distance = None
            if lat is not None and lng is not None:
                distance = round(
                    haversine_km(lat, lng, float(pharmacy_data["lat"]), float(pharmacy_data["lng"])), 1
                )

            matches.append(
                InventoryMatch(
                    medicine_id=row["medicine_id"],
                    brand=str(medicine_doc.get("brand") or brand or ""),
                    generic=medicine_doc.get("generic"),
                    strength=medicine_doc.get("strength"),
                    form=medicine_doc.get("form"),
                    price=float(row["price"]) if row.get("price") is not None else None,
                    stock=stock,
                    in_stock=stock > 0,
                    strength_match=strengths_match(
                        generic_strength(med), medicine_doc.get("strength")
                    ),
                    pharmacy=Pharmacy(
                        id=pharmacy_data["id"],
                        name=pharmacy_data.get("name", ""),
                        branch=pharmacy_data.get("branch"),
                        address=pharmacy_data.get("address", ""),
                        city=pharmacy_data.get("city", ""),
                        phone=pharmacy_data.get("phone"),
                        rating=pharmacy_data.get("rating"),
                        open_hours=pharmacy_data.get("open_hours"),
                        lat=float(pharmacy_data["lat"]),
                        lng=float(pharmacy_data["lng"]),
                        distance_km=distance,
                    ),
                    updated_at=row.get("updated_at"),
                )
            )

        # In-stock first, then strength match, then distance
        matches.sort(
            key=lambda m: (
                not m.in_stock,
                m.strength_match is False,   # False sinks; None (unknown) stays neutral
                m.pharmacy.distance_km if m.pharmacy.distance_km is not None else 9999,
                -(m.pharmacy.rating or 0),
            )
        )
        return matches

    # ------------------------------------------------------------------
    # Alternatives
    # ------------------------------------------------------------------

    async def _attach_alternatives(
        self,
        store: DataStore,
        results: list[MedicineResult],
        unavailable: list[dict[str, Any]],
        lat: Optional[float],
        lng: Optional[float],
    ) -> None:
        """Ask Gemini for alternative brands and check them against the database."""
        llm_brands: dict[int, list[str]] = {}
        try:
            llm_brands = await self._llm.suggest_alternatives(
                [
                    {"index": item["index"], "name": item["name"], "generic": item["generic"], "strength": item["strength"]}
                    for item in unavailable
                ]
            )
        except LLMError as exc:
            logger.warning("Could not fetch alternatives from Gemini: %s", exc)

        for item in unavailable:
            index = item["index"]
            result = results[index]

            seen_brands: set[str] = set()
            brands: list[str] = []
            for brand in item.get("preset", []) + llm_brands.get(index, []):
                normalised = brand.strip().lower()
                if normalised and normalised not in seen_brands and normalised != result.name.strip().lower():
                    seen_brands.add(normalised)
                    brands.append(brand.strip())
            brands = brands[:4]

            alternatives: list[AlternativeResult] = []
            for brand in brands:
                alt_matches = await self._search_matches(
                    store, {"name": brand, "generic_name": result.generic_name}, lat, lng
                )
                alt_best = self._pick_best(alt_matches)
                alternatives.append(
                    AlternativeResult(
                        brand=brand,
                        found=alt_best is not None,
                        best_match=alt_best,
                        matches=alt_matches[:4],
                    )
                )
                # If an alternative is available and nothing else was, surface it
                if alt_best is not None and not result.available:
                    result.available = True
                    if result.availability in ("unknown", "out_of_stock"):
                        result.availability = (
                            "in_stock" if alt_best.stock >= _LOW_STOCK_THRESHOLD else "limited"
                        )
                    if result.best_match is None:
                        result.best_match = alt_best

            result.alternatives = alternatives

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_best(matches: list[InventoryMatch]) -> Optional[InventoryMatch]:
        """Best in-stock match, preferring exact strength and proximity."""
        candidates = [m for m in matches if m.in_stock]
        if not candidates:
            return None
        same_strength = [m for m in candidates if m.strength_match is not False]
        pool = same_strength or candidates
        return min(
            pool,
            key=lambda m: (
                m.pharmacy.distance_km if m.pharmacy.distance_km is not None else 9999,
                m.price if m.price is not None else 99999,
            ),
        )

    @staticmethod
    def _availability_status(
        matches: list[InventoryMatch], best: Optional[InventoryMatch]
    ) -> str:
        if best is not None:
            return "in_stock" if best.stock >= _LOW_STOCK_THRESHOLD else "limited"
        if matches:
            return "out_of_stock"
        return "unknown"

    @staticmethod
    def _build_frequency(med: dict[str, Any]) -> Optional[FrequencyInfo]:
        raw = med.get("frequency_raw")
        interpretation = med.get("frequency_interpretation")
        meanings_raw = med.get("abbreviation_meanings") or []
        meanings = [
            AbbreviationMeaning(abbreviation=str(m.get("abbreviation", "")), meaning=str(m.get("meaning", "")))
            for m in meanings_raw
            if isinstance(m, dict) and m.get("abbreviation")
        ]
        if not (raw or interpretation or meanings):
            return None
        return FrequencyInfo(
            raw=raw,
            interpretation=interpretation,
            times_per_day=med.get("times_per_day"),
            abbreviation_meanings=meanings,
        )

    @staticmethod
    def _overall_confidence(extraction: dict[str, Any], results: list[MedicineResult]) -> float:
        try:
            value = float(extraction.get("overall_confidence") or 0)
            if value > 0:
                return round(min(max(value, 0.0), 1.0), 2)
        except (TypeError, ValueError):
            pass
        if results:
            return round(sum(m.confidence for m in results) / len(results), 2)
        return 0.0

    @staticmethod
    def _build_map_pharmacies(
        results: list[MedicineResult], lat: Optional[float], lng: Optional[float]
    ) -> list[MapPharmacy]:
        """Deduplicate pharmacies across all medicines/alternatives for the map."""
        grouped: dict[str, MapPharmacy] = {}

        def collect(match: InventoryMatch) -> None:
            entry = grouped.get(match.pharmacy.id)
            if entry is None:
                entry = MapPharmacy(pharmacy=match.pharmacy)
                grouped[match.pharmacy.id] = entry
            entry.medicines.append(
                MapPharmacyMedicine(
                    brand=match.brand,
                    strength=match.strength,
                    price=match.price,
                    stock=match.stock,
                    in_stock=match.in_stock,
                )
            )

        for medicine in results:
            for match in medicine.matches:
                collect(match)
            for alternative in medicine.alternatives:
                for match in alternative.matches:
                    collect(match)

        pharmacies = list(grouped.values())
        for entry in pharmacies:
            # Most available first inside the popup
            entry.medicines.sort(key=lambda m: (not m.in_stock, m.brand))
        pharmacies.sort(
            key=lambda p: (
                p.pharmacy.distance_km if p.pharmacy.distance_km is not None else 9999,
                -len([m for m in p.medicines if m.in_stock]),
            )
        )
        return pharmacies[:_MAX_MAP_PHARMACIES]


def generic_strength(med: dict[str, Any] | MedicineResult) -> Optional[str]:
    if isinstance(med, MedicineResult):
        return med.strength
    return med.get("strength")
