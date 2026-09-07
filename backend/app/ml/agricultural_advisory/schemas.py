"""Canonical schemas for the Agricultural Advisory Engine.

These types are the contract between every layer described in
docs/AGRICULTURAL_ADVISORY.md: Observation Layer -> Context Engine -> Risk
Engine -> Advisory Engine -> API/Frontend. Nothing downstream of the
Observation Layer should depend on where an observation came from (YOLO
pest detector, a future disease classifier, a sensor, or a weather feed).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Data quality: the engine must always be able to say "I don't know" instead
# of silently substituting a default value for missing data.
# ---------------------------------------------------------------------------


class DataQuality(str, Enum):
    VALID = "VALID"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    STALE = "STALE"
    MISSING = "MISSING"
    INVALID = "INVALID"
    OUT_OF_RANGE = "OUT_OF_RANGE"
    UNKNOWN = "UNKNOWN"


class TrendDirection(str, Enum):
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class RiskLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"


class RiskCategory(str, Enum):
    PEST_PRESSURE = "PEST_PRESSURE"
    DISEASE_RISK = "DISEASE_RISK"
    WATER_STRESS = "WATER_STRESS"
    DROUGHT = "DROUGHT"
    HEAT_STRESS = "HEAT_STRESS"
    FLOOD_RISK = "FLOOD_RISK"
    EXCESS_RAIN = "EXCESS_RAIN"


class Priority(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    URGENT = "URGENT"


class RecommendationType(str, Enum):
    IMMEDIATE_ACTION = "IMMEDIATE_ACTION"
    MONITOR = "MONITOR"
    PREVENTIVE_ACTION = "PREVENTIVE_ACTION"
    CULTURAL_CONTROL = "CULTURAL_CONTROL"
    PHYSICAL_CONTROL = "PHYSICAL_CONTROL"
    BIOLOGICAL_CONTROL = "BIOLOGICAL_CONTROL"
    IRRIGATION_ACTION = "IRRIGATION_ACTION"
    RECHECK = "RECHECK"
    ESCALATE = "ESCALATE"
    INFORMATION = "INFORMATION"


class AdvisoryStatus(str, Enum):
    ADVISORY_AVAILABLE = "advisory_available"
    NO_PEST_OR_DISEASE_DETECTED = "no_pest_or_disease_detected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    FURTHER_OBSERVATION_REQUIRED = "further_observation_required"
    KNOWLEDGE_GAP = "knowledge_gap"
    UNSUPPORTED = "unsupported"


# ---------------------------------------------------------------------------
# Observation layer
# ---------------------------------------------------------------------------


@dataclass
class Observation:
    """A single normalized fact, regardless of where it came from."""

    source: str  # e.g. "pest_detector", "disease_detector", "sensor", "weather", "farmer"
    type: str  # "pest" | "disease" | "image_quality" | "sensor" | "weather"
    quality: DataQuality
    name: Optional[str] = None
    confidence: Optional[float] = None
    count: Optional[int] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    timestamp: Optional[str] = None
    raw: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "type": self.type,
            "quality": self.quality.value,
            "name": self.name,
            "confidence": self.confidence,
            "count": self.count,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
        }


@dataclass
class TrendResult:
    direction: TrendDirection
    first_detected: Optional[str] = None
    last_detected: Optional[str] = None
    observation_count: int = 0
    previous_count: Optional[int] = None
    current_count: Optional[int] = None
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "direction": self.direction.value,
            "first_detected": self.first_detected,
            "last_detected": self.last_detected,
            "observation_count": self.observation_count,
            "previous_count": self.previous_count,
            "current_count": self.current_count,
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Farm context
# ---------------------------------------------------------------------------


@dataclass
class FarmContext:
    """Everything the advisory engine is allowed to reason about for one request.

    Every field is optional except observation_timestamp. Missing data stays
    missing (None / empty) rather than being defaulted to a "normal" value —
    see agricultural_advisory/data_quality.py.
    """

    observation_timestamp: str
    farm_id: Optional[str] = None
    field_id: Optional[str] = None
    crop: Optional[str] = None
    crop_variety: Optional[str] = None
    growth_stage: Optional[str] = None
    location: Optional[dict] = None

    sensor_data: dict[str, Observation] = field(default_factory=dict)
    weather_data: dict[str, Observation] = field(default_factory=dict)
    pest_observations: list[Observation] = field(default_factory=list)
    disease_observation: Optional[Observation] = None
    image_quality: Optional[Observation] = None

    historical_observations: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "farm_id": self.farm_id,
            "field_id": self.field_id,
            "crop": self.crop,
            "crop_variety": self.crop_variety,
            "growth_stage": self.growth_stage,
            "observation_timestamp": self.observation_timestamp,
            "location": self.location,
            "sensor_data": {k: v.to_dict() for k, v in self.sensor_data.items()},
            "weather_data": {k: v.to_dict() for k, v in self.weather_data.items()},
            "pest_observations": [o.to_dict() for o in self.pest_observations],
            "disease_observation": (
                self.disease_observation.to_dict() if self.disease_observation else None
            ),
            "image_quality": self.image_quality.to_dict() if self.image_quality else None,
        }


# ---------------------------------------------------------------------------
# Risk
# ---------------------------------------------------------------------------


@dataclass
class RiskAssessment:
    category: RiskCategory
    level: RiskLevel
    scope: str  # e.g. "image_only", "image_and_field_observation", "farm_sensor_data"
    evidence_confidence: str  # "low" | "moderate" | "high" — strength of evidence, NOT model confidence
    score: float
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "level": self.level.value,
            "scope": self.scope,
            "confidence": self.evidence_confidence,
            "score": round(self.score, 4),
            "note": self.note,
        }


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


@dataclass
class SourceRef:
    id: str
    organization: str
    title: str
    url: str
    reference_type: str = "extension_publication"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization": self.organization,
            "title": self.title,
            "url": self.url,
            "reference_type": self.reference_type,
        }


@dataclass
class Recommendation:
    rule_id: str
    priority: Priority
    type: RecommendationType
    action: str
    evidence: dict
    source_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "priority": self.priority.value,
            "type": self.type.value,
            "action": self.action,
            "evidence": self.evidence,
            "source_ids": self.source_ids,
        }


@dataclass
class AuditRecord:
    timestamp: str
    farm_id: Optional[str]
    field_id: Optional[str]
    observation_id: str
    inputs_summary: dict
    risk_assessments: list[dict]
    rules_triggered: list[str]
    recommendation_count: int
    advisory_engine_version: str
    knowledge_base_version: str
    rule_set_version: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "farm_id": self.farm_id,
            "field_id": self.field_id,
            "observation_id": self.observation_id,
            "inputs_summary": self.inputs_summary,
            "risk_assessments": self.risk_assessments,
            "rules_triggered": self.rules_triggered,
            "recommendation_count": self.recommendation_count,
            "versions": {
                "advisory_engine": self.advisory_engine_version,
                "knowledge_base": self.knowledge_base_version,
                "rule_set": self.rule_set_version,
            },
        }


@dataclass
class AdvisoryResult:
    status: AdvisoryStatus
    risk_assessments: list[RiskAssessment] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    explanations: list[str] = field(default_factory=list)
    sources: list[SourceRef] = field(default_factory=list)
    audit: Optional[AuditRecord] = None
    message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "risk_assessments": [r.to_dict() for r in self.risk_assessments],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "explanations": self.explanations,
            "sources": [s.to_dict() for s in self.sources],
            "audit": self.audit.to_dict() if self.audit else None,
            "message": self.message,
        }
