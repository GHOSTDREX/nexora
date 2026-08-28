"""
SMART AGRICULTURE AI
System Configuration & Constants
"""

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# File Paths
MODEL_PATH = os.path.join(BASE_DIR, "models", "irrigation_prediction_model.pkl")
DB_PATH = os.path.join(BASE_DIR, "database", "irrigation.db")
LOG_PATH = os.path.join(BASE_DIR, "logs", "app.log")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 8000
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# Sensor Staleness Threshold (in Minutes)
STALE_SENSOR_THRESHOLD_MINUTES = 15

# 16 Trained ML Model Features (Exact Ordering)
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
    "Region"
]

# Allowed Categorical Choices in Model Training
CATEGORICAL_CHOICES = {
    "Soil_Type": ["Clay", "Loamy", "Sandy", "Silt"],
    "Crop_Type": ["Wheat", "Maize", "Cotton", "Rice", "Sugarcane", "Potato"],
    "Crop_Growth_Stage": ["Sowing", "Vegetative", "Flowering", "Harvest"],
    "Season": ["Kharif", "Rabi", "Zaid"],
    "Mulching_Used": ["Yes", "No"],
    "Region": ["North", "South", "East", "West", "Central"]
}

# Physical & Sensor Range Limits
SENSOR_RANGES = {
    "soil_moisture": (0.0, 100.0),
    "temperature": (-10.0, 60.0),
    "humidity": (0.0, 100.0),
    "rainfall": (0.0, 5000.0),
    "sunlight": (0.0, 100000.0),  # Raw Sensor units (e.g. lux or W/m2)
    "wind_speed": (0.0, 150.0)
}

FARM_CONFIG_RANGES = {
    "soil_ph": (3.5, 10.5),
    "organic_carbon": (0.0, 10.0),
    "electrical_conductivity": (0.0, 20.0),
    "field_area_hectare": (0.01, 1000.0)
}
