"""
Development utility: a tiny OpenAI-compatible mock of the Gemini API.

Lets you exercise the FULL pipeline (OCR -> "Gemini" -> Firestore -> dashboard)
locally without a Gemini key or spending credits.

Usage:
    cd backend
    python scripts/mock_llm.py                 # serves on http://localhost:8001

    # then run the API against it:
    GEMINI_API_KEY=mock GEMINI_BASE_URL=http://localhost:8001/v1 uvicorn app.main:app --reload

NOT for production use.
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi import FastAPI, Request  # noqa: E402

from app.services import demo_data  # noqa: E402

app = FastAPI(title="Mock Gemini API (dev only)")

# Keyword table used to fake a "smart" extraction from OCR text.
_MEDICINE_HINTS: list[dict] = [
    {"keywords": ["augmentin", "clavulanic", "co-amoxiclav"],
     "payload": {"name": "Augmentin", "generic_name": "Amoxicillin + Clavulanic Acid", "strength": "625 mg",
                 "form": "tablet", "frequency_raw": "1-0-1", "frequency_interpretation": "One tablet in the morning and one at night",
                 "times_per_day": 2, "duration": "5 days", "confidence": 0.93,
                 "alternative_brands": ["Clavam 625", "Amoclav 625", "Amoclav-Drop"]}},
    {"keywords": ["panadol", "paracetamol", "calpol"],
     "payload": {"name": "Panadol", "generic_name": "Paracetamol", "strength": "500 mg",
                 "form": "tablet", "frequency_raw": "SOS", "frequency_interpretation": "Only when needed (as required)",
                 "times_per_day": None, "duration": None, "confidence": 0.95,
                 "alternative_brands": ["Calpol", "Disprin", "Neodipar"]}},
    {"keywords": ["brufen", "ibuprofen"],
     "payload": {"name": "Brufen", "generic_name": "Ibuprofen", "strength": "400 mg",
                 "form": "tablet", "frequency_raw": "TDS", "frequency_interpretation": "Three times a day after meals",
                 "times_per_day": 3, "duration": "3 days", "confidence": 0.9,
                 "alternative_brands": ["Ibuprofen-GP", "Rufen"]}},
    {"keywords": ["risek", "omeprazole"],
     "payload": {"name": "Risek", "generic_name": "Omeprazole", "strength": "20 mg",
                 "form": "capsule", "frequency_raw": "OD", "frequency_interpretation": "Once daily before breakfast",
                 "times_per_day": 1, "duration": "14 days", "confidence": 0.91,
                 "alternative_brands": ["Omez 20", "Ruling 20"]}},
    {"keywords": ["zyrtec", "cetirizine"],
     "payload": {"name": "Zyrtec", "generic_name": "Cetirizine", "strength": "10 mg",
                 "form": "tablet", "frequency_raw": "HS", "frequency_interpretation": "One tablet at bedtime",
                 "times_per_day": 1, "duration": "7 days", "confidence": 0.94,
                 "alternative_brands": ["Zirtin 10", "Cetrin 10"]}},
    {"keywords": ["glucophage", "metformin"],
     "payload": {"name": "Glucophage", "generic_name": "Metformin", "strength": "500 mg",
                 "form": "tablet", "frequency_raw": "1-0-1", "frequency_interpretation": "One tablet in the morning and one at night",
                 "times_per_day": 2, "duration": "30 days", "confidence": 0.92,
                 "alternative_brands": ["Neodipar-M", "Metfor"]}},
]

# Default prescription used when nothing in the OCR text matches a hint.
_DEFAULT_MEDICINES = [_MEDICINE_HINTS[0]["payload"]]

_ALT_BRANDS = {
    md["brand"]: [b for b in {m["brand"] for m in demo_data.MEDICINES
                              if m["generic"] == md["generic"] and m["brand"] != md["brand"]}]
    for md in demo_data.MEDICINES
}


def _extraction_reply(ocr_text: str) -> dict:
    lowered = ocr_text.lower()
    medicines = []
    for hint in _MEDICINE_HINTS:
        if any(k in lowered for k in hint["keywords"]):
            medicines.append(hint["payload"])
    if not medicines:
        medicines = _DEFAULT_MEDICINES

    return {
        "patient_name": None,
        "doctor_name": None,
        "prescribed_date": None,
        "summary": (
            "This prescription contains "
            f"{len(medicines)} medicine(s): {', '.join(m['name'] for m in medicines)}. "
            "Take each medicine as directed on the label, complete the full course "
            "and consult your pharmacist if any dosage is unclear."
        ),
        "overall_confidence": 0.9,
        "warnings": ["Mock LLM response — configure a real GEMINI_API_KEY for production-quality analysis."],
        "medicines": [
            {**m, "abbreviation_meanings": [
                {"abbreviation": m.get("frequency_raw") or "", "meaning": m.get("frequency_interpretation") or ""}
            ], "instructions": "After meals"}
            for m in medicines
        ],
    }


def _alternatives_reply(user_text: str) -> dict:
    alternatives = []
    for match in re.finditer(r"index (\d+): ([^\n—]+)", user_text):
        index = int(match.group(1))
        raw_name = match.group(2).strip()
        # Match against known brands, else generic keywords
        brand_key = None
        lowered = raw_name.lower()
        for brand in _ALT_BRANDS:
            if brand.lower() in lowered:
                brand_key = brand
                break
        if brand_key is None:
            for med in demo_data.MEDICINES:
                if med["generic"].split()[0].lower() in lowered:
                    brand_key = med["brand"]
                    break
        brands = _ALT_BRANDS.get(brand_key, ["Clavam 625", "Amoxil 500", "Keflin 500"])[:4]
        alternatives.append({"index": index, "brands": brands})
    return {"alternatives": alternatives}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> dict:
    body = await request.json()
    messages = body.get("messages", [])
    user_text = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")

    if "NOT found in our pharmacy database" in user_text:
        payload = _alternatives_reply(user_text)
    else:
        payload = _extraction_reply(user_text)

    content = json.dumps(payload, ensure_ascii=False)
    return {
        "id": "mock-chatcmpl",
        "object": "chat.completion",
        "model": body.get("model", "mock-gemini"),
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}, "finish_reason": "stop"}],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
