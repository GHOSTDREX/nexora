"""Authoritative, notebook-aligned Soil Health rule definitions."""

RULE_VERSION = "jupyter-prototype-boundaries"
RULE_SOURCE = "Soil Health Jupyter validation analysis"
DISCLAIMER = (
    "Prototype dataset-derived rules for Nitrogen, Phosphorus, Potassium, Soil Moisture and Soil pH; "
    "Temperature and Humidity use general heuristic ranges, not notebook-validated boundaries. "
    "Not universal agronomic recommendations. Field validation is required."
)

# Boundary semantics are intentional: values exactly at nutrient/moisture thresholds
# are healthy; pH is healthy inclusively from 6.10 through 7.00.
# Temperature/Humidity ranges are a general-purpose heuristic (typical safe field-crop
# comfort zone), not derived from the validation notebook like the other five.
RULES = {
    "nitrogen": {"healthy_min": 30.0},
    "phosphorus": {"healthy_min": 25.0},
    "potassium": {"healthy_min": 25.0},
    "soil_moisture": {"healthy_min": 25.0},
    "soil_ph": {"healthy_min": 6.10, "healthy_max": 7.00},
    "temperature": {"healthy_min": 15.0, "healthy_max": 35.0},
    "humidity": {"healthy_min": 30.0, "healthy_max": 85.0},
}

SENSOR_BOUNDS = {
    "nitrogen": (0.0, 1000.0),
    "phosphorus": (0.0, 1000.0),
    "potassium": (0.0, 1000.0),
    "soil_moisture": (0.0, 100.0),
    "humidity": (0.0, 100.0),
    "temperature": (-50.0, 70.0),
    "soil_ph": (0.0, 14.0),
}
REQUIRED_FIELDS = ("nitrogen", "phosphorus", "potassium", "soil_moisture", "humidity", "temperature")
