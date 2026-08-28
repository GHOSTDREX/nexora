from pydantic import BaseModel


class FarmCreate(BaseModel):
    name: str = "My Farm"
    region: str = "North"
    latitude: float = 28.6139
    longitude: float = 77.2090
    field_area_hectare: float = 2.5
    soil_type: str = "Loamy"
    soil_ph: float = 6.5
    organic_carbon: float = 0.85
    electrical_conductivity: float = 1.5
    crop_type: str = "Wheat"
    crop_growth_stage: str = "Vegetative"
    season: str = "Rabi"
    mulching_used: str = "No"
    hardware_enabled: bool = False
    sensor_node_host: str = ""
    robot_host: str = ""
    camera_host: str = ""


class FarmUpdate(FarmCreate):
    pass


class FarmOut(FarmCreate):
    id: int
    irrigation_mode: str
    sensor_mode: str

    class Config:
        from_attributes = True


class IrrigationModeUpdate(BaseModel):
    irrigation_mode: str  # Auto | Manual


class SensorModeUpdate(BaseModel):
    sensor_mode: str  # Auto | Manual
