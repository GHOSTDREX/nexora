# Soil Health Module

Standalone deterministic Soil Health subsystem with manual testing, a hardware-ready sensor adapter, FastAPI, and a Streamlit UI.

## Authoritative rules

All thresholds live in `src/config.py` and are evaluated by `src/soil_health_engine.py`.

- Nitrogen: healthy at or above 30; below is Moderate Stress.
- Phosphorus: healthy at or above 25; below is Moderate Stress.
- Potassium: healthy at or above 25; below is Moderate Stress.
- Soil Moisture: healthy at or above 25; below is Moderate Stress.
- Soil pH: healthy inclusively from 6.10 through 7.00. Values 5.50, 6.00, and 7.10 are stress cases from validation.
- Temperature: healthy inclusively from 15.0°C through 35.0°C. This is a general heuristic field-crop comfort range, not a notebook-validated boundary like the five rules above.
- Humidity: healthy inclusively from 30% through 85%. Same heuristic (not notebook-validated) caveat as temperature.
- pH is optional. Missing pH is represented internally as `None`; zero is never used as a missing sentinel by the engine.
- Rain detection is optional and does not affect the result.

The score is the percentage of evaluated parameters that are Healthy. It is a transparent prototype score, not a validated agronomic index. The current rules are prototype dataset-derived decision rules, not universal agronomic recommendations. Field validation is required.

## Run

```powershell
cd "Soil Health"
pip install -r requirements.txt
streamlit run frontend\soil_health_app.py
```

FastAPI:

```powershell
uvicorn api.app:app --reload --port 8002
```

`POST /api/soil-health/analyze` accepts the canonical sensor fields. `GET /health` checks service availability.

## Test

```powershell
python -m unittest discover -s tests -p "test_*.py"
```

The tests cover the regression case, every requested stress case, all boundaries, missing pH, multiple stress accumulation, invalid input, and manual/sensor consistency.
