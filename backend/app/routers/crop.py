from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import CropRecommendation, Farm, SensorReading
from app.deps import get_current_farm
from app.ml.crop_condition.crop_condition_engine import assess_crop_condition
from app.ml.crop_recommendation.predictor import CropRecommender
from app.schemas.crop import CropConditionRequest, CropRecommendationOut

router = APIRouter(prefix="/api/crop", tags=["crop"])

recommender = CropRecommender()


def _latest_reading(db: Session, farm: Farm) -> SensorReading:
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id))
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor readings yet for this farm.")
    return reading


@router.post("/condition")
def crop_condition(
    payload: CropConditionRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    reading = _latest_reading(db, farm)
    sensor_data = {
        "soil_moisture": reading.soil_moisture,
        "temperature": reading.temperature,
        "humidity": reading.humidity,
        "rainfall": reading.rainfall,
        "ph": farm.soil_ph,
        "nitrogen": reading.nitrogen,
        "phosphorus": reading.phosphorus,
        "potassium": reading.potassium,
    }
    try:
        result = assess_crop_condition(crop=payload.crop, sensor_data=sensor_data)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return result


@router.get("/recommend", response_model=CropRecommendationOut)
def crop_recommend(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    reading = _latest_reading(db, farm)

    result = recommender.recommend(
        n=reading.nitrogen,
        p=reading.phosphorus,
        k=reading.potassium,
        temperature=reading.temperature,
        humidity=reading.humidity,
        ph=farm.soil_ph,
        rainfall=reading.rainfall if reading.rainfall > 5 else 150.0,
    )

    record = CropRecommendation(
        farm_id=farm.id,
        top_crop=result["top_crop"],
        confidence=result["confidence"],
        alternatives=result["alternatives"],
        input_features=result["input_features"],
    )
    db.add(record)
    db.commit()

    return CropRecommendationOut(**result)


@router.get("/recommend/latest", response_model=CropRecommendationOut)
def crop_recommend_latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    record = (
        db.query(CropRecommendation)
        .filter(CropRecommendation.farm_id == farm.id)
        .order_by(desc(CropRecommendation.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No crop recommendation yet — call /recommend first.")
    return CropRecommendationOut(
        top_crop=record.top_crop,
        confidence=record.confidence,
        alternatives=record.alternatives,
        input_features=record.input_features,
    )
