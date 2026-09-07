from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.db.database import get_db
from app.db.models import Farm, FarmState, SensorReading
from app.deps import get_current_farm
from app.schemas.sensor import ManualNpkIn, ManualSensorReadingIn, SensorHistoryOut, SensorReadingOut
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

    def _save() -> tuple[SensorReading, FarmState | None]:
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
        return reading, state

    reading, state = await run_in_threadpool(_save)

    await manager.broadcast(farm.id, build_sensor_update_message(
        reading,
        state.pump_on if state else False,
        state.robot_connected if state else True,
    ))

    return reading


@router.post("/manual-npk", response_model=SensorReadingOut, status_code=201)
async def submit_manual_npk(
    payload: ManualNpkIn,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    """NPK + soil moisture from the farmer's handheld probe. Unlike
    /manual, this works for any farm regardless of sensor_mode — it's meant
    to run alongside live hardware-polled temp/humidity/rain (see
    services/hardware_poller.py), not replace the whole reading."""

    def _save() -> tuple[SensorReading, FarmState]:
        state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
        if state is None:
            state = FarmState(farm_id=farm.id)
            db.add(state)
        state.last_soil_moisture = payload.soil_moisture
        state.last_nitrogen = payload.nitrogen
        state.last_phosphorus = payload.phosphorus
        state.last_potassium = payload.potassium

        last = (
            db.query(SensorReading)
            .filter(SensorReading.farm_id == farm.id)
            .order_by(desc(SensorReading.id))
            .first()
        )
        reading = SensorReading(
            farm_id=farm.id,
            device_id=last.device_id if last else "ESP32_ROBOT_01",
            soil_moisture=payload.soil_moisture,
            temperature=last.temperature if last else 0.0,
            humidity=last.humidity if last else 0.0,
            rainfall=last.rainfall if last else 0.0,
            sunlight=last.sunlight if last else 8.0,
            wind_speed=last.wind_speed if last else 0.0,
            nitrogen=payload.nitrogen,
            phosphorus=payload.phosphorus,
            potassium=payload.potassium,
            rain_detected=last.rain_detected if last else False,
            status="MANUAL_NPK",
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        db.refresh(state)
        return reading, state

    reading, state = await run_in_threadpool(_save)

    await manager.broadcast(farm.id, build_sensor_update_message(
        reading, state.pump_on, state.robot_connected,
    ))

    return reading
