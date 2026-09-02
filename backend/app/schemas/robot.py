from datetime import datetime

from pydantic import BaseModel, Field


class RobotStatusOut(BaseModel):
    robot_connected: bool
    robot_battery_pct: float
    pump_on: bool
    motor_speed: int
    irrigation_mode: str
    camera_pan_deg: int
    camera_tilt_deg: int


class RobotActionRequest(BaseModel):
    action_type: str  # pump_on | pump_off | seed_on | seed_off | plow_on | plow_off | set_speed | move_forward | move_back | move_left | move_right | move_stop
    value: int | None = Field(default=None, ge=0, le=255)  # only used by set_speed


class RobotActionOut(BaseModel):
    action_type: str
    detail: dict
    source: str
    timestamp: datetime

    class Config:
        from_attributes = True
