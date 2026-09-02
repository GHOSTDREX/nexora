"""
AgriNova — Live sensor + automation simulator.

No physical ESP32 hardware is connected yet, so this background loop stands
in for it: every tick it advances each farm's sensor readings with a small
random walk around that farm's own baseline (seeded from FarmState at farm
creation, so two farms never show identical numbers), runs the irrigation
automation state machine described in the MVP spec, and pushes the results
out over that farm's WebSocket connections. Everything
here writes through the same tables a real ESP32 ingesting via the REST API
would use, so swapping in real hardware later is a drop-in replacement.
"""

import asyncio
import logging
import random
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.config import SIMULATOR_TICK_SECONDS
from app.db.database import SessionLocal
from app.db.models import Alert, Farm, FarmState, SensorReading
from app.services.connection_manager import build_sensor_update_message, manager

logger = logging.getLogger("agrinova.simulator")

LOW_MOISTURE_THRESHOLD = 32.0
TARGET_MOISTURE = 55.0
RAIN_PROBABILITY_PER_TICK = 0.05
RAIN_STOP_PROBABILITY_PER_TICK = 0.35
DISCONNECT_PROBABILITY_PER_TICK = 0.004
RECONNECT_PROBABILITY_PER_TICK = 0.6
NPK_ALERT_EVERY_N_TICKS = 45

# Per-process RNG continuity per farm (reseeded from FarmState.rng_seed the
# first time a farm is seen so restarts stay reproducible-ish but each farm
# is independent of every other farm).
_rngs: dict[int, random.Random] = {}
_tick_counts: dict[int, int] = {}


def _rng_for(farm_id: int, seed: int) -> random.Random:
    if farm_id not in _rngs:
        _rngs[farm_id] = random.Random(seed or farm_id)
    return _rngs[farm_id]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _drift(rng: random.Random, current: float, baseline: float, low: float, high: float, step: float) -> float:
    pulled = current + (baseline - current) * 0.03
    noise = rng.uniform(-step, step)
    return _clamp(pulled + noise, low, high)


