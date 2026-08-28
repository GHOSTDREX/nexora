from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict

from src.soil_health_engine import predict_soil_health

app = FastAPI(title="Smart Agriculture AI - Soil Health", version="1.0.0")


class SoilReading(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nitrogen: float
    phosphorus: float
    potassium: float
    soil_moisture: float
    humidity: float
    temperature: float
    soil_ph: float | None = None
    rain_detected: bool | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "module": "soil_health", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.post("/api/soil-health/analyze")
def analyze(payload: SoilReading) -> dict[str, Any]:
    try:
        return predict_soil_health(**payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
