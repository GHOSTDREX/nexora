from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, YieldPrediction
from app.deps import get_current_farm
from app.ml.yield_prediction.engine import predict_yield
from app.ml.yield_prediction.validator import SUPPORTED_CROPS, SUPPORTED_SEASONS, SUPPORTED_STATES
from app.schemas.yield_prediction import YieldPredictionOut, YieldPredictionRequest

router = APIRouter(prefix="/api/yield", tags=["yield"])


def _out(record: YieldPrediction) -> YieldPredictionOut:
    return YieldPredictionOut(
        crop=record.crop,
        state=record.state,
        season=record.season,
        year=record.year,
        area_hectare=record.area_hectare,
        predicted_yield=record.predicted_yield,
        estimated_total_production=record.estimated_total_production,
        fertilizer_per_ha=record.fertilizer_per_ha,
        pesticide_per_ha=record.pesticide_per_ha,
        warnings=record.warnings,
        timestamp=record.timestamp,
    )


@router.get("/options")
def yield_options():
    return {"crops": SUPPORTED_CROPS, "states": SUPPORTED_STATES, "seasons": SUPPORTED_SEASONS}


@router.post("/predict", response_model=YieldPredictionOut)
def yield_predict(
    payload: YieldPredictionRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    try:
        result = predict_yield(
            crop=payload.crop,
            state=payload.state,
            season=payload.season,
            year=payload.year,
            area_hectare=payload.area_hectare,
            fertilizer_kg=payload.fertilizer_kg,
            pesticide_kg=payload.pesticide_kg,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    record = YieldPrediction(
        farm_id=farm.id,
        crop=result["crop"],
        state=result["state"],
        season=result["season"],
        year=result["year"],
        area_hectare=result["area_hectare"],
        predicted_yield=result["predicted_yield"],
        estimated_total_production=result["estimated_total_production"],
        fertilizer_per_ha=result["fertilizer_per_ha"],
        pesticide_per_ha=result["pesticide_per_ha"],
        warnings=result["warnings"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return _out(record)


@router.get("/latest", response_model=YieldPredictionOut)
def yield_latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    record = (
        db.query(YieldPrediction)
        .filter(YieldPrediction.farm_id == farm.id)
        .order_by(desc(YieldPrediction.id))
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No yield prediction yet — call /predict first.")
    return _out(record)
