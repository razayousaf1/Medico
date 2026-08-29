"""
Seed a real Firestore project with the demo dataset.

Usage:
    cd backend
    cp .env.example .env          # configure FIREBASE_CREDENTIALS_PATH (or _B64)
    python seed/seed_firestore.py

Writes the `pharmacies`, `medicines` and `inventory` collections.
Safe to re-run — documents are upserted by deterministic IDs.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import firebase_admin  # noqa: E402
from firebase_admin import credentials, firestore  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.services import demo_data  # noqa: E402


def main() -> None:
    settings = get_settings()

    cred = None
    if settings.firebase_credentials_b64:
        import base64
        import json

        info = json.loads(base64.b64decode(settings.firebase_credentials_b64))
        cred = credentials.Certificate(info)
    elif settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        print("No Firebase credentials configured. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_B64 in backend/.env")
        sys.exit(1)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    batch_size = 400
    now = datetime.now(timezone.utc).isoformat()

    def write_batch(collection: str, docs: list[dict]) -> None:
        for start in range(0, len(docs), batch_size):
            batch = db.batch()
            for doc in docs[start : start + batch_size]:
                doc_id = doc["id"]
                payload = {k: v for k, v in doc.items() if k != "id"}
                batch.set(db.collection(collection).document(doc_id), payload, merge=True)
            batch.commit()
        print(f"  {collection}: {len(docs)} documents written")

    print("Seeding Firestore…")

    pharmacies = [{**p} for p in demo_data.PHARMACIES]
    for pharmacy in pharmacies:
        pharmacy["updated_at"] = now
    write_batch("pharmacies", pharmacies)

    medicines = demo_data.enriched_medicines()
    for medicine in medicines:
        medicine["updated_at"] = now
    write_batch("medicines", medicines)

    inventory = [{**row, "updated_at": now} for row in demo_data.INVENTORY]
    write_batch("inventory", inventory)

    print("Done. Point the API at this project with the same .env and restart uvicorn.")


if __name__ == "__main__":
    main()
