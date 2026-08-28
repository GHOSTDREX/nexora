from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    code: str
    severity: str
    params: dict
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True
