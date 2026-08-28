from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, FarmState, SensorReading
from app.deps import get_current_farm
from app.schemas.sensor import ManualSensorReadingIn, SensorHistoryOut, SensorReadingOut
from app.services.connection_manager import build_sensor_update_message, manager

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


@router.get("/latest", response_model=SensorReadingOut)
def get_latest(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    reading = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id))
        .first()
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No sensor readings yet for this farm.")
    return reading


@router.get("/history", response_model=SensorHistoryOut)
def get_history(
    limit: int = 60,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 500))
    rows = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id))
        .limit(limit)
        .all()
    )
    rows.reverse()
    return SensorHistoryOut(record_count=len(rows), history=rows)


@router.post("/manual", response_model=SensorReadingOut, status_code=201)
async def submit_manual_reading(
    payload: ManualSensorReadingIn,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    if farm.sensor_mode != "Manual":
        raise HTTPException(
            status_code=400,
            detail="Farm is in Auto sensor mode — switch to Manual mode before submitting a reading.",
        )

    last = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(desc(SensorReading.id))
        .first()
    )
    sunlight = last.sunlight if last else 8.0
    if payload.rain_detected:
        rainfall = last.rainfall if (last and last.rainfall > 5) else 20.0
    else:
        rainfall = 0.0

    reading = SensorReading(
        farm_id=farm.id,
        device_id=last.device_id if last else "ESP32_FIELD_01",
        soil_moisture=payload.soil_moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall=rainfall,
        sunlight=sunlight,
        wind_speed=payload.wind_speed,
        nitrogen=payload.nitrogen,
        phosphorus=payload.phosphorus,
        potassium=payload.potassium,
        rain_detected=payload.rain_detected,
        status="MANUAL",
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()

    await manager.broadcast(farm.id, build_sensor_update_message(
        reading,
        state.pump_on if state else False,
        state.lid_open if state else False,
        state.robot_connected if state else True,
    ))

    return reading
