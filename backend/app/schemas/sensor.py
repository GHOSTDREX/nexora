from datetime import datetime

from pydantic import BaseModel, Field


class SensorReadingOut(BaseModel):
    id: int
    device_id: str
    timestamp: datetime
    soil_moisture: float
    temperature: float
    humidity: float
    rainfall: float
    sunlight: float
    wind_speed: float
    nitrogen: float
    phosphorus: float
    potassium: float
    rain_detected: bool
    status: str

    class Config:
        from_attributes = True


class SensorHistoryOut(BaseModel):
    record_count: int
    history: list[SensorReadingOut]


class ManualSensorReadingIn(BaseModel):
    temperature: float = Field(ge=-20, le=70)
    humidity: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)
    nitrogen: float = Field(ge=0, le=200)
    phosphorus: float = Field(ge=0, le=150)
    potassium: float = Field(ge=0, le=200)
    wind_speed: float = Field(ge=0, le=150)
    rain_detected: bool = False
