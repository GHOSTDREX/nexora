from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, FertilizerRecommendation, SensorReading
from app.deps import get_current_farm
from app.ml.fertilizer.engine import recommend_fertilizer
from app.schemas.fertilizer import FertilizerRecommendationOut, FertilizerRequest

router = APIRouter(prefix="/api/fertilizer", tags=["fertilizer"])


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


@router.post("/recommend", response_model=FertilizerRecommendationOut)
def fertilizer_recommend(
    payload: FertilizerRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    reading = _latest_reading(db, farm)
    try:
        result = recommend_fertilizer(
            crop_type=payload.crop,
            soil_type=farm.soil_type,
            crop_growth_stage=farm.crop_growth_stage,
            soil_ph=farm.soil_ph,
            nitrogen_level=reading.nitrogen,
            phosphorus_level=reading.phosphorus,
            potassium_level=reading.potassium,
            electrical_conductivity=farm.electrical_conductivity,
        )
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    record = FertilizerRecommendation(
        farm_id=farm.id,
        crop=result["crop"],
        recommended_fertilizer=result["recommended_fertilizer"],
        model_probability=result["model_probability"],
        nutrient_status=result["nutrient_status"],
        reason=result["reason"],
        input_features=result["input_features"],
        warnings=result["warnings"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return FertilizerRecommendationOut(
        crop=record.crop,
        recommended_fertilizer=record.recommended_fertilizer,
        model_probability=record.model_probability,
        nutrient_status=record.nutrient_status,
        reason=record.reason,
        input_features=record.input_features,
        warnings=record.warnings,
        timestamp=record.timestamp,
    )


@router.get("/latest", response_model=FertilizerRecommendationOut)
def fertilizer_latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    record = (
        db.query(FertilizerRecommendation)
        .filter(FertilizerRecommendation.farm_id == farm.id)
        .order_by(desc(FertilizerRecommendation.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No fertilizer recommendation yet — call /recommend first.")
    return FertilizerRecommendationOut(
        crop=record.crop,
        recommended_fertilizer=record.recommended_fertilizer,
        model_probability=record.model_probability,
        nutrient_status=record.nutrient_status,
        reason=record.reason,
        input_features=record.input_features,
        warnings=record.warnings,
        timestamp=record.timestamp,
    )
