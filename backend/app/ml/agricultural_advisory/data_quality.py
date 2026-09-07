"""Data-quality classification.

Rule zero of this module: missing data is never treated as a value. A
missing rainfall reading is not "no rain"; a missing temperature reading is
not "normal temperature." Every classifier here returns an explicit
DataQuality alongside the value (or None), and callers must branch on it.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from app.ml.agricultural_advisory.config import settings
from app.ml.agricultural_advisory.schemas import DataQuality


def _parse_timestamp(timestamp: Optional[str]) -> Optional[datetime]:
    if not timestamp:
        return None
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def classify_reading(
    value: Optional[float],
    *,
    sensor_key: Optional[str] = None,
    timestamp: Optional[str] = None,
    max_age_seconds: Optional[int] = None,
) -> DataQuality:
    """Classify a single scalar sensor/weather reading.

    Order of checks: MISSING -> INVALID -> STALE -> OUT_OF_RANGE -> VALID.
    """
    if value is None:
        return DataQuality.MISSING

    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return DataQuality.INVALID

    if timestamp is not None and max_age_seconds is not None:
        parsed = _parse_timestamp(timestamp)
        if parsed is None:
            return DataQuality.INVALID
        age = (datetime.now(timezone.utc) - parsed).total_seconds()
        if age > max_age_seconds:
            return DataQuality.STALE

    if sensor_key and sensor_key in settings.sensor_ranges:
        bounds = settings.sensor_ranges[sensor_key]
        if numeric_value < bounds.minimum or numeric_value > bounds.maximum:
            return DataQuality.OUT_OF_RANGE

    return DataQuality.VALID


def classify_detection_confidence(
    confidence: Optional[float], required_threshold: float
) -> DataQuality:
    """Classify an AI detection's confidence against the model's own acceptance threshold.

    This never invents a new threshold — `required_threshold` must come from
    the producing model's own configuration (e.g. the pest detector's
    PEST_CONFIDENCE_THRESHOLD, or the disease model's production threshold).
    """
    if confidence is None:
        return DataQuality.MISSING
    if confidence < required_threshold:
        return DataQuality.LOW_CONFIDENCE
    return DataQuality.VALID