async def _tick_farm(db: Session, farm: Farm, state: FarmState):
    rng = _rng_for(farm.id, state.rng_seed)
    baseline = state.sim_baseline or {}
    tick_no = _tick_counts.get(farm.id, 0) + 1
    _tick_counts[farm.id] = tick_no

    last = (
        db.query(SensorReading)
        .filter(SensorReading.farm_id == farm.id)
        .order_by(SensorReading.id.desc())
        .first()
    )

    soil_moisture = last.soil_moisture if last else baseline.get("soil_moisture", 55.0)
    temperature = last.temperature if last else baseline.get("temperature", 28.0)
    humidity = last.humidity if last else baseline.get("humidity", 60.0)
    nitrogen = last.nitrogen if last else baseline.get("nitrogen", 80.0)
    phosphorus = last.phosphorus if last else baseline.get("phosphorus", 45.0)
    potassium = last.potassium if last else baseline.get("potassium", 60.0)
    wind_speed = last.wind_speed if last else baseline.get("wind_speed", 10.0)
    sunlight = last.sunlight if last else 8.0

    # Rain state machine
    last_rain_detected = bool(last.rain_detected) if last else False
    rain_detected = last_rain_detected
    if rain_detected:
        if rng.random() < RAIN_STOP_PROBABILITY_PER_TICK:
            rain_detected = False
    else:
        if rng.random() < RAIN_PROBABILITY_PER_TICK:
            rain_detected = True

    new_alerts: list[Alert] = []

    if rain_detected:
        rainfall = _clamp((last.rainfall if last else 0) + rng.uniform(1, 6), 0, 400)
        soil_moisture = _clamp(soil_moisture + rng.uniform(2, 5), 0, 100)
        humidity = _clamp(humidity + rng.uniform(1, 3), 0, 100)
        sunlight = _clamp(sunlight - rng.uniform(1, 3), 0, 14)
    else:
        rainfall = _clamp((last.rainfall if last else 0) * 0.9, 0, 400)
        soil_moisture = _drift(rng, soil_moisture, baseline.get("soil_moisture", 55.0), 5, 95, 1.5)
        sunlight = _clamp(_drift(rng, sunlight, 8.5, 3, 14, 0.6), 0, 14)

    temperature = _drift(rng, temperature, baseline.get("temperature", 28.0), 12, 42, 0.6)
    humidity = _clamp(_drift(rng, humidity, baseline.get("humidity", 60.0), 25, 95, 1.2), 0, 100)
    wind_speed = _clamp(_drift(rng, wind_speed, baseline.get("wind_speed", 10.0), 0, 45, 1.0), 0, 150)
    nitrogen = _clamp(_drift(rng, nitrogen, baseline.get("nitrogen", 80.0), 20, 150, 1.0), 0, 200)
    phosphorus = _clamp(_drift(rng, phosphorus, baseline.get("phosphorus", 45.0), 10, 100, 0.8), 0, 150)
    potassium = _clamp(_drift(rng, potassium, baseline.get("potassium", 60.0), 15, 130, 1.0), 0, 200)

    # --- Automation: irrigation (Auto mode only) ---
    if farm.irrigation_mode == "Auto":
        if not state.pump_on and soil_moisture < LOW_MOISTURE_THRESHOLD:
            state.pump_on = True
            new_alerts.append(Alert(farm_id=farm.id, code="irrigation_started_auto", severity="warning",
                                     params={"soil_moisture": round(soil_moisture, 1)}))
        elif state.pump_on and soil_moisture >= TARGET_MOISTURE:
            state.pump_on = False
            new_alerts.append(Alert(farm_id=farm.id, code="irrigation_completed_auto", severity="info",
                                     params={"soil_moisture": round(soil_moisture, 1)}))

    if state.pump_on:
        soil_moisture = _clamp(soil_moisture + rng.uniform(3, 6), 0, 100)

    if rain_detected and not last_rain_detected:
        new_alerts.append(Alert(farm_id=farm.id, code="rain_detected", severity="info", params={}))

    # --- Robot connectivity flapping (rare, for realism) ---
    if state.robot_connected and rng.random() < DISCONNECT_PROBABILITY_PER_TICK:
        state.robot_connected = False
        new_alerts.append(Alert(farm_id=farm.id, code="robot_disconnected", severity="critical", params={}))
    elif not state.robot_connected and rng.random() < RECONNECT_PROBABILITY_PER_TICK:
        state.robot_connected = True
        new_alerts.append(Alert(farm_id=farm.id, code="robot_reconnected", severity="info", params={}))

    if tick_no % NPK_ALERT_EVERY_N_TICKS == 0:
        new_alerts.append(Alert(farm_id=farm.id, code="npk_reading_updated", severity="info", params={}))

    reading = SensorReading(
        farm_id=farm.id,
        device_id="ESP32_FIELD_01",
        soil_moisture=round(soil_moisture, 1),
        temperature=round(temperature, 1),
        humidity=round(humidity, 1),
        rainfall=round(rainfall, 1),
        sunlight=round(sunlight, 1),
        wind_speed=round(wind_speed, 1),
        nitrogen=round(nitrogen, 1),
        phosphorus=round(phosphorus, 1),
        potassium=round(potassium, 1),
        rain_detected=rain_detected,
        status="LIVE",
    )
    db.add(reading)
    for alert in new_alerts:
        db.add(alert)
    db.commit()
    db.refresh(reading)

    await manager.broadcast(farm.id, build_sensor_update_message(
        reading, state.pump_on, state.robot_connected, new_alerts,
    ))


async def run_simulator_loop(stop_event: asyncio.Event):
    logger.info("AgriNova simulator loop started (tick=%ss)", SIMULATOR_TICK_SECONDS)
    while not stop_event.is_set():
        db = SessionLocal()
        try:
            farms = db.query(Farm).all()
            for farm in farms:
                if farm.sensor_mode == "Manual" or farm.hardware_enabled:
                    continue
                state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
                if state is None:
                    seed = farm.id * 7919 + 13
                    state = FarmState(farm_id=farm.id, rng_seed=seed, sim_baseline={})
                    db.add(state)
                    db.commit()
                    db.refresh(state)
                try:
                    await _tick_farm(db, farm, state)
                except Exception:
                    logger.exception("Simulator tick failed for farm %s", farm.id)
                    db.rollback()
        finally:
            db.close()

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=SIMULATOR_TICK_SECONDS)
        except asyncio.TimeoutError:
            pass
    logger.info("AgriNova simulator loop stopped")
