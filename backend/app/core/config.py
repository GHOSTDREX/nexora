"""
AgriNova Backend — System Configuration & Constants
"""

import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent

# --- Security / Auth ---
_DEFAULT_JWT_SECRET = "agrinova-dev-secret-change-me"
JWT_SECRET = os.getenv("JWT_SECRET", _DEFAULT_JWT_SECRET)
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

if JWT_SECRET == _DEFAULT_JWT_SECRET:
    logging.getLogger("agrinova.security").warning(
        "JWT_SECRET is not set — using the publicly-known default from "
        ".env.example. Anyone who knows this default can forge a valid "
        "login token for any user. Set a real JWT_SECRET before deploying "
        "anywhere reachable outside your own machine."
    )

# --- LLM ---
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

# --- Database ---
DB_PATH = os.getenv("DB_PATH", str(BACKEND_DIR / "data" / "agrinova.db"))
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- CORS ---
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:5174,http://127.0.0.1:5174,"
    "http://localhost:5175,http://127.0.0.1:5175",
).split(",")

# --- Simulator ---
SIMULATOR_TICK_SECONDS = float(os.getenv("SIMULATOR_TICK_SECONDS", "4"))

# --- Sensor staleness ---
STALE_SENSOR_THRESHOLD_MINUTES = 15

# --- Irrigation ML model — 16 trained features (exact ordering) ---
MODEL_FEATURES = [
    "Soil_Type",
    "Soil_pH",
    "Soil_Moisture",
    "Organic_Carbon",
    "Electrical_Conductivity",
    "Temperature_C",
    "Humidity",
    "Rainfall_mm",
    "Sunlight_Hours",
    "Wind_Speed_kmh",
    "Crop_Type",
    "Crop_Growth_Stage",
    "Season",
    "Field_Area_hectare",
    "Mulching_Used",
    "Region",
]

CATEGORICAL_CHOICES = {
    "Soil_Type": ["Clay", "Loamy", "Sandy", "Silt"],
    "Crop_Type": ["Wheat", "Maize", "Cotton", "Rice", "Sugarcane", "Potato"],
    "Crop_Growth_Stage": ["Sowing", "Vegetative", "Flowering", "Harvest"],
    "Season": ["Kharif", "Rabi", "Zaid"],
    "Mulching_Used": ["Yes", "No"],
    "Region": ["North", "South", "East", "West", "Central"],
}

SENSOR_RANGES = {
    "soil_moisture": (0.0, 100.0),
    "temperature": (-10.0, 60.0),
    "humidity": (0.0, 100.0),
    "rainfall": (0.0, 5000.0),
    "sunlight": (0.0, 100000.0),
    "wind_speed": (0.0, 150.0),
}

FARM_CONFIG_RANGES = {
    "soil_ph": (3.5, 10.5),
    "organic_carbon": (0.0, 10.0),
    "electrical_conductivity": (0.0, 20.0),
    "field_area_hectare": (0.01, 1000.0),
}

# --- Supported UI languages ---
SUPPORTED_LANGUAGES = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "gu": "Gujarati",
    "ta": "Tamil",
    "te": "Telugu",
    "kn": "Kannada",
    "bn": "Bengali",
    "pa": "Punjabi",
    "ml": "Malayalam",
}
RULE_BASED_LANGUAGES = ["en", "hi", "mr"]
