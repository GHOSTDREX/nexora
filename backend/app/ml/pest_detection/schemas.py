"""Canonical application-level result schema.

Every entry point (CLI, API) returns data shaped by these dataclasses via
`.to_dict()`, so the JSON contract stays identical everywhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ResultStatus(str, Enum):
    DETECTIONS_FOUND = "detections_found"
    NO_PEST_DETECTED = "no_pest_detected"
    INVALID_IMAGE = "invalid_image"
    IMAGE_QUALITY_WARNING = "image_quality_warning"
    INFERENCE_ERROR = "inference_error"


class SeverityLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    NONE = "NONE"


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float

    @property
    def width(self) -> float:
        return max(0.0, self.x2 - self.x1)

    @property
    def height(self) -> float:
        return max(0.0, self.y2 - self.y1)

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def center_x(self) -> float:
        return self.x1 + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y1 + self.height / 2

    def to_dict(self) -> dict:
        return {
            "x1": round(self.x1, 2),
            "y1": round(self.y1, 2),
            "x2": round(self.x2, 2),
            "y2": round(self.y2, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "area": round(self.area, 2),
            "center_x": round(self.center_x, 2),
            "center_y": round(self.center_y, 2),
        }


@dataclass
class Detection:
    class_id: int
    name: str
    confidence: float
    bbox: BoundingBox

    def to_dict(self) -> dict:
        return {
            "class_id": self.class_id,
            "name": self.name,
            "confidence": round(self.confidence, 4),
            "bbox": self.bbox.to_dict(),
        }


@dataclass
class SpeciesSummary:
    name: str
    count: int
    average_confidence: float
    max_confidence: float
    min_confidence: float

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "average_confidence": round(self.average_confidence, 4),
            "max_confidence": round(self.max_confidence, 4),
            "min_confidence": round(self.min_confidence, 4),
        }


@dataclass
class SeverityResult:
    level: SeverityLevel
    score: float
    type: str = "image_level_indicator"
    note: str = (
        "Heuristic derived from this single image only. Not a validated "
        "field-wide infestation measurement."
    )

    def to_dict(self) -> dict:
        return {
            "level": self.level.value,
            "score": round(self.score, 4),
            "type": self.type,
            "note": self.note,
        }


@dataclass
class ImageInfo:
    filename: str
    width: int
    height: int

    def to_dict(self) -> dict:
        return {"filename": self.filename, "width": self.width, "height": self.height}


@dataclass
class TimingInfo:
    preprocessing_ms: float = 0.0
    inference_ms: float = 0.0
    postprocessing_ms: float = 0.0
    total_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "preprocessing_ms": round(self.preprocessing_ms, 2),
            "inference_ms": round(self.inference_ms, 2),
            "postprocessing_ms": round(self.postprocessing_ms, 2),
            "total_ms": round(self.total_ms, 2),
        }


@dataclass
class DetectionResult:
    status: ResultStatus
    image: ImageInfo | None = None
    detections: list[Detection] = field(default_factory=list)
    species: list[SpeciesSummary] = field(default_factory=list)
    severity: SeverityResult | None = None
    timing: TimingInfo | None = None
    message: str | None = None

    @property
    def total_pests(self) -> int:
        return len(self.detections)

    @property
    def species_count(self) -> int:
        return len(self.species)

    @property
    def highest_confidence(self) -> float | None:
        if not self.detections:
            return None
        return max(d.confidence for d in self.detections)

    def to_dict(self) -> dict:
        confidences = [d.confidence for d in self.detections]
        result = {
            "status": self.status.value,
            "image": self.image.to_dict() if self.image else None,
            "detections": [d.to_dict() for d in self.detections],
            "summary": {
                "total_pests": self.total_pests,
                "species_count": self.species_count,
                "highest_confidence": round(max(confidences), 4) if confidences else None,
                "average_confidence": (
                    round(sum(confidences) / len(confidences), 4) if confidences else None
                ),
                "minimum_confidence": round(min(confidences), 4) if confidences else None,
            },
            "species": [s.to_dict() for s in self.species],
            "severity": self.severity.to_dict() if self.severity else None,
        }
        if self.timing:
            result["timing"] = self.timing.to_dict()
        if self.message:
            result["message"] = self.message
        return result
