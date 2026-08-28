"""
AgriNova Backend — ORM models.

Hierarchy: User -> Farm -> {Device, SensorReading, RobotAction, CameraSnapshot,
Alert, IrrigationPrediction, CropRecommendation, FertilizerRecommendation,
SoilHealthRecord, ChatMessage, FarmState}

Every child table carries farm_id so all queries can be scoped to the
authenticated user's own farm (see app.deps.get_current_farm).
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    preferred_language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    farm: Mapped["Farm"] = relationship(back_populates="owner", uselist=False, cascade="all, delete-orphan")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), default="My Farm")
    region: Mapped[str] = mapped_column(String(64), default="North")
    latitude: Mapped[float] = mapped_column(Float, default=28.6139)
    longitude: Mapped[float] = mapped_column(Float, default=77.2090)

    field_area_hectare: Mapped[float] = mapped_column(Float, default=2.5)
    soil_type: Mapped[str] = mapped_column(String(32), default="Loamy")
    soil_ph: Mapped[float] = mapped_column(Float, default=6.5)
    organic_carbon: Mapped[float] = mapped_column(Float, default=0.85)
    electrical_conductivity: Mapped[float] = mapped_column(Float, default=1.5)
    crop_type: Mapped[str] = mapped_column(String(32), default="Wheat")
    crop_growth_stage: Mapped[str] = mapped_column(String(32), default="Vegetative")
    season: Mapped[str] = mapped_column(String(16), default="Rabi")
    mulching_used: Mapped[str] = mapped_column(String(8), default="No")

    irrigation_mode: Mapped[str] = mapped_column(String(16), default="Auto")  # Auto | Manual
    sensor_mode: Mapped[str] = mapped_column(String(16), default="Auto")  # Auto | Manual

    # Real ESP32 hardware, LAN-reachable (mDNS hostname or IP), no scheme/port —
    # e.g. "agrinova-sensors.local". When hardware_enabled, the hardware_poller
    # service polls sensor_node_host instead of the simulator, and robot/camera
    # commands are forwarded to robot_host/camera_host instead of only being
    # recorded against simulated state.
    hardware_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    sensor_node_host: Mapped[str] = mapped_column(String(128), default="")
    robot_host: Mapped[str] = mapped_column(String(128), default="")
    camera_host: Mapped[str] = mapped_column(String(128), default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

    owner: Mapped["User"] = relationship(back_populates="farm")


class FarmState(Base):
    """Live/mutable automation + robot + camera state — one row per farm."""

    __tablename__ = "farm_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), unique=True, nullable=False)

    pump_on: Mapped[bool] = mapped_column(Boolean, default=False)
    lid_open: Mapped[bool] = mapped_column(Boolean, default=False)
    robot_connected: Mapped[bool] = mapped_column(Boolean, default=True)
    robot_battery_pct: Mapped[float] = mapped_column(Float, default=92.0)

    camera_pan_deg: Mapped[int] = mapped_column(Integer, default=0)
    camera_tilt_deg: Mapped[int] = mapped_column(Integer, default=0)

    rng_seed: Mapped[int] = mapped_column(Integer, default=0)
    sim_baseline: Mapped[dict] = mapped_column(JSON, default=dict)

    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    device_type: Mapped[str] = mapped_column(String(32), nullable=False)  # robot | sensor_node | camera
    status: Mapped[str] = mapped_column(String(16), default="LIVE")
    last_seen: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    device_id: Mapped[str] = mapped_column(String(64), default="ESP32_FIELD_01")
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    soil_moisture: Mapped[float] = mapped_column(Float)
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[float] = mapped_column(Float)
    rainfall: Mapped[float] = mapped_column(Float)
    sunlight: Mapped[float] = mapped_column(Float)
    wind_speed: Mapped[float] = mapped_column(Float)

    nitrogen: Mapped[float] = mapped_column(Float, default=0.0)
    phosphorus: Mapped[float] = mapped_column(Float, default=0.0)
    potassium: Mapped[float] = mapped_column(Float, default=0.0)
    rain_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    status: Mapped[str] = mapped_column(String(16), default="LIVE")


class RobotAction(Base):
    __tablename__ = "robot_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(48), nullable=False)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(16), default="auto")  # auto | manual
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class CameraSnapshot(Base):
    __tablename__ = "camera_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    image_data_url: Mapped[str] = mapped_column(Text)
    pan_deg: Mapped[int] = mapped_column(Integer, default=0)
    tilt_deg: Mapped[int] = mapped_column(Integer, default=0)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="info")  # info | warning | critical
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class IrrigationPrediction(Base):
    __tablename__ = "irrigation_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    prediction: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    probabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    mapped_features: Mapped[dict] = mapped_column(JSON, default=dict)
    indicators: Mapped[dict] = mapped_column(JSON, default=dict)


class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    top_crop: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    alternatives: Mapped[dict] = mapped_column(JSON, default=dict)
    input_features: Mapped[dict] = mapped_column(JSON, default=dict)


class FertilizerRecommendation(Base):
    __tablename__ = "fertilizer_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    crop: Mapped[str] = mapped_column(String(32))
    recommended_fertilizer: Mapped[str] = mapped_column(String(32))
    model_probability: Mapped[float] = mapped_column(Float)
    nutrient_status: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text)
    input_features: Mapped[dict] = mapped_column(JSON, default=dict)
    warnings: Mapped[dict] = mapped_column(JSON, default=list)


class SoilHealthRecord(Base):
    __tablename__ = "soil_health_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    overall_status: Mapped[str] = mapped_column(String(24))
    health_score: Mapped[int] = mapped_column(Integer)
    factors: Mapped[dict] = mapped_column(JSON, default=dict)
    stress_factors: Mapped[dict] = mapped_column(JSON, default=list)
    primary_issue: Mapped[str | None] = mapped_column(String(32), nullable=True)
    recommendation: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)


class YieldPrediction(Base):
    __tablename__ = "yield_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
    crop: Mapped[str] = mapped_column(String(64))
    state: Mapped[str] = mapped_column(String(64))
    season: Mapped[str] = mapped_column(String(32))
    year: Mapped[int] = mapped_column(Integer)
    area_hectare: Mapped[float] = mapped_column(Float)
    predicted_yield: Mapped[float] = mapped_column(Float)
    estimated_total_production: Mapped[float] = mapped_column(Float)
    fertilizer_per_ha: Mapped[float] = mapped_column(Float)
    pesticide_per_ha: Mapped[float] = mapped_column(Float)
    warnings: Mapped[dict] = mapped_column(JSON, default=list)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    farm_id: Mapped[int] = mapped_column(ForeignKey("farms.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    content: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), default="en")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
