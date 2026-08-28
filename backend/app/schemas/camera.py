from datetime import datetime

from pydantic import BaseModel


class CameraFrameOut(BaseModel):
    image_data_url: str
    pan_deg: int
    tilt_deg: int
    timestamp: datetime
    stream_url: str | None = None


class CameraMoveRequest(BaseModel):
    direction: str  # pan_left | pan_right | tilt_up | tilt_down | center


class CameraSnapshotOut(BaseModel):
    id: int
    image_data_url: str
    pan_deg: int
    tilt_deg: int
    timestamp: datetime

    class Config:
        from_attributes = True
