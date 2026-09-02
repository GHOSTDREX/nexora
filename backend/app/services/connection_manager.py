"""
AgriNova — WebSocket connection registry.

Keyed by farm_id so live updates for one farm are never broadcast to another
user's connections, while still supporting many simultaneous clients per farm
(e.g. the same farmer open on two devices) and many farms at once.
"""

import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, farm_id: int, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self._connections.setdefault(farm_id, set()).add(websocket)

    async def disconnect(self, farm_id: int, websocket: WebSocket):
        async with self._lock:
            conns = self._connections.get(farm_id)
            if conns and websocket in conns:
                conns.remove(websocket)
                if not conns:
                    del self._connections[farm_id]

    async def broadcast(self, farm_id: int, message: dict):
        conns = list(self._connections.get(farm_id, []))
        stale = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        if stale:
            async with self._lock:
                for ws in stale:
                    self._connections.get(farm_id, set()).discard(ws)


manager = ConnectionManager()


def build_sensor_update_message(reading, pump_on: bool, robot_connected: bool, alerts=None) -> dict:
    """Shape a `sensor_update` WebSocket message from a SensorReading row —
    shared by the simulator tick and the manual-reading endpoint so the two
    can never drift apart in what fields they send the dashboard."""
    return {
        "type": "sensor_update",
        "reading": {
            "soil_moisture": reading.soil_moisture,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "rainfall": reading.rainfall,
            "sunlight": reading.sunlight,
            "wind_speed": reading.wind_speed,
            "nitrogen": reading.nitrogen,
            "phosphorus": reading.phosphorus,
            "potassium": reading.potassium,
            "rain_detected": reading.rain_detected,
            "timestamp": reading.timestamp.isoformat(),
        },
        "robot": {
            "pump_on": pump_on,
            "robot_connected": robot_connected,
        },
        "alerts": [
            {"code": a.code, "severity": a.severity, "params": a.params}
            for a in (alerts or [])
        ],
    }
