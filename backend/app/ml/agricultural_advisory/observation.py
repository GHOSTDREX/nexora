"""Normalizes raw AI-service outputs into the canonical Observation schema.

This is the only module that knows about the shape of pest_detection's
DetectionResult JSON (or a future disease-detector result). Everything
downstream (risk engine, rule engine, advisory service) only ever sees
Observation objects, so a new perception source can be added by writing one
new normalizer here — nothing else in the advisory engine has to change.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from app.ml.agricultural_advisory.config import settings
from app.ml.agricultural_advisory.data_quality import classify_detection_confidence
from app.ml.agricultural_advisory.schemas import DataQuality, Observation

# The pest detector's own confidence threshold (source of truth: pest_detection.config).
# Imported lazily to avoid a hard import-time dependency in environments that
# only run the advisory engine's unit tests without ultralytics installed.


def _pest_detector_confidence_threshold() -> float:
    try:
        from pest_detection.config import settings as pest_settings

        return pest_settings.confidence_threshold
    except Exception:  # noqa: BLE001 - fall back if pest_detection isn't importable
        return 0.25


def pest_detection_result_to_observations(
    result: dict[str, Any], timestamp: Optional[str] = None
) -> list[Observation]:
    """Convert a pest_detection DetectionResult.to_dict() payload into one
    Observation per detected species (using the already-grouped `species` list,
    never re-deriving counts from raw detections — the detector's grouping is
    authoritative).
    """
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    threshold = _pest_detector_confidence_threshold()

    species = result.get("species") or []
    observations = []
    for entry in species:
        confidence = entry.get("average_confidence")
        quality = classify_detection_confidence(confidence, threshold)
        observations.append(
            Observation(
                source="pest_detector",
                type="pest",
                name=entry.get("name"),
                confidence=confidence,
                count=entry.get("count"),
                quality=quality,
                timestamp=timestamp,
                raw=entry,
            )
        )
    return observations


def image_quality_observation(
    result: dict[str, Any], timestamp: Optional[str] = None
) -> Optional[Observation]:
    """Extracts an image-quality signal from a pest_detection result, if any."""
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    status = result.get("status")
    if status == "image_quality_warning":
        return Observation(
            source="pest_detector",
            type="image_quality",
            name="quality_warning",
            quality=DataQuality.INVALID,
            timestamp=timestamp,
            raw={"message": result.get("message")},
        )
    if status == "invalid_image":
        return Observation(
            source="pest_detector",
            type="image_quality",
            name="invalid_image",
            quality=DataQuality.INVALID,
            timestamp=timestamp,
            raw={"message": result.get("message")},
        )
    return Observation(
        source="pest_detector",
        type="image_quality",
        name="acceptable",
        quality=DataQuality.VALID,
        timestamp=timestamp,
    )


def disease_result_to_observation(
    result: Optional[dict[str, Any]], timestamp: Optional[str] = None
) -> Optional[Observation]:
    """Normalizes a disease-detector result into an Observation.

    This is an interface, not a live integration: no disease model currently
    ships in this repository (see docs/AGRICULTURAL_ADVISORY.md,
    "Disease detection status"). It accepts the same shape the eventual
    MobileNetV3 disease service is specified to produce
    (`{"name": ..., "confidence": ..., "quality": "valid"}`), so the risk and
    safety-gate logic can be built, tested, and exercised today without a
    real model behind it, and swapped in later with no changes to this
    function's callers.
    """
    if not result:
        return None
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()
    confidence = result.get("confidence")
    quality = classify_detection_confidence(confidence, settings.disease_confidence_threshold)
    return Observation(
        source="disease_detector",
        type="disease",
        name=result.get("name"),
        confidence=confidence,
        quality=quality,
        timestamp=timestamp,
        raw=result,
    )


def sensor_reading_to_observation(
    key: str, value: Optional[float], unit: str, quality: DataQuality, timestamp: Optional[str] = None
) -> Observation:
    return Observation(
        source="sensor",
        type="sensor",
        name=key,
        value=value,
        unit=unit,
        quality=quality,
        timestamp=timestamp,
    )


def weather_reading_to_observation(
    key: str, value: Optional[float], unit: str, quality: DataQuality, timestamp: Optional[str] = None
) -> Observation:
    return Observation(
        source="weather",
        type="weather",
        name=key,
        value=value,
        unit=unit,
        quality=quality,
        timestamp=timestamp,
    )
