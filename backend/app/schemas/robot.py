from datetime import datetime

from pydantic import BaseModel


class RobotStatusOut(BaseModel):
    robot_connected: bool
    robot_battery_pct: float
    pump_on: bool
    lid_open: bool
    irrigation_mode: str
    camera_pan_deg: int
    camera_tilt_deg: int


class RobotActionRequest(BaseModel):
    action_type: str  # pump_on | pump_off | lid_open | lid_close | dispense_seed | dispense_fertilizer | move_forward | move_back | move_left | move_right | move_stop


class RobotActionOut(BaseModel):
    action_type: str
    detail: dict
    source: str
    timestamp: datetime

    class Config:
        from_attributes = True
