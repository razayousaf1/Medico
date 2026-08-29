/** Types mirroring the backend Pydantic response models (app/models/schemas.py). */

export type AvailabilityStatus = "in_stock" | "limited" | "out_of_stock" | "unknown";

export interface AbbreviationMeaning {
  abbreviation: string;
  meaning: string;
}

export interface FrequencyInfo {
  raw: string | null;
  interpretation: string | null;
  times_per_day: number | null;
  abbreviation_meanings: AbbreviationMeaning[];
}

export interface Pharmacy {
  id: string;
  name: string;
  branch: string | null;
  address: string;
  city: string;
  phone: string | null;
  rating: number | null;
  open_hours: string | null;
  lat: number;
  lng: number;
  distance_km: number | null;
}

export interface InventoryMatch {
  medicine_id: string;
  brand: string;
  generic: string | null;
  strength: string | null;
  form: string | null;
  price: number | null;
  stock: number;
  in_stock: boolean;
  strength_match: boolean | null;
  pharmacy: Pharmacy;
  updated_at: string | null;
}

export interface AlternativeResult {
  brand: string;
  found: boolean;
  best_match: InventoryMatch | null;
  matches: InventoryMatch[];
}

export interface MedicineResult {
  name: string;
  generic_name: string | null;
  strength: string | null;
  form: string | null;
  frequency: FrequencyInfo | null;
  duration: string | null;
  instructions: string | null;
  confidence: number;
  available: boolean;
  availability: AvailabilityStatus;
  best_match: InventoryMatch | null;
  matches: InventoryMatch[];
  alternatives: AlternativeResult[];
}

export interface MapPharmacyMedicine {
  brand: string;
  strength: string | null;
  price: number | null;
  stock: number;
  in_stock: boolean;
}

export interface MapPharmacy {
  pharmacy: Pharmacy;
  medicines: MapPharmacyMedicine[];
}

export interface UserLocation {
  lat: number;
  lng: number;
}

export interface PrescriptionAnalysis {
  id: string;
  created_at: string;
  summary: string;
  overall_confidence: number;
  patient_name: string | null;
  doctor_name: string | null;
  prescribed_date: string | null;
  warnings: string[];
  medicines: MedicineResult[];
  pharmacies: MapPharmacy[];
  user_location: UserLocation | null;
  ocr_text: string | null;
  ocr_confidence: number | null;
  processing_ms: number;
  demo_mode: boolean;
}

export interface HealthStatus {
  status: string;
  app_env: string;
  gemini_configured: boolean;
  firebase_configured: boolean;
  using_demo_data: boolean;
  ocr_available: boolean;
  model: string;
}
