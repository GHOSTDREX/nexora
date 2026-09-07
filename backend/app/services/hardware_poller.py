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

All DB reads/writes here run via asyncio.to_thread (see simulator.py's
_tick_farm for the same pattern and rationale) — against local SQLite the
per-call latency is negligible, but against a real network-hop database a
sync call made directly on the event loop would block every other request
in the process for its duration, once per tick. Only the actual hardware
HTTP calls (bounded by HTTP_TIMEOUT_SECONDS) stay as plain awaited async
calls on the main loop, since they're already non-blocking there.
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


def _list_hardware_farms() -> list[Farm]:
    db = SessionLocal()
    try:
        farms = db.query(Farm).filter(Farm.hardware_enabled.is_(True)).all()
        for farm in farms:
            db.expunge(farm)
        return farms
    finally:
        db.close()


async def _fetch_json(client: httpx.AsyncClient, host: str, path: str) -> dict | None:
    if not host or not is_safe_hardware_host(host):
        return None
    try:
        resp = await client.get(f"http://{host}{path}", timeout=HTTP_TIMEOUT_SECONDS)
        resp.raise_for_status()
        return resp.json()
    except (httpx.HTTPError, ValueError):
        return None


async def _send_robot_command(client: httpx.AsyncClient, robot_host: str, action: str) -> bool:
    if not robot_host or not is_safe_hardware_host(robot_host):
        return False
    try:
        resp = await client.get(f"http://{robot_host}/command", params={"action": action}, timeout=HTTP_TIMEOUT_SECONDS)
        return resp.status_code == 200
    except httpx.HTTPError:
        return False


def _mark_disconnected_sync(farm_id: int):
    db = SessionLocal()
    try:
        state = db.query(FarmState).filter(FarmState.farm_id == farm_id).first()
        if state is None:
            return
        if state.robot_connected:
            state.robot_connected = False
            db.add(Alert(farm_id=farm_id, code="robot_disconnected", severity="critical", params={}))
        state.robot_battery_pct = simulate_battery_drift(_battery_rng, state.robot_battery_pct)
        db.commit()
    finally:
        db.close()


def _apply_probe_payload(state: FarmState, probe_payload: dict | None):
    """Best-effort — a missing or unreachable probe just means FarmState
    keeps whatever soil/NPK values it already had (see module docstring)."""
    if probe_payload is None:
        return
    state.last_soil_moisture = float(probe_payload.get("soil_moisture", state.last_soil_moisture))
    state.last_nitrogen = float(probe_payload.get("nitrogen", state.last_nitrogen))
    state.last_phosphorus = float(probe_payload.get("phosphorus", state.last_phosphorus))
    state.last_potassium = float(probe_payload.get("potassium", state.last_potassium))


def _prepare_tick_sync(farm: Farm, robot_payload: dict, probe_payload: dict | None) -> dict:
    """All DB reads + the parts of the write that don't depend on an
    irrigation command's outcome. Returns everything run_hardware_poller_loop
    needs to decide whether to fire a pump command and to finish the write
    afterward in _finish_tick_sync."""
    db = SessionLocal()
    try:
        state = _get_state(db, farm)
        new_alerts: list[Alert] = []

        if not state.robot_connected:
            state.robot_connected = True
            new_alerts.append(Alert(farm_id=farm.id, code="robot_reconnected", severity="info", params={}))

        _apply_probe_payload(state, probe_payload)
        soil_moisture = state.last_soil_moisture

        if "battery_pct" in robot_payload:
            state.robot_battery_pct = round(float(robot_payload["battery_pct"]), 1)
        else:
            state.robot_battery_pct = simulate_battery_drift(_battery_rng, state.robot_battery_pct)

        want_pump_on = (
            farm.irrigation_mode == "Auto" and not state.pump_on and soil_moisture < LOW_MOISTURE_THRESHOLD
        )
        want_pump_off = (
            farm.irrigation_mode == "Auto" and state.pump_on and soil_moisture >= TARGET_MOISTURE
        )

        for alert in new_alerts:
            db.add(alert)
        db.commit()

        return {
            "soil_moisture": soil_moisture,
            "pump_on": state.pump_on,
            "robot_connected": state.robot_connected,
            "want_pump_on": want_pump_on,
            "want_pump_off": want_pump_off,
        }
    finally:
        db.close()


