import base64
import re
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.core.network_safety import is_safe_hardware_host
from app.db.database import get_db
from app.db.models import CameraSnapshot, Farm, FarmState, RobotAction
from app.deps import get_current_farm
from app.schemas.camera import CameraFrameOut, CameraMoveRequest, CameraSnapshotOut
from app.services.camera_render import render_frame

router = APIRouter(prefix="/api/camera", tags=["camera"])

PAN_LIMIT = 90
TILT_LIMIT = 45
STEP = 15

# The pan servo is physically wired to the motor-control ESP32-S3, not the
# AI-Thinker camera board (see motor_controls/motor_controls.ino — it has no
# free GPIOs left for a servo once every camera pin is used), so pan commands
# forward to robot_host. There is no hardware tilt axis; tilt only affects
# the simulated placeholder.
_PAN_ACTION = {"pan_left": "camera_left", "pan_right": "camera_right", "center": "camera_center"}


def _forward_camera_pan(farm: Farm, direction: str) -> None:
    action = _PAN_ACTION.get(direction)
    if not (farm.hardware_enabled and farm.robot_host and action):
        return
    if not is_safe_hardware_host(farm.robot_host):
        return
    try:
        httpx.get(f"http://{farm.robot_host}/command", params={"action": action}, timeout=3.0)
    except httpx.HTTPError:
        pass


async def _fetch_hardware_frame(camera_host: str) -> str | None:
    """Pull exactly one JPEG frame out of the AI-Thinker board's MJPEG
    /stream (see AI_THINKER_CAM/AI_THINKER_CAM.ino's stream_handler) and
    return it as a data: URL, for use where a still image is needed
    (snapshots) rather than a live <img> pointed at the stream directly."""
    if not is_safe_hardware_host(camera_host):
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            async with client.stream("GET", f"http://{camera_host}/stream") as resp:
                buf = b""
                length: int | None = None
                body_start = 0
                async for chunk in resp.aiter_bytes():
                    buf += chunk
                    if length is None:
                        header_end = buf.find(b"\r\n\r\n")
                        if header_end == -1:
                            if len(buf) > 4096:
                                return None
                            continue
                        match = re.search(rb"Content-Length:\s*(\d+)", buf[:header_end], re.IGNORECASE)
                        if not match:
                            return None
                        length = int(match.group(1))
                        body_start = header_end + 4
                    if len(buf) >= body_start + length:
                        jpeg_bytes = buf[body_start:body_start + length]
                        return f"data:image/jpeg;base64,{base64.b64encode(jpeg_bytes).decode('ascii')}"
    except (httpx.HTTPError, OSError):
        return None
    return None


def _get_state(db: Session, farm: Farm) -> FarmState:
    state = db.query(FarmState).filter(FarmState.farm_id == farm.id).first()
    if not state:
        state = FarmState(farm_id=farm.id)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/frame", response_model=CameraFrameOut)
def get_frame(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    state = _get_state(db, farm)
    image_data_url = render_frame(farm.id, state.camera_pan_deg, state.camera_tilt_deg)
    stream_url = f"http://{farm.camera_host}/stream" if farm.hardware_enabled and farm.camera_host else None
    return CameraFrameOut(
        image_data_url=image_data_url,
        pan_deg=state.camera_pan_deg,
        tilt_deg=state.camera_tilt_deg,
        timestamp=datetime.now(timezone.utc),
        stream_url=stream_url,
    )


@router.post("/move", response_model=CameraFrameOut)
def move(
    payload: CameraMoveRequest,
    farm: Farm = Depends(get_current_farm),
    db: Session = Depends(get_db),
):
    state = _get_state(db, farm)

    if payload.direction == "pan_left":
        state.camera_pan_deg = max(-PAN_LIMIT, state.camera_pan_deg - STEP)
    elif payload.direction == "pan_right":
        state.camera_pan_deg = min(PAN_LIMIT, state.camera_pan_deg + STEP)
    elif payload.direction == "tilt_up":
        state.camera_tilt_deg = min(TILT_LIMIT, state.camera_tilt_deg + STEP)
    elif payload.direction == "tilt_down":
        state.camera_tilt_deg = max(-TILT_LIMIT, state.camera_tilt_deg - STEP)
    elif payload.direction == "center":
        state.camera_pan_deg = 0
        state.camera_tilt_deg = 0
    else:
        raise HTTPException(status_code=400, detail=f"Unknown direction '{payload.direction}'.")

    _forward_camera_pan(farm, payload.direction)

    db.add(RobotAction(
        farm_id=farm.id,
        action_type="camera_move",
        detail={"direction": payload.direction, "pan": state.camera_pan_deg, "tilt": state.camera_tilt_deg},
        source="manual",
    ))
    db.commit()

    image_data_url = render_frame(farm.id, state.camera_pan_deg, state.camera_tilt_deg)
    stream_url = f"http://{farm.camera_host}/stream" if farm.hardware_enabled and farm.camera_host else None
    return CameraFrameOut(
        image_data_url=image_data_url,
        pan_deg=state.camera_pan_deg,
        tilt_deg=state.camera_tilt_deg,
        timestamp=datetime.now(timezone.utc),
        stream_url=stream_url,
    )


@router.post("/capture", response_model=CameraSnapshotOut, status_code=201)
async def capture(farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    state = _get_state(db, farm)
    image_data_url = None
    if farm.hardware_enabled and farm.camera_host:
        image_data_url = await _fetch_hardware_frame(farm.camera_host)
    if not image_data_url:
        image_data_url = render_frame(farm.id, state.camera_pan_deg, state.camera_tilt_deg)

    snapshot = CameraSnapshot(
        farm_id=farm.id,
        image_data_url=image_data_url,
        pan_deg=state.camera_pan_deg,
        tilt_deg=state.camera_tilt_deg,
    )
    db.add(snapshot)
    db.add(RobotAction(farm_id=farm.id, action_type="camera_capture", detail={}, source="manual"))
    db.commit()
    db.refresh(snapshot)
    return snapshot


@router.get("/snapshots", response_model=list[CameraSnapshotOut])
def snapshots(limit: int = 12, farm: Farm = Depends(get_current_farm), db: Session = Depends(get_db)):
    rows = (
        db.query(CameraSnapshot)
        .filter(CameraSnapshot.farm_id == farm.id)
        .order_by(desc(CameraSnapshot.id))
        .limit(max(1, min(limit, 60)))
        .all()
    )
    return rows
