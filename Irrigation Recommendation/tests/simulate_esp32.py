"""
SMART AGRICULTURE AI
ESP32 Hardware Telemetry Simulator

Simulates an ESP32 micro-controller posting live field sensor measurements
to the FastAPI backend REST endpoint (POST /api/v1/sensors/readings).
"""

import time
import json
import urllib.request
from datetime import datetime, timezone

API_ENDPOINT = "http://127.0.0.1:8000/api/v1/sensors/readings"


def send_esp32_reading(farm_id="FARM_001", device_id="ESP32_FIELD_01", moisture=24.5, temp=31.2, humidity=55.0, rainfall=0.0, sunlight=850.0, wind=11.5):
    payload = {
        "farm_id": farm_id,
        "device_id": device_id,
        "soil_moisture": float(moisture),
        "temperature": float(temp),
        "humidity": float(humidity),
        "rainfall": float(rainfall),
        "sunlight": float(sunlight),
        "wind_speed": float(wind),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    try:
        req = urllib.request.Request(
            API_ENDPOINT,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        response = urllib.request.urlopen(req, timeout=5)
        res_data = json.loads(response.read().decode("utf-8"))
        print(f"[ESP32 SIMULATOR] Successfully sent packet -> Status: {response.status} | Response: {res_data}")
        return True
    except Exception as e:
        print(f"[ESP32 SIMULATOR] Transmission error: {str(e)}")
        return False


if __name__ == "__main__":
    print("=======================================================")
    print("[+] ESP32 Live Telemetry Simulator Active")

    print("=======================================================\n")
    
    # Send a sequence of simulated readings
    readings = [
        (28.5, 29.0, 60.0, 0.0, 750.0, 9.5),
        (26.0, 30.5, 57.0, 0.0, 800.0, 10.2),
        (24.5, 32.0, 52.0, 0.0, 880.0, 11.5),
        (21.0, 34.5, 48.0, 0.0, 920.0, 13.0)
    ]

    for sm, temp, hum, rf, sun, ws in readings:
        send_esp32_reading(moisture=sm, temp=temp, humidity=hum, rainfall=rf, sunlight=sun, wind=ws)
        time.sleep(1)