def _finish_tick_sync(
    farm: Farm, robot_payload: dict, prepared: dict, pump_command_result: bool | None,
) -> tuple[SensorReading, list[Alert], bool, bool]:
    db = SessionLocal()
    try:
        state = _get_state(db, farm)
        new_alerts: list[Alert] = []
        soil_moisture = prepared["soil_moisture"]

        if prepared["want_pump_on"] and pump_command_result:
            state.pump_on = True
            new_alerts.append(Alert(
                farm_id=farm.id, code="irrigation_started_auto", severity="warning",
                params={"soil_moisture": round(soil_moisture, 1)},
            ))
        elif prepared["want_pump_off"] and pump_command_result:
            state.pump_on = False
            new_alerts.append(Alert(
                farm_id=farm.id, code="irrigation_completed_auto", severity="info",
                params={"soil_moisture": round(soil_moisture, 1)},
            ))

        reading = SensorReading(
            farm_id=farm.id,
            device_id="ESP32_ROBOT_01",
            soil_moisture=soil_moisture,
            temperature=float(robot_payload.get("temp", 0.0)),
            humidity=float(robot_payload.get("hum", 0.0)),
            rainfall=0.0,
            sunlight=0.0,
            wind_speed=0.0,
            nitrogen=state.last_nitrogen,
            phosphorus=state.last_phosphorus,
            potassium=state.last_potassium,
            rain_detected=bool(robot_payload.get("rain", False)),
            status="LIVE",
        )
        db.add(reading)
        for alert in new_alerts:
            db.add(alert)
        db.commit()
        db.refresh(reading)

        return reading, new_alerts, state.pump_on, state.robot_connected
    finally:
        db.close()


async def _poll_farm(client: httpx.AsyncClient, farm: Farm):
    if not farm.robot_host or not is_safe_hardware_host(farm.robot_host):
        return

    robot_payload = await _fetch_json(client, farm.robot_host, "/status")
    if robot_payload is None:
        await asyncio.to_thread(_mark_disconnected_sync, farm.id)
        return

    probe_payload = await _fetch_json(client, farm.sensor_node_host, "/sensors")

    prepared = await asyncio.to_thread(_prepare_tick_sync, farm, robot_payload, probe_payload)

    pump_command_result: bool | None = None
    if prepared["want_pump_on"]:
        pump_command_result = await _send_robot_command(client, farm.robot_host, "pump_on")
    elif prepared["want_pump_off"]:
        pump_command_result = await _send_robot_command(client, farm.robot_host, "pump_off")

    reading, new_alerts, pump_on, robot_connected = await asyncio.to_thread(
        _finish_tick_sync, farm, robot_payload, prepared, pump_command_result,
    )

    await manager.broadcast(farm.id, build_sensor_update_message(
        reading, pump_on, robot_connected, new_alerts,
    ))


async def run_hardware_poller_loop(stop_event: asyncio.Event):
    logger.info("AgriNova hardware poller loop started (tick=%ss)", SIMULATOR_TICK_SECONDS)
    async with httpx.AsyncClient() as client:
        while not stop_event.is_set():
            farms = await asyncio.to_thread(_list_hardware_farms)
            for farm in farms:
                try:
                    await _poll_farm(client, farm)
                except Exception:
                    logger.exception("Hardware poll failed for farm %s", farm.id)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=SIMULATOR_TICK_SECONDS)
            except asyncio.TimeoutError:
                pass
    logger.info("AgriNova hardware poller loop stopped")
