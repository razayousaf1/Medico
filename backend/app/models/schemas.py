"""Pydantic response models shared by the API and the frontend contract."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Shared building blocks
# ------------------------------------------------------------------

class AbbreviationMeaning(BaseModel):
    """A prescription abbreviation plus its plain-language meaning."""
    abbreviation: str
    meaning: str


class FrequencyInfo(BaseModel):
    """How often a medicine should be taken."""
    raw: Optional[str] = None                 # e.g. "1-0-1"
    interpretation: Optional[str] = None      # e.g. "One tablet in the morning and at night"
    times_per_day: Optional[int] = None
    abbreviation_meanings: list[AbbreviationMeaning] = Field(default_factory=list)


class Pharmacy(BaseModel):
    id: str
    name: str
    branch: Optional[str] = None
    address: str = ""
    city: str = ""
    phone: Optional[str] = None
    rating: Optional[float] = None
    open_hours: Optional[str] = None
    lat: float
    lng: float
    distance_km: Optional[float] = None


class InventoryMatch(BaseModel):
    """A single (medicine, pharmacy) availability row from Firestore."""
    medicine_id: str
    brand: str
    generic: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    price: Optional[float] = None            # PKR
    stock: int = 0
    in_stock: bool = False
    strength_match: Optional[bool] = None    # None when strength is unknown
    pharmacy: Pharmacy
    updated_at: Optional[str] = None


class AlternativeResult(BaseModel):
    """An alternative brand suggested by Gemini and checked against inventory."""
    brand: str
    found: bool = False
    best_match: Optional[InventoryMatch] = None
    matches: list[InventoryMatch] = Field(default_factory=list)


class UserLocation(BaseModel):
    lat: float
    lng: float


# ------------------------------------------------------------------
# Medicine-level result
# ------------------------------------------------------------------

class MedicineResult(BaseModel):
    name: str
    generic_name: Optional[str] = None
    strength: Optional[str] = None
    form: Optional[str] = None
    frequency: Optional[FrequencyInfo] = None
    duration: Optional[str] = None
    instructions: Optional[str] = None
    confidence: float = 0.0
    available: bool = False
    availability: Literal["in_stock", "limited", "out_of_stock", "unknown"] = "unknown"
    best_match: Optional[InventoryMatch] = None
    matches: list[InventoryMatch] = Field(default_factory=list)
    alternatives: list[AlternativeResult] = Field(default_factory=list)


# ------------------------------------------------------------------
# Map payload
# ------------------------------------------------------------------

class MapPharmacyMedicine(BaseModel):
    brand: str
    strength: Optional[str] = None
    price: Optional[float] = None
    stock: int = 0
    in_stock: bool = False


class MapPharmacy(BaseModel):
    """A pharmacy on the dashboard map together with what it stocks."""
    pharmacy: Pharmacy
    medicines: list[MapPharmacyMedicine] = Field(default_factory=list)


# ------------------------------------------------------------------
# Top-level API response
# ------------------------------------------------------------------

class PrescriptionAnalysis(BaseModel):
    id: str
    created_at: datetime
    summary: str = ""
    overall_confidence: float = 0.0
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    prescribed_date: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)
    medicines: list[MedicineResult] = Field(default_factory=list)
    pharmacies: list[MapPharmacy] = Field(default_factory=list)
    user_location: Optional[UserLocation] = None
    ocr_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    processing_ms: int = 0
    demo_mode: bool = False


# ------------------------------------------------------------------
# Health check
# ------------------------------------------------------------------

class HealthStatus(BaseModel):
    status: str = "ok"
    app_env: str = "development"
    gemini_configured: bool = False
    firebase_configured: bool = False
    using_demo_data: bool = True
    ocr_available: bool = False
    model: str = ""
