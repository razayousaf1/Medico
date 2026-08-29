# Medico — Prescription Intelligence & Medicine Availability Platform

Upload a prescription photo. Medico reads it with **PaddleOCR**, structures it with **Gemini AI** (correcting OCR errors, decoding abbreviations, extracting generics/strengths), searches **Firebase Firestore** for live pharmacy stock and prices in Pakistan, and renders a premium dashboard with an **OpenStreetMap** pharmacy map.

```
Upload → PaddleOCR → Gemini AI → Structured JSON → Firestore search
      → Alternatives for unavailable medicines → Dashboard + Map
```

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), TypeScript, Tailwind CSS v4, shadcn-style UI, Framer Motion, React Leaflet |
| Backend | FastAPI (Python 3.11+), Uvicorn |
| OCR | PaddleOCR (English) |
| AI | Google Gemini API |
| Database | Firebase Firestore |
| Maps | OpenStreetMap + React Leaflet |

## Repository layout

```
medico/
├── backend/
│   ├── app/
│   │   ├── api/routes/prescriptions.py   # /api/analyze-prescription, /api/health
│   │   ├── core/config.py                # env-driven settings
│   │   ├── models/schemas.py             # Pydantic response models
│   │   ├── services/
│   │   │   ├── ocr_service.py            # PaddleOCR wrapper (img + PDF)
│   │   │   ├── llm_service.py            # Gemini API client + prompts
│   │   │   ├── firestore_service.py      # Firestore / demo dataset store
│   │   │   ├── availability_service.py   # pipeline orchestration
│   │   │   └── demo_data.py              # built-in Lahore dataset
│   │   ├── utils/geo.py                  # haversine, strength matching
│   │   └── main.py                       # FastAPI app
│   ├── scripts/mock_llm.py               # local mock of the Gemini API
│   ├── seed/seed_firestore.py            # push demo data → Firestore
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── app/                          # landing page + /dashboard
    │   ├── components/
    │   │   ├── ui/                       # button, card, badge, progress…
    │   │   ├── site/                      # navbar, footer
    │   │   ├── upload/upload-zone.tsx     # drag & drop + progress stepper
    │   │   └── dashboard/                 # summary, stats, medicine card, map
    │   └── lib/                          # api client, types, session store, utils
    ├── package.json
    └── .env.example
```

## Quick start (zero external keys)

The backend ships with a built-in demo dataset (8 Lahore pharmacies, 40 medicines, generated inventory), so the whole platform runs locally with no Firebase or Gemini key — availability lookup works end-to-end and the API response flags `demo_mode: true`.

**Only for full OCR → AI analysis you need a Gemini key** (or the included mock).

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # first install: ~1-2 min

cp .env.example .env               # optional for demo mode

uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local         # defaults to http://localhost:8000
npm run dev
```

Open http://localhost:3000

## API keys & configuration

All secrets live in **`backend/.env`** (never committed — see `.gitignore`). Copy `backend/.env.example` and fill in:

### Google Gemini — required for real AI analysis

1. Create a free key at **https://aistudio.google.com/apikey**.
2. Set in `backend/.env`:
   ```
   GEMINI_API_KEY=AIza...
   GEMINI_MODEL=gemini-2.5-flash    # also: gemini-2.5-pro, gemini-2.0-flash
   ```
3. Restart uvicorn. `/api/health` will report `gemini_configured: true`.

Without a key, `/api/analyze-prescription` returns a clear 502 error explaining how to configure it.

### Firebase Firestore — required for live pharmacy data

1. Firebase console → **Project settings → Service accounts → Generate new private key** → download JSON.
2. Configure **one** of (in `backend/.env`):
   ```
   FIREBASE_CREDENTIALS_PATH=/absolute/path/to/firebase-service-account.json
   # or, for deployment (single env var):
   FIREBASE_CREDENTIALS_B64=$(base64 -i firebase-service-account.json | tr -d '\n')
   # or, on Google Cloud with Application Default Credentials:
   FIRESTORE_PROJECT_ID=your-project-id
   ```
3. Seed the database:
   ```bash
   cd backend
   source .venv/bin/activate
   python seed/seed_firestore.py
   ```
4. Restart uvicorn — `/api/health` reports `using_demo_data: false`.

**Firestore collections:**

- `pharmacies` — `{ name, branch, address, city, phone, rating, open_hours, lat, lng }`
- `medicines` — `{ brand, generic, strength, form, manufacturer, category, brand_lower, generic_keywords[] }` (the lowercase/keyword fields power the search queries)
- `inventory` — `{ pharmacy_id, medicine_id, price, stock, updated_at }`

If Firebase is missing or misconfigured the API automatically falls back to the demo dataset and logs a warning — it never crashes.

### Frontend

`frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Testing without a Gemini key (mock)

