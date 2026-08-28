from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, SensorReading, SoilHealthRecord
from app.deps import get_current_farm
from app.ml.soil_health.config import DISCLAIMER, RULE_SOURCE, RULE_VERSION
from app.ml.soil_health.soil_health_engine import predict_soil_health
from app.schemas.soil_health import SoilHealthOut

router = APIRouter(prefix="/api/soil-health", tags=["soil-health"])


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


def _out(record: SoilHealthRecord) -> SoilHealthOut:
    return SoilHealthOut(
        overall_status=record.overall_status,
        health_score=record.health_score,
        factors=record.factors,
        stress_factors=record.stress_factors,
        primary_issue=record.primary_issue,
        recommendation=record.recommendation,
        explanation=record.explanation,
        rule_version=RULE_VERSION,
        rule_source=RULE_SOURCE,
        disclaimer=DISCLAIMER,
        timestamp=record.timestamp,
    )


@router.get("/analyze", response_model=SoilHealthOut)
def soil_health_analyze(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    reading = _latest_reading(db, farm)
    try:
        result = predict_soil_health(
            nitrogen=reading.nitrogen,
            phosphorus=reading.phosphorus,
            potassium=reading.potassium,
            soil_moisture=reading.soil_moisture,
            humidity=reading.humidity,
            temperature=reading.temperature,
            soil_ph=farm.soil_ph,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    record = SoilHealthRecord(
        farm_id=farm.id,
        overall_status=result["overall_status"],
        health_score=result["health_score"],
        factors=result["factors"],
        stress_factors=result["stress_factors"],
        primary_issue=result["primary_issue"],
        recommendation=result["recommendation"],
        explanation=result["explanation"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _out(record)


@router.get("/latest", response_model=SoilHealthOut)
def soil_health_latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    record = (
        db.query(SoilHealthRecord)
        .filter(SoilHealthRecord.farm_id == farm.id)
        .order_by(desc(SoilHealthRecord.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No soil health analysis yet — call /analyze first.")
    return _out(record)
