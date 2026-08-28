"""Input validation shared by every Soil Health input mode."""

from __future__ import annotations

import math
from typing import Any

from .config import REQUIRED_FIELDS, SENSOR_BOUNDS


def validate_reading(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"valid": False, "errors": ["Input must be an object."], "values": {}}
    errors: list[str] = []
    values: dict[str, Any] = {}
    for field in REQUIRED_FIELDS:
        if field not in payload or payload[field] is None:
            errors.append(f"Missing required field: {field}.")
            continue
        value = payload[field]
        if isinstance(value, bool):
            errors.append(f"{field} must be numeric, not boolean.")
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric.")
            continue
        minimum, maximum = SENSOR_BOUNDS[field]
        if not math.isfinite(number) or not minimum <= number <= maximum:
            errors.append(f"{field} must be finite and within {minimum:g} to {maximum:g}.")
            continue
        values[field] = number
    if payload.get("soil_ph") is not None:
        value = payload["soil_ph"]
        try:
            number = float(value)
            minimum, maximum = SENSOR_BOUNDS["soil_ph"]
            if not math.isfinite(number) or not minimum <= number <= maximum:
                raise ValueError
            values["soil_ph"] = number
        except (TypeError, ValueError):
            errors.append("soil_ph must be finite and within 0 to 14.")
    if "rain_detected" in payload:
        if not isinstance(payload["rain_detected"], bool):
            errors.append("rain_detected must be boolean.")
        else:
            values["rain_detected"] = payload["rain_detected"]
    return {"valid": not errors, "errors": errors, "values": values}
