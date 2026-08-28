"""
SMART AGRICULTURE AI
FastAPI Microservice (REST API)

Provides production REST endpoints for:
1. ESP32 telemetry ingestion (POST /api/v1/sensors/readings)
2. Live & historical sensor data retrieval (GET /api/v1/sensors/latest & history)
3. Irrigation Recommendation prediction (POST /api/v1/irrigation/predict)
4. Farm configuration management (GET/POST /api/v1/farms)
"""

import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Ensure root workspace directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database.db_manager import DatabaseManager
from src.sensor_validator import SensorValidator
from src.feature_mapper import FeatureMapper
from src.irrigation_engine import IrrigationEngine
from src.explanation_engine import ExplanationEngine
from src.config import API_PORT, API_HOST

# Initialize FastAPI App
app = FastAPI(
    title="Smart Agriculture AI - Irrigation Microservice API",
    description="Production REST API for ESP32 telemetry ingest, validation, and ML inference.",
    version="1.0.0"
)

# Singletons
db = DatabaseManager()
engine = IrrigationEngine()


# --- Pydantic Request Models ---
class SensorTelemetrySchema(BaseModel):
    farm_id: str = Field(default="FARM_001", description="Farm identifier")
    device_id: str = Field(default="ESP32_FIELD_01", description="ESP32 device identifier")
    soil_moisture: float = Field(..., description="Soil moisture % (0-100)")
    temperature: float = Field(..., description="Air temperature °C")
    humidity: float = Field(..., description="Relative humidity % (0-100)")
    rainfall: float = Field(..., description="Cumulative rainfall mm (>=0)")
    sunlight: float = Field(..., description="Solar radiation / Sunlight raw units")
    wind_speed: float = Field(..., description="Wind speed km/h (>=0)")
    timestamp: Optional[str] = Field(default=None, description="ISO timestamp string")


class FarmConfigSchema(BaseModel):
    farm_id: str = Field(default="FARM_001")
    region: str = Field(default="North")
    field_area_hectare: float = Field(default=2.5, alias="field_area")
    soil_type: str = Field(default="Loamy")
    soil_ph: float = Field(default=6.5)
    organic_carbon: float = Field(default=0.85)
    electrical_conductivity: float = Field(default=1.5)
    crop_type: str = Field(default="Wheat")
    crop_growth_stage: str = Field(default="Vegetative")
    season: str = Field(default="Rabi")
    mulching_used: str = Field(default="No")

    class Config:
        populate_by_name = True


class PredictRequestSchema(BaseModel):
    farm_id: str = Field(default="FARM_001")
    mode: str = Field(default="Live", description="Live or Demo mode")
    sensor_data: Dict[str, Any]
    farm_data: Dict[str, Any]


# --- REST API Endpoints ---

