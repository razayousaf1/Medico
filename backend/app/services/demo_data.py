"""
Built-in demo dataset: pharmacies / medicines / inventory in Lahore, Pakistan.

Used in two places:
  1. `FirestoreStore` fallback — when Firebase is not configured the API
     serves availability from this dataset so local development works
     out of the box.
  2. `scripts/../seed/seed_firestore.py` — pushes the same dataset into
     a real Firestore project.

Doc shapes mirror the Firestore collections exactly so the demo store and
the production store are interchangeable.
"""

import random
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# pharmacies collection
# ---------------------------------------------------------------------------

PHARMACIES: list[dict] = [
    {
        "id": "ph_servaid_dha",
        "name": "Servaid Pharmacy",
        "branch": "DHA Phase 5",
        "address": "Main Boulevard, DHA Phase 5",
        "city": "Lahore",
        "phone": "042-37195000",
        "rating": 4.7,
        "open_hours": "24/7",
        "lat": 31.4697,
        "lng": 74.4103,
    },
    {
        "id": "ph_dwatson_gulberg",
        "name": "D. Watson",
        "branch": "MM Alam Road, Gulberg III",
        "address": "18-C MM Alam Road, Gulberg III",
        "city": "Lahore",
        "phone": "042-35776001",
        "rating": 4.5,
        "open_hours": "09:00 - 24:00",
        "lat": 31.5185,
        "lng": 74.3411,
    },
    {
        "id": "ph_alfatah_jt",
        "name": "Al-Fatah Pharmacy",
        "branch": "Johar Town",
        "address": "Pia Main Boulevard, Johar Town",
        "city": "Lahore",
        "phone": "042-35220001",
        "rating": 4.4,
        "open_hours": "09:00 - 23:00",
        "lat": 31.4697,
        "lng": 74.2728,
    },
    {
        "id": "ph_fazaldin_mall",
        "name": "Fazal Din & Sons",
        "branch": "The Mall",
        "address": "Shahrah-e-Quaid-e-Azam, The Mall",
        "city": "Lahore",
        "phone": "042-37235121",
        "rating": 4.3,
        "open_hours": "08:30 - 22:00",
        "lat": 31.5615,
        "lng": 74.3257,
    },
    {
        "id": "ph_shaheen_mt",
        "name": "Shaheen Chemist",
        "branch": "Model Town",
        "address": "Ali Block, Model Town Link Road",
        "city": "Lahore",
        "phone": "042-35910092",
        "rating": 4.2,
        "open_hours": "09:00 - 23:30",
        "lat": 31.4805,
        "lng": 74.3239,
    },
    {
        "id": "ph_sehat_garden",
        "name": "Sehat Pharmacy",
        "branch": "Garden Town",
        "address": "Block C, Garden Town, Ferozepur Road",
        "city": "Lahore",
        "phone": "042-35914045",
        "rating": 4.1,
        "open_hours": "10:00 - 23:00",
        "lat": 31.5040,
        "lng": 74.3300,
    },
    {
        "id": "ph_iqbal_town",
        "name": "Pharmacy Plus",
        "branch": "Iqbal Town",
        "address": "Moon Market, Allama Iqbal Town",
        "city": "Lahore",
        "phone": "042-37800311",
        "rating": 4.0,
        "open_hours": "09:30 - 23:00",
        "lat": 31.5100,
        "lng": 74.2860,
    },
    {
        "id": "ph_wapda_town",
        "name": "Rehman Pharma",
        "branch": "Wapda Town",
        "address": "Neelum Block, Wapda Town",
        "city": "Lahore",
        "phone": "042-35320222",
        "rating": 3.9,
        "open_hours": "10:00 - 22:30",
        "lat": 31.4450,
        "lng": 74.2780,
    },
]

# ---------------------------------------------------------------------------
# medicines collection  (base_price = reference PKR price used to seed inventory)
# ---------------------------------------------------------------------------

