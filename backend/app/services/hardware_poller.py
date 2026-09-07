"""
AgriNova — Real ESP32 hardware poller.

Runs alongside services/simulator.py, but only touches farms with
hardware_enabled=True (the simulator skips those — see its farm loop).
Instead of generating random values, it polls the robot controller board's
/status HTTP endpoint over the LAN every tick, writes the reading through
the exact same SensorReading table + WebSocket broadcast path the simulator
uses (see connection_manager.build_sensor_update_message), and forwards the
same irrigation-automation decision to the same board's /command endpoint
instead of only flipping an in-memory flag.

Motors, the DHT22 and the rain sensor all live on one consolidated ESP32-S3
board now (motor_controls.ino) — /status does not report rainfall (mm),
sunlight, or wind, so those three SensorReading fields are written as 0.0
for hardware farms rather than fabricated.

Soil moisture and NPK come from a second, separate standalone board
(Farm.sensor_node_host) carrying only a soil-moisture probe and an RS485
NPK sensor — deliberately off the robot chassis so it can be walked to a
spot in the field. When that host is set and reachable, this module polls
its /sensors endpoint the same way it polls the robot's /status, and
writes the result into FarmState.last_nitrogen etc. When it's unset or
unreachable, those FarmState fields simply keep whatever value they last
had — from an earlier successful poll, or a manual submission via
POST /api/sensors/manual-npk (see routers/sensors.py) — carried forward
into every reading here rather than zeroed out.
"""

import asyncio
import logging
import random

import httpx
from sqlalchemy.orm import Session

from app.core.config import SIMULATOR_TICK_SECONDS
from app.core.network_safety import is_safe_hardware_host
from app.db.database import SessionLocal
from app.db.models import Alert, Farm, FarmState, SensorReading
from app.services.connection_manager import build_sensor_update_message, manager
from app.services.simulator import LOW_MOISTURE_THRESHOLD, TARGET_MOISTURE, simulate_battery_drift

logger = logging.getLogger("agrinova.hardware")

HTTP_TIMEOUT_SECONDS = 3.0

# Battery falls back to the same simulated drift as sensor-less farms
# whenever there's no real reading — disconnected, or firmware that
# doesn't report "battery_pct" yet. One shared RNG is fine here (unlike
# the sensor simulator, this doesn't need per-farm reproducibility).
_battery_rng = random.Random()


def _get_state(db: Session, farm: Farm) -> FarmState:
    state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
    if state is None:
        state = FarmState(farm_id=farm.id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


async def _send_robot_command(client: httpx.AsyncClient, robot_host: str, action: str) -> bool:
    if not robot_host or not is_safe_hardware_host(robot_host):
        return False
    try:
        resp = await client.get(f"http://{robot_host}/command", params={"action": action}, timeout=HTTP_TIMEOUT_SECONDS)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


async def _poll_soil_probe(client: httpx.AsyncClient, state: FarmState, sensor_node_host: str):
    """Best-effort — a missing or unreachable probe just means FarmState
    keeps whatever soil/NPK values it already had (see module docstring)."""
    if not sensor_node_host or not is_safe_hardware_host(sensor_node_host):
        return
    try:
        resp = await client.get(f"http://{sensor_node_host}/sensors", timeout=HTTP_TIMEOUT_SECONDS)
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError):
        return
    state.last_soil_moisture = float(payload.get("soil_moisture", state.last_soil_moisture))
    state.last_nitrogen = float(payload.get("nitrogen", state.last_nitrogen))
    state.last_phosphorus = float(payload.get("phosphorus", state.last_phosphorus))
    state.last_potassium = float(payload.get("potassium", state.last_potassium))


async def _poll_farm(client: httpx.AsyncClient, db: Session, farm: Farm):
    if not farm.robot_host or not is_safe_hardware_host(farm.robot_host):
        return

    state = _get_state(db, farm)

    try:
        resp = await client.get(f"http://{farm.robot_host}/status", timeout=HTTP_TIMEOUT_SECONDS)
        resp.raise_for_status()
        payload = resp.json()
    except (httpx.HTTPError, ValueError):
        if state.robot_connected:
            state.robot_connected = False
            db.add(Alert(farm_id=farm.id, code="robot_disconnected", severity="critical", params={}))
        state.robot_battery_pct = simulate_battery_drift(_battery_rng, state.robot_battery_pct)
        db.commit()
        return

    new_alerts: list[Alert] = []

    if not state.robot_connected:
        state.robot_connected = True
        new_alerts.append(Alert(farm_id=farm.id, code="robot_reconnected", severity="info", params={}))

    # Live from the separate soil/NPK probe board when configured and
    # reachable; otherwise these FarmState fields keep their last known
    # value (see module docstring).
    await _poll_soil_probe(client, state, farm.sensor_node_host)
    soil_moisture = state.last_soil_moisture

    if "battery_pct" in payload:
        state.robot_battery_pct = round(float(payload["battery_pct"]), 1)
    else:
        state.robot_battery_pct = simulate_battery_drift(_battery_rng, state.robot_battery_pct)

    if farm.irrigation_mode == "Auto":
        if not state.pump_on and soil_moisture < LOW_MOISTURE_THRESHOLD:
            if await _send_robot_command(client, farm.robot_host, "pump_on"):
                state.pump_on = True
                new_alerts.append(Alert(
                    farm_id=farm.id, code="irrigation_started_auto", severity="warning",
                    params={"soil_moisture": round(soil_moisture, 1)},
                ))
        elif state.pump_on and soil_moisture >= TARGET_MOISTURE:
            if await _send_robot_command(client, farm.robot_host, "pump_off"):
                state.pump_on = False
                new_alerts.append(Alert(
                    farm_id=farm.id, code="irrigation_completed_auto", severity="info",
                    params={"soil_moisture": round(soil_moisture, 1)},
                ))

    reading = SensorReading(
        farm_id=farm.id,
        device_id="ESP32_ROBOT_01",
        soil_moisture=soil_moisture,
        temperature=float(payload.get("temp", 0.0)),
        humidity=float(payload.get("hum", 0.0)),
        rainfall=0.0,
        sunlight=0.0,
        wind_speed=0.0,
        nitrogen=state.last_nitrogen,
        phosphorus=state.last_phosphorus,
        potassium=state.last_potassium,
        rain_detected=bool(payload.get("rain", False)),
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


async def run_hardware_poller_loop(stop_event: asyncio.Event):
    logger.info("AgriNova hardware poller loop started (tick=%ss)", SIMULATOR_TICK_SECONDS)
    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            db = SessionLocal()
            try:
                farms = db.query(Farm).filter(Farm.hardware_enabled.is_(True)).all()
                for farm in farms:
                    try:
                        await _poll_farm(client, db, farm)
                    except Exception:
                        logger.exception("Hardware poll failed for farm %s", farm.id)
                        db.rollback()
            finally:
                db.close()

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=SIMULATOR_TICK_SECONDS)
            except asyncio.TimeoutError:
                pass
    logger.info("AgriNova hardware poller loop stopped")
