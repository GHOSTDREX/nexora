import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.network_safety import is_safe_hardware_host
from app.db.database import get_db
from app.db.models import Alert, Farm, FarmState, RobotAction
from app.deps import get_current_farm
from app.schemas.robot import RobotActionOut, RobotActionRequest, RobotStatusOut

router = APIRouter(prefix="/api/robot", tags=["robot"])

VALID_ACTIONS = {
    "pump_on", "pump_off",
    "lid_open", "lid_close",
    "dispense_seed", "dispense_fertilizer",
    "move_forward", "move_back", "move_left", "move_right", "move_stop",
    "seed_on", "seed_off",
    "plow_on", "plow_off",
}

# Action names here are sent to motor_controls.ino verbatim — the app's own
# vocabulary was designed to already match the firmware's /command?action=
# values 1:1 (see motor_controls/motor_controls.ino) so no translation table
# is needed; only "dispense_seed"/"dispense_fertilizer" have no hardware
# equivalent yet and are simulation-only.
HARDWARE_FORWARDED_ACTIONS = {
    "pump_on", "pump_off",
    "move_forward", "move_back", "move_left", "move_right", "move_stop",
    "seed_on", "seed_off",
    "plow_on", "plow_off",
}


def _forward_to_robot(farm: Farm, action: str) -> None:
    if not (farm.hardware_enabled and farm.robot_host and action in HARDWARE_FORWARDED_ACTIONS):
        return
    if not is_safe_hardware_host(farm.robot_host):
        return
    try:
        httpx.get(f"http://{farm.robot_host}/command", params={"action": action}, timeout=3.0)
    except httpx.HTTPError:
        pass  # best-effort — the hardware poller's own connectivity check surfaces persistent failures


def _get_state(db: Session, farm: Farm) -> FarmState:
    state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
    if not state:
        state = FarmState(farm_id=farm.id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/status", response_model=RobotStatusOut)
def get_status(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    state = _get_state(db, farm)
    return RobotStatusOut(
        robot_connected=state.robot_connected,
        robot_battery_pct=state.robot_battery_pct,
        pump_on=state.pump_on,
        lid_open=state.lid_open,
        irrigation_mode=farm.irrigation_mode,
        camera_pan_deg=state.camera_pan_deg,
        camera_tilt_deg=state.camera_tilt_deg,
    )


@router.get("/actions", response_model=list[RobotActionOut])
def get_actions(limit: int = 30, farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    rows = (
        db.query(RobotAction)
        .filter(RobotAction.farm_id == farm.id)
        .order_by(desc(RobotAction.id))
        .limit(max(1, min(limit, 200)))
        .all()
    )
    return rows


@router.post("/action", response_model=RobotActionOut)
def manual_action(
    payload: RobotActionRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    if payload.action_type not in VALID_ACTIONS:
        raise HTTPException(status_code=400, detail=f"Unknown action_type '{payload.action_type}'.")

    # The simulator skips ticking a farm entirely while sensor_mode is
    # "Manual" (see services/simulator.py), so its auto pump-off logic never
    # runs then either — this escape hatch keeps the pump controllable even
    # though irrigation_mode itself is still "Auto".
    if farm.irrigation_mode == "Auto" and farm.sensor_mode != "Manual" and payload.action_type in ("pump_on", "pump_off"):
        raise HTTPException(
            status_code=409,
            detail="Irrigation is in Auto mode — switch to Manual mode to control the pump directly.",
        )

    state = _get_state(db, farm)
    detail: dict = {}

    if payload.action_type == "pump_on":
        state.pump_on = True
    elif payload.action_type == "pump_off":
        state.pump_on = False
    elif payload.action_type == "lid_open":
        state.lid_open = True
    elif payload.action_type == "lid_close":
        state.lid_open = False

    _forward_to_robot(farm, payload.action_type)

    action_row = RobotAction(farm_id=farm.id, action_type=payload.action_type, detail=detail, source="manual")
    db.add(action_row)

    alert_code = {
        "pump_on": "irrigation_started_manual",
        "pump_off": "irrigation_stopped_manual",
        "lid_open": "harvesting_lid_opened_manual",
        "lid_close": "harvesting_lid_closed_manual",
        "dispense_seed": "seed_dispensed",
        "dispense_fertilizer": "fertilizer_dispensed",
    }.get(payload.action_type)
    if alert_code:
        db.add(Alert(farm_id=farm.id, code=alert_code, severity="info", params={}))

    db.commit()
    db.refresh(action_row)

    return RobotActionOut(action_type=payload.action_type, detail=detail, source="manual", timestamp=action_row.timestamp)