MEDICINES: list[dict] = [
    # --- Pain / fever ---
    {"id": "md_panadol_500", "brand": "Panadol", "generic": "Paracetamol", "strength": "500 mg", "form": "tablet", "manufacturer": "GSK", "category": "analgesic", "base_price": 35},
    {"id": "md_panadol_extra", "brand": "Panadol Extra", "generic": "Paracetamol + Caffeine", "strength": "500/65 mg", "form": "tablet", "manufacturer": "GSK", "category": "analgesic", "base_price": 60},
    {"id": "md_brufen_400", "brand": "Brufen", "generic": "Ibuprofen", "strength": "400 mg", "form": "tablet", "manufacturer": "Abbott", "category": "nsaid", "base_price": 180},
    {"id": "md_brufen_600", "brand": "Brufen", "generic": "Ibuprofen", "strength": "600 mg", "form": "tablet", "manufacturer": "Abbott", "category": "nsaid", "base_price": 250},
    {"id": "md_voltaren_50", "brand": "Voltaren", "generic": "Diclofenac Sodium", "strength": "50 mg", "form": "tablet", "manufacturer": "Novartis", "category": "nsaid", "base_price": 210},
    {"id": "md_synflex_275", "brand": "Synflex", "generic": "Naproxen Sodium", "strength": "275 mg", "form": "tablet", "manufacturer": "Ibn Sina", "category": "nsaid", "base_price": 190},
    {"id": "md_disprin", "brand": "Disprin", "generic": "Aspirin", "strength": "300 mg", "form": "tablet", "manufacturer": "Reckitt", "category": "analgesic", "base_price": 25},
    # --- Antibiotics ---
    {"id": "md_augmentin_625", "brand": "Augmentin", "generic": "Amoxicillin + Clavulanic Acid", "strength": "625 mg", "form": "tablet", "manufacturer": "GSK", "category": "antibiotic", "base_price": 480},
    {"id": "md_augmentin_1g", "brand": "Augmentin", "generic": "Amoxicillin + Clavulanic Acid", "strength": "1 g", "form": "tablet", "manufacturer": "GSK", "category": "antibiotic", "base_price": 720},
    {"id": "md_amoxil_500", "brand": "Amoxil", "generic": "Amoxicillin Trihydrate", "strength": "500 mg", "form": "capsule", "manufacturer": "GSK", "category": "antibiotic", "base_price": 220},
    {"id": "md_clavam_625", "brand": "Clavam", "generic": "Amoxicillin + Clavulanic Acid", "strength": "625 mg", "form": "tablet", "manufacturer": "Alkem", "category": "antibiotic", "base_price": 445},
    {"id": "md_ciproxin_500", "brand": "Ciproxin", "generic": "Ciprofloxacin", "strength": "500 mg", "form": "tablet", "manufacturer": "Bayer", "category": "antibiotic", "base_price": 450},
    {"id": "md_zithromax_500", "brand": "Zithromax", "generic": "Azithromycin", "strength": "500 mg", "form": "tablet", "manufacturer": "Pfizer", "category": "antibiotic", "base_price": 620},
    {"id": "md_flagyl_400", "brand": "Flagyl", "generic": "Metronidazole", "strength": "400 mg", "form": "tablet", "manufacturer": "Sanofi", "category": "antibiotic", "base_price": 140},
    {"id": "md_keflin_500", "brand": "Keflin", "generic": "Cephalexin", "strength": "500 mg", "form": "capsule", "manufacturer": "Getz Pharma", "category": "antibiotic", "base_price": 385},
    # --- GI ---
    {"id": "md_risek_20", "brand": "Risek", "generic": "Omeprazole", "strength": "20 mg", "form": "capsule", "manufacturer": "Getz Pharma", "category": "ppi", "base_price": 320},
    {"id": "md_nexum_40", "brand": "Nexum", "generic": "Esomeprazole", "strength": "40 mg", "form": "capsule", "manufacturer": "Getz Pharma", "category": "ppi", "base_price": 420},
    {"id": "md_motilium_10", "brand": "Motilium", "generic": "Domperidone", "strength": "10 mg", "form": "tablet", "manufacturer": "Highnoon", "category": "antiemetic", "base_price": 180},
    {"id": "md_buscopan", "brand": "Buscopan", "generic": "Hyoscine Butylbromide", "strength": "10 mg", "form": "tablet", "manufacturer": "Boehringer", "category": "antispasmodic", "base_price": 240},
    # --- Respiratory / allergy ---
    {"id": "md_ventolin_inhaler", "brand": "Ventolin", "generic": "Salbutamol", "strength": "100 mcg/dose", "form": "inhaler", "manufacturer": "GSK", "category": "bronchodilator", "base_price": 750},
    {"id": "md_zyrtec_10", "brand": "Zyrtec", "generic": "Cetirizine", "strength": "10 mg", "form": "tablet", "manufacturer": "UCB", "category": "antihistamine", "base_price": 230},
    {"id": "md_claritin_10", "brand": "Claritin", "generic": "Loratadine", "strength": "10 mg", "form": "tablet", "manufacturer": "Bayer", "category": "antihistamine", "base_price": 260},
    {"id": "md_singulair_10", "brand": "Singulair", "generic": "Montelukast", "strength": "10 mg", "form": "tablet", "manufacturer": "Organon", "category": "antiasthmatic", "base_price": 560},
    # --- Diabetes / cardiac ---
    {"id": "md_glucophage_500", "brand": "Glucophage", "generic": "Metformin", "strength": "500 mg", "form": "tablet", "manufacturer": "Merck", "category": "antidiabetic", "base_price": 190},
    {"id": "md_glucophage_850", "brand": "Glucophage", "generic": "Metformin", "strength": "850 mg", "form": "tablet", "manufacturer": "Merck", "category": "antidiabetic", "base_price": 260},
    {"id": "md_diamicron_80", "brand": "Diamicron", "generic": "Gliclazide", "strength": "80 mg", "form": "tablet", "manufacturer": "Servier", "category": "antidiabetic", "base_price": 340},
    {"id": "md_lipitor_10", "brand": "Lipitor", "generic": "Atorvastatin", "strength": "10 mg", "form": "tablet", "manufacturer": "Pfizer", "category": "statin", "base_price": 480},
    {"id": "md_atorva_10", "brand": "Atorva", "generic": "Atorvastatin", "strength": "10 mg", "form": "tablet", "manufacturer": "Getz Pharma", "category": "statin", "base_price": 290},
    {"id": "md_concor_5", "brand": "Concor", "generic": "Bisoprolol", "strength": "5 mg", "form": "tablet", "manufacturer": "Merck", "category": "beta_blocker", "base_price": 340},
    {"id": "md_tenormin_50", "brand": "Tenormin", "generic": "Atenolol", "strength": "50 mg", "form": "tablet", "manufacturer": "AstraZeneca", "category": "beta_blocker", "base_price": 220},
    {"id": "md_norvasc_5", "brand": "Norvasc", "generic": "Amlodipine", "strength": "5 mg", "form": "tablet", "manufacturer": "Pfizer", "category": "ccb", "base_price": 310},
    {"id": "md_loprin_75", "brand": "Loprin", "generic": "Aspirin", "strength": "75 mg", "form": "tablet", "manufacturer": "Barrett Hodgson", "category": "antiplatelet", "base_price": 80},
    {"id": "md_lasix_40", "brand": "Lasix", "generic": "Furosemide", "strength": "40 mg", "form": "tablet", "manufacturer": "Sanofi", "category": "diuretic", "base_price": 110},
    # --- CNS ---
    {"id": "md_tegral_200", "brand": "Tegral", "generic": "Carbamazepine", "strength": "200 mg", "form": "tablet", "manufacturer": "Novartis", "category": "antiepileptic", "base_price": 350},
    {"id": "md_xanax_05", "brand": "Xanax", "generic": "Alprazolam", "strength": "0.5 mg", "form": "tablet", "manufacturer": "Pfizer", "category": "anxiolytic", "base_price": 190},
    {"id": "md_lexotanil_3", "brand": "Lexotanil", "generic": "Bromazepam", "strength": "3 mg", "form": "tablet", "manufacturer": "Roche", "category": "anxiolytic", "base_price": 210},
    # --- Paediatric / syrups ---
    {"id": "md_calpol_syrup", "brand": "Calpol", "generic": "Paracetamol", "strength": "120 mg/5 ml", "form": "syrup", "manufacturer": "GSK", "category": "analgesic", "base_price": 150},
    {"id": "md_flagyl_syrup", "brand": "Flagyl", "generic": "Metronidazole Benzoate", "strength": "200 mg/5 ml", "form": "syrup", "manufacturer": "Sanofi", "category": "antibiotic", "base_price": 130},
    {"id": "md_arinac_tab", "brand": "Arinac", "generic": "Paracetamol + Pseudoephedrine", "strength": "500/60 mg", "form": "tablet", "manufacturer": "Abbott", "category": "cold_flu", "base_price": 95},
]

