from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, IrrigationPrediction, SensorReading
from app.deps import get_current_farm
from app.ml.irrigation.explanation_engine import ExplanationEngine
from app.ml.irrigation.feature_mapper import FeatureMapper
from app.ml.irrigation.irrigation_engine import IrrigationEngine
from app.schemas.irrigation import IrrigationPredictionOut

router = APIRouter(prefix="/api/irrigation", tags=["irrigation"])

engine = IrrigationEngine()


def _farm_data_dict(farm: Farm) -> dict:
    return {
        "region": farm.region,
        "field_area_hectare": farm.field_area_hectare,
        "soil_type": farm.soil_type,
        "soil_ph": farm.soil_ph,
        "organic_carbon": farm.organic_carbon,
        "electrical_conductivity": farm.electrical_conductivity,
        "crop_type": farm.crop_type,
        "crop_growth_stage": farm.crop_growth_stage,
        "season": farm.season,
        "mulching_used": farm.mulching_used,
    }


def run_prediction(db: Session, farm: Farm, reading: SensorReading) -> IrrigationPrediction:
    sensor_data = {
        "soil_moisture": reading.soil_moisture,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "rainfall": reading.rainfall,
        "sunlight": reading.sunlight,
        "wind_speed": reading.wind_speed,
    }
    mapped_features = FeatureMapper.map_to_model_features(sensor_data, _farm_data_dict(farm))
    result = engine.predict(mapped_features)
    agri_support = ExplanationEngine.generate_agricultural_decision_support(
        mapped_features, result["prediction"]
    )

    record = IrrigationPrediction(
        farm_id=farm.id,
        prediction=result["prediction"],
        confidence=result["confidence"],
        probabilities=result["probabilities"],
        mapped_features=mapped_features,
        indicators=agri_support["indicators"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/predict", response_model=IrrigationPredictionOut)
def predict(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id))
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor readings yet for this farm.")

    try:
        record = run_prediction(db, farm, reading)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return IrrigationPredictionOut(
        prediction=record.prediction,
        confidence=record.confidence,
        probabilities=record.probabilities,
        mapped_features=record.mapped_features,
        indicators=record.indicators,
        timestamp=record.timestamp,
    )


@router.get("/latest", response_model=IrrigationPredictionOut)
def latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    record = (
        db.query(IrrigationPrediction)
        .filter(IrrigationPrediction.farm_id == farm.id)
        .order_by(desc(IrrigationPrediction.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No irrigation prediction yet — call /predict first.")
    return IrrigationPredictionOut(
        prediction=record.prediction,
        confidence=record.confidence,
        probabilities=record.probabilities,
        mapped_features=record.mapped_features,
        indicators=record.indicators,
        timestamp=record.timestamp,
    )