@app.get("/")
def root():
    return {
        "status": "online",
        "system": "Smart Agriculture AI Microservice API",
        "model_loaded": engine.model is not None,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/v1/sensors/readings", status_code=status.HTTP_201_CREATED)

def receive_sensor_telemetry(payload: SensorTelemetrySchema):
    """
    ESP32 Live Telemetry Ingestion Endpoint.
    Validates readings, stores in database, and returns confirmation.
    """
    data_dict = payload.model_dump()
    if not data_dict.get("timestamp"):
        data_dict["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Sensor Validation
    is_valid, errors = SensorValidator.validate_reading(data_dict)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP422_UNPROCESSABLE_ENTITY,
            detail={"message": "Corrupted or invalid ESP32 packet", "errors": errors}
        )

    data_dict["status"] = "LIVE"
    db.insert_sensor_reading(data_dict)

    return {
        "status": "success",
        "message": "ESP32 telemetry ingested successfully",
        "farm_id": payload.farm_id,
        "device_id": payload.device_id,
        "timestamp": data_dict["timestamp"]
    }


@app.get("/api/v1/sensors/latest/{farm_id}")
def get_latest_sensor(farm_id: str = "FARM_001"):
    """Retrieves the latest sensor reading and evaluates staleness."""
    reading = db.get_latest_sensor_reading(farm_id)
    if not reading:
        raise HTTPException(status_code=404, detail=f"No sensor readings found for farm {farm_id}")

    is_stale, stale_msg = SensorValidator.check_staleness(reading.get("timestamp"))
    reading["is_stale"] = is_stale
    reading["sensor_health"] = "STALE" if is_stale else "LIVE"
    reading["status_note"] = stale_msg
    return reading


@app.get("/api/v1/sensors/history/{farm_id}")
def get_sensor_history(farm_id: str = "FARM_001", limit: int = 30):
    """Returns historical sensor telemetry time-series records."""
    history = db.get_sensor_history(farm_id, limit=limit)
    return {"farm_id": farm_id, "record_count": len(history), "history": history}


@app.get("/api/v1/farms/{farm_id}")
def get_farm_config(farm_id: str = "FARM_001"):
    """Gets farm configuration data."""
    farm = db.get_farm(farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail=f"Farm {farm_id} not found")
    return farm


@app.post("/api/v1/farms/{farm_id}")
def update_farm_config(farm_id: str, payload: FarmConfigSchema):
    """Updates farm configuration data."""
    farm_dict = payload.model_dump()
    farm_dict["farm_id"] = farm_id
    db.upsert_farm(farm_dict)
    return {"status": "success", "message": f"Farm {farm_id} updated successfully", "farm_data": farm_dict}


@app.post("/api/v1/irrigation/predict")
def predict_irrigation(payload: PredictRequestSchema):
    """
    Main Irrigation Prediction Endpoint.
    Maps live ESP32 readings + farm config into exact 16 model features, runs inference,
    computes confidence, generates separate explanations, and logs to DB.
    """
    sensor_data = payload.sensor_data
    farm_data = payload.farm_data

    # 1. Validate Sensor Telemetry
    is_valid, errors = SensorValidator.validate_reading(sensor_data)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP400_BAD_REQUEST,
            detail={"message": "Sensor Validation Failure", "errors": errors}
        )

    # 2. Check Staleness
    is_stale, stale_msg = SensorValidator.check_staleness(sensor_data.get("timestamp"))

    # 3. Explicit Feature Mapping
    try:
        mapped_features = FeatureMapper.map_to_model_features(sensor_data, farm_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Feature Mapping Failed: {str(e)}")

    # 4. Machine Learning Inference
    try:
        inference_result = engine.predict(mapped_features)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML Inference Error: {str(e)}")

    # 5. Explanations
    agri_support = ExplanationEngine.generate_agricultural_decision_support(mapped_features, inference_result["prediction"])
    model_expl = ExplanationEngine.generate_model_explanation(engine)

    # 6. Record Prediction in Database
    db_pred_record = {
        "farm_id": payload.farm_id,
        "prediction": inference_result["prediction"],
        "confidence": inference_result["confidence"],
        "probabilities": inference_result["probabilities"],
        "mode": payload.mode
    }
    db.insert_prediction(db_pred_record)

    return {
        "status": "success",
        "farm_id": payload.farm_id,
        "mode": payload.mode,
        "is_stale": is_stale,
        "sensor_health": "STALE" if is_stale else "LIVE",
        "prediction": inference_result["prediction"],
        "confidence": inference_result["confidence"],
        "probabilities": inference_result["probabilities"],
        "agricultural_decision_support": agri_support,
        "model_explanation": model_expl,
        "mapped_features": mapped_features
    }


from src.agronomist_agent import AgronomistAgent


# Initialize Agent Singleton
agronomist_agent = AgronomistAgent()


class AgentChatSchema(BaseModel):
    user_query: str = Field(..., description="User's query string")
    farm_id: str = Field(default="FARM_001")
    sensor_data: Dict[str, Any]
    farm_data: Dict[str, Any]
    prediction_info: Optional[Dict[str, Any]] = None


@app.get("/api/v1/agent/prompts")
def get_agent_prompts():
    """Returns quick interactive question prompts for farmers."""
    return {"prompts": AgronomistAgent.get_suggested_prompts()}


@app.post("/api/v1/agent/chat")
def chat_with_agronomist(payload: AgentChatSchema):
    """
    Interactive AI Agronomist Agent Chat Endpoint.
    Analyzes live ESP32 telemetry + farm config + ML prediction context to answer farmer queries.
    """
    try:
        agent_response = agronomist_agent.process_query(
            user_query=payload.user_query,
            sensor_data=payload.sensor_data,
            farm_data=payload.farm_data,
            prediction_info=payload.prediction_info
        )
        return {"status": "success", "agent_response": agent_response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent Error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=API_HOST, port=API_PORT)

