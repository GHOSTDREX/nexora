import os
from typing import Any

import requests

from .sensor_schema import normalize_sensor_payload


class ESP32Client:
    def __init__(self, endpoint: str | None = None, timeout: float = 5.0) -> None:
        self.endpoint = endpoint or os.getenv("SOIL_HEALTH_SENSOR_ENDPOINT", "")
        self.timeout = timeout

    def read(self) -> dict[str, Any]:
        if not self.endpoint:
            raise ConnectionError("SOIL_HEALTH_SENSOR_ENDPOINT is not configured.")
        try:
            response = requests.get(self.endpoint, timeout=self.timeout)
            response.raise_for_status()
            return normalize_sensor_payload(response.json())
        except requests.RequestException as exc:
            raise ConnectionError("Unable to connect to ESP32 sensor endpoint.") from exc
