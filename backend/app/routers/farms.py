import random

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm, FarmState, SensorReading, User
from app.deps import get_current_farm, get_current_user
from app.schemas.farm import FarmCreate, FarmOut, FarmUpdate, IrrigationModeUpdate, SensorModeUpdate

router = APIRouter(prefix="/api/farm", tags=["farm"])


def _seed_initial_reading(db: Session, farm: Farm):
    """Seed one reading so a brand-new farm doesn't show an empty dashboard
    before the simulator's first tick."""
    reading = SensorReading(
        farm_id=farm.id,
        device_id="ESP32_FIELD_01",
        soil_moisture=random.uniform(45, 60),
        temperature=random.uniform(24, 30),
        humidity=random.uniform(55, 70),
        rainfall=0.0,
        sunlight=random.uniform(6, 10),
        wind_speed=random.uniform(5, 12),
        nitrogen=random.uniform(60, 100),
        phosphorus=random.uniform(30, 60),
        potassium=random.uniform(40, 90),
        rain_detected=False,
        status="LIVE",
    )
    db.add(reading)


@router.post("", response_model=FarmOut, status_code=201)
def create_farm(
    payload: FarmCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Farm).filter(Farm.owner_id == user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Farm already exists for this account.")

    farm = Farm(owner_id=user.id, **payload.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)

    # Each farm gets its own independent simulation seed/baseline so two
    # farms never drift with identical sensor values.
    rng = random.Random(farm.id * 7919 + 13)
    baseline = {
        "soil_moisture": rng.uniform(50, 65),
        "temperature": rng.uniform(24, 32),
        "humidity": rng.uniform(50, 75),
        "nitrogen": rng.uniform(60, 110),
        "phosphorus": rng.uniform(30, 70),
        "potassium": rng.uniform(40, 100),
        "wind_speed": rng.uniform(5, 15),
    }
    state = FarmState(farm_id=farm.id, rng_seed=rng.randint(1, 1_000_000), sim_baseline=baseline)
    db.add(state)

    _seed_initial_reading(db, farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("", response_model=FarmOut)
def get_farm(farm: Farm = Depends(get_current_farm)):
    return farm


@router.put("", response_model=FarmOut)
def update_farm(
    payload: FarmUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    for key, value in payload.model_dump().items():
        setattr(farm, key, value)
    db.commit()
    db.refresh(farm)
    return farm


@router.patch("/irrigation-mode", response_model=FarmOut)
def set_irrigation_mode(
    payload: IrrigationModeUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    if payload.irrigation_mode not in ("Auto", "Manual"):
        raise HTTPException(status_code=400, detail="irrigation_mode must be 'Auto' or 'Manual'.")
    farm.irrigation_mode = payload.irrigation_mode
    db.commit()
    db.refresh(farm)
    return farm


@router.patch("/sensor-mode", response_model=FarmOut)
def set_sensor_mode(
    payload: SensorModeUpdate,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    if payload.sensor_mode not in ("Auto", "Manual"):
        raise HTTPException(status_code=400, detail="sensor_mode must be 'Auto' or 'Manual'.")
    farm.sensor_mode = payload.sensor_mode
    db.commit()
    db.refresh(farm)
    return farm
