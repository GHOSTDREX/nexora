"""
SMART AGRICULTURE AI
Sensor Validator & Staleness Detection Service
"""

import math
from datetime import datetime, timezone
from app.core.config import SENSOR_RANGES, STALE_SENSOR_THRESHOLD_MINUTES


class SensorValidator:
    @staticmethod
    def validate_reading(data_dict):
        """Validates ESP32 incoming sensor payload."""
        errors = []

        required_fields = ["soil_moisture", "temperature", "humidity", "rainfall", "sunlight", "wind_speed"]
        for field in required_fields:
            if field not in data_dict or data_dict[field] is None:
                errors.append(f"Missing required sensor field: '{field}'")
                continue

            val = data_dict[field]
            try:
                val_float = float(val)
                if math.isnan(val_float) or math.isinf(val_float):
                    errors.append(f"Field '{field}' contains invalid NaN or Infinite value.")
                    continue

                min_val, max_val = SENSOR_RANGES.get(field, (0.0, 100000.0))
                if val_float < min_val or val_float > max_val:
                    errors.append(f"Field '{field}' value {val_float} out of range [{min_val}, {max_val}].")

            except (ValueError, TypeError):
                errors.append(f"Field '{field}' must be a valid numeric number.")

        is_valid = len(errors) == 0
        return is_valid, errors

    @staticmethod
    def check_staleness(timestamp_str, threshold_minutes=STALE_SENSOR_THRESHOLD_MINUTES):
        """Checks if a sensor timestamp is older than threshold minutes."""
        if not timestamp_str:
            return True, "No timestamp provided"

        try:
            # Parse ISO timestamp
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            ts_dt = datetime.fromisoformat(timestamp_str)
            if ts_dt.tzinfo is None:
                ts_dt = ts_dt.replace(tzinfo=timezone.utc)

            now_dt = datetime.now(timezone.utc)
            delta_minutes = (now_dt - ts_dt).total_seconds() / 60.0

            if delta_minutes > threshold_minutes:
                return True, f"Sensor reading is stale ({int(delta_minutes)} minutes old, threshold {threshold_minutes} min)."
            return False, "Live"
        except Exception as e:
            return True, f"Invalid timestamp format: {str(e)}"
