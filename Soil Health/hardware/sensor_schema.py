from typing import Any

from src.validation import validate_reading


def normalize_sensor_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = validate_reading(payload)
    if not result["valid"]:
        raise ValueError("Invalid ESP32 payload: " + " ".join(result["errors"]))
    return result["values"]