# ---------------------------------------------------------------------------
# inventory collection — generated deterministically from the two tables above
# ---------------------------------------------------------------------------

_UPDATED_AT = "2026-08-28T18:30:00+00:00"


def build_inventory() -> list[dict]:
    """Deterministically distribute medicines across pharmacies.

    Wide-availability staples (analgesics, PPIs, antihistamines) land in most
    pharmacies; specialty items land in fewer — which naturally exercises the
    "unavailable -> suggest alternatives" flow in demos.
    """
    rng = random.Random(42)
    wide_categories = {"analgesic", "ppi", "antihistamine", "antiplatelet", "nsaid"}
    inventory: list[dict] = []
    counter = 0

    for med in MEDICINES:
        pharmacy_ids = [p["id"] for p in PHARMACIES]
        if med["category"] in wide_categories:
            # stocked by most pharmacies
            k = rng.randint(6, len(pharmacy_ids))
        elif med["category"] in {"antibiotic", "antidiabetic", "statin", "beta_blocker"}:
            k = rng.randint(4, 7)
        else:
            # specialty / controlled — sparse availability
            k = rng.randint(1, 4)
        chosen = rng.sample(pharmacy_ids, k=k)

        for pharmacy_id in chosen:
            price = round(med["base_price"] * rng.uniform(0.9, 1.18) / 5) * 5
            # ~20% of stocked rows are sold out right now
            stock = 0 if rng.random() < 0.2 else rng.randint(3, 60)
            counter += 1
            inventory.append(
                {
                    "id": f"inv_{counter:04d}",
                    "pharmacy_id": pharmacy_id,
                    "medicine_id": med["id"],
                    "price": float(price),
                    "stock": stock,
                    "updated_at": _UPDATED_AT,
                }
            )
    return inventory


INVENTORY: list[dict] = build_inventory()

# Enriched medicine docs with the lowercase / keyword fields the Firestore
# queries rely on. The seed script writes these extra fields too.


def _keywords(generic: str) -> list[str]:
    stop = {"acid", "sodium", "potassium", "hydrochloride", "trihydrate", "benzoate", "butylbromide"}
    tokens = [t.strip().lower() for t in generic.replace("/", " + ").replace("+", " ").split()]
    return [t for t in tokens if t and t not in stop]


def enriched_medicines() -> list[dict]:
    out = []
    for med in MEDICINES:
        doc = {
            **{k: v for k, v in med.items() if k != "base_price"},
            "brand_lower": med["brand"].lower(),
            "generic_lower": med["generic"].lower(),
            "generic_keywords": _keywords(med["generic"]),
        }
        out.append(doc)
    return out
