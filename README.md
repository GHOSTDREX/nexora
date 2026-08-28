# AgriNova

AI-powered smart agriculture dashboard. Connects simulated ESP32 field sensors and a camera-equipped robot to real ML models (irrigation need prediction, multi-crop recommendation) and an LLM-backed farmer assistant, behind a multi-user, multilingual web app.

```
nexora/
├── Crop Suitability Analysis/   original prototype (source reference, untouched)
├── Irrigation Recommendation/   original prototype (source reference, untouched)
├── backend/                     FastAPI + SQLAlchemy + SQLite
└── frontend/                    React + Vite + TypeScript + Tailwind CSS
```

## Backend

```bash
cd backend
python -m venv venv
source venv/Scripts/activate        # Windows Git Bash; use venv\Scripts\activate.bat for cmd.exe
pip install -r requirements.txt

# Train the crop-recommendation model once (already committed, but re-run after changing the dataset)
python -m app.ml.crop_recommendation.train

# Optional: copy .env.example to .env and set ANTHROPIC_API_KEY to enable the real LLM assistant
cp .env.example .env

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs: http://127.0.0.1:8000/docs

Without `ANTHROPIC_API_KEY` set, the AI Assistant automatically falls back to a rule-based responder (English/Hindi/Marathi) — the app works fully out of the box either way.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at http://127.0.0.1:5173. It talks to the backend via `VITE_API_URL`/`VITE_WS_URL` in `frontend/.env` (defaults to `http://127.0.0.1:8000` / `ws://127.0.0.1:8000`).

## What's simulated vs. real

- **Real**: the irrigation-need ML model (ported from the uploaded Decision Tree pipeline), the crop-recommendation ML model (RandomForest trained on the uploaded `crop_recommendation.csv`, ~99.5% test accuracy), the crop-condition rule engine, live weather (Open-Meteo), JWT auth, per-user/per-farm data isolation.
- **Simulated** (no physical ESP32/ESP32-CAM connected yet): sensor readings drift live via a per-farm backend loop and are written through the same REST ingestion path real hardware would use; the camera feed is a procedurally generated frame reacting to pan/tilt commands. Both are drop-in replaceable with real hardware later without frontend changes.
- **Not included in this build**: crop disease detection (no model/dataset was provided).

## Multi-user

Each registered user completes a short onboarding flow to create their own farm. Every API route derives the farm from the authenticated JWT — never from a client-supplied ID — so many farmers can use the app concurrently without ever seeing each other's data. The live sensor/automation loop runs independently per farm with its own random seed, so values differ farm-to-farm.

## Languages

English, Hindi, Marathi, Gujarati, Tamil, Telugu, Kannada, Bengali, Punjabi, and Malayalam — switchable from the dropdown in the top bar or Settings. The LLM assistant (when enabled) answers fluently in all ten; the offline rule-based assistant supports English/Hindi/Marathi and defaults to English for the rest.