`backend/scripts/mock_llm.py` fakes the Gemini API using the demo dataset, letting you exercise the full OCR → AI → availability pipeline locally:

```bash
# terminal 1
cd backend && source .venv/bin/activate
python scripts/mock_llm.py            # http://localhost:8001

# terminal 2
cd backend
GEMINI_API_KEY=mock GEMINI_BASE_URL=http://localhost:8001/v1 uvicorn app.main:app --reload
```

The mock recognises common medicines in the OCR text (Augmentin, Panadol, Brufen, Risek, Zyrtec, Glucophage) and returns structured JSON in the same shape as the real API.

## API reference

### `POST /api/analyze-prescription`

Multipart form: `file` (JPG/PNG/WEBP/PDF, ≤ 10 MB) · optional query `lat`, `lng`.

Response (trimmed):
```json
{
  "id": "a1b2c3d4e5f6",
  "summary": "This prescription contains 2 medicines…",
  "overall_confidence": 0.91,
  "warnings": [],
  "medicines": [
    {
      "name": "Augmentin",
      "generic_name": "Amoxicillin + Clavulanic Acid",
      "strength": "625 mg",
      "frequency": {
        "raw": "1-0-1",
        "interpretation": "One tablet in the morning and at night",
        "times_per_day": 2,
        "abbreviation_meanings": [{"abbreviation": "1-0-1", "meaning": "…"}]
      },
      "confidence": 0.93,
      "availability": "in_stock",
      "best_match": {
        "brand": "Augmentin", "strength": "625 mg", "price": 480, "stock": 24,
        "in_stock": true, "strength_match": true,
        "pharmacy": {"name": "Servaid Pharmacy", "distance_km": 1.4, "lat": 31.47, "lng": 74.41}
      },
      "matches": ["…more pharmacies…"],
      "alternatives": [{"brand": "Clavam 625", "found": true, "best_match": {"…": "…"}}]
    }
  ],
  "pharmacies": ["…map payload: pharmacy + stocked medicines…"],
  "ocr_text": "Dr. …\nRx\nAugmentin 625mg 1-0-1 x5d…",
  "ocr_confidence": 0.96,
  "processing_ms": 8420,
  "demo_mode": true
}
```

Errors are structured: `400` unsupported type / `413` too large / `422` unreadable image (OCR) / `502` Gemini misconfigured or unreachable — each with a human-readable `detail`.

### `GET /api/health`

Reports `gemini_configured`, `firebase_configured`, `using_demo_data`, `ocr_available`, and the active model.

## How the Gemini prompts work

`app/services/llm_service.py` sends OCR text to Gemini with a pharmacist-expert system prompt that instructs it to: correct OCR noise (`rn/m`, `0/O`, merged words), extract brand + generic + strength + form + duration, interpret South Asian dosage abbreviations (SOS, OD, BD, TDS, QID, HS, PRN, AC/PC, STAT, `1-0-1` patterns), suggest Pakistani alternative brands, and return **JSON only**. Parsing is defensive (fences stripped, outermost-object extraction, one automatic retry) and `response_format: json_object` is used when supported.

For medicines with no stock match, a second call asks Gemini for alternative brands, which are then checked against Firestore so only *actually available* alternatives are surfaced.

## Deployment

### Backend (Docker / any Python host)

`backend/Dockerfile` is included. With secrets via env vars (`FIREBASE_CREDENTIALS_B64` is the most portable):

```bash
docker build -t medico-api ./backend
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=AIza... \
  -e FIREBASE_CREDENTIALS_B64=... \
  -e CORS_ORIGINS=https://your-frontend.example.com \
  medico-api
```

On **Cloud Run**: deploy the same image, set the same env vars, and you can rely on Application Default Credentials (`FIRESTORE_PROJECT_ID`) instead of a service-account key. First request after cold start takes longer while PaddleOCR loads its model into memory.

### Frontend (Vercel / Netlify)

```bash
# Vercel
cd frontend
vercel --prod
# Set environment variable: NEXT_PUBLIC_API_URL=https://your-api.example.com
```

Update `CORS_ORIGINS` on the backend to include the deployed frontend origin.

## Development notes

- **PaddleOCR models** (~100 MB) auto-download to `~/.paddleocr` on first OCR request.
- **PDF support** rasterises pages via PyMuPDF at 2× zoom before OCR.
- The OCR engine is **lazy-initialised and cached** per process; heavy calls run in a thread pool so the event loop stays responsive.
- Frontend keeps the analysis in `sessionStorage` (`src/lib/store.ts`) — the dashboard survives navigation and refreshes without a backend session.
- Geolocation is **optional**: with it, pharmacies sort by real distance; without it, the app falls back to Lahore city centre and distances show `—`.

## License

MIT — use it, extend it, ship it.
