import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Farm
from app.deps import get_current_farm

router = APIRouter(prefix="/api/weather", tags=["weather"])

_CACHE: dict[str, tuple[float, dict]] = {}
CACHE_TTL_SECONDS = 600

WEATHER_CODE_LABEL = {
    0: "clear_sky", 1: "mainly_clear", 2: "partly_cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light_drizzle", 53: "drizzle", 55: "heavy_drizzle",
    61: "light_rain", 63: "rain", 65: "heavy_rain", 71: "light_snow", 73: "snow",
    75: "heavy_snow", 80: "rain_showers", 81: "rain_showers", 82: "violent_showers",
    95: "thunderstorm", 96: "thunderstorm_hail", 99: "thunderstorm_hail",
}


@router.get("/today")
def get_today_weather(farm: Farm = Depends(get_current_farm)):
    cache_key = f"{round(farm.latitude, 2)},{round(farm.longitude, 2)}"
    cached = _CACHE.get(cache_key)
    if cached and (time.time() - cached[0]) < CACHE_TTL_SECONDS:
        return cached[1]

    params = {
        "latitude": farm.latitude,
        "longitude": farm.longitude,
        "current": "temperature_2m,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code",
        "timezone": "auto",
    }
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get("https://api.open-meteo.com/v1/forecast", params=params)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Weather service unavailable: {exc}")

    current = data.get("current", {})
    code = current.get("weather_code", 0)
    result = {
        "temperature_c": current.get("temperature_2m"),
        "humidity_pct": current.get("relative_humidity_2m"),
        "rain_probability_pct": current.get("precipitation_probability"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
        "condition": WEATHER_CODE_LABEL.get(code, "unknown"),
    }
    _CACHE[cache_key] = (time.time(), result)
    return result
