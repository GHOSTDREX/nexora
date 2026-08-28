"""Validation and dataset-derived prototype interpretation bands."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd

SUPPORTED_CROPS = ("Rice", "Sugarcane")
SUPPORTED_SOILS = ("Clay", "Loamy", "Sandy", "Silt")
SUPPORTED_STAGES = ("Sowing", "Vegetative", "Flowering", "Harvest")
FEATURE_COLUMNS = ["Crop_Type", "Soil_Type", "Soil_pH", "Nitrogen_Level", "Phosphorus_Level", "Potassium_Level", "Electrical_Conductivity", "Crop_Growth_Stage"]
NUMERIC_FIELDS = {"soil_ph": "Soil_pH", "nitrogen_level": "Nitrogen_Level", "phosphorus_level": "Phosphorus_Level", "potassium_level": "Potassium_Level", "electrical_conductivity": "Electrical_Conductivity"}


def _training_ranges() -> dict[str, tuple[float, float]]:
    path = Path(__file__).resolve().parents[1] / "data" / "fertilizer_recommendation.csv"
    subset = pd.read_csv(path)
    subset = subset[subset["Crop_Type"].isin(SUPPORTED_CROPS)]
    return {field: (float(subset[column].min()), float(subset[column].max())) for field, column in NUMERIC_FIELDS.items()}


TRAINING_RANGES = _training_ranges()


def nutrient_status(nitrogen: float, phosphorus: float, potassium: float, soil_ph: float) -> dict[str, str]:
    return {"nitrogen": "Low" if nitrogen < 60 else "Moderate" if nitrogen < 100 else "High", "phosphorus": "Low" if phosphorus < 40 else "Moderate" if phosphorus < 65 else "High", "potassium": "Low" if potassium < 40 else "Moderate" if potassium < 70 else "High", "soil_ph": "Acidic" if soil_ph < 5.5 else "Alkaline" if soil_ph > 7.5 else "Suitable Range"}


def validate_inputs(values: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized = dict(values)
    if values.get("crop_type") not in SUPPORTED_CROPS:
        errors.append("Crop must be Rice or Sugarcane.")
    if values.get("soil_type") not in SUPPORTED_SOILS:
        errors.append(f"Soil type must be one of: {', '.join(SUPPORTED_SOILS)}.")
    if values.get("crop_growth_stage") not in SUPPORTED_STAGES:
        errors.append(f"Growth stage must be one of: {', '.join(SUPPORTED_STAGES)}.")
    for field, column in NUMERIC_FIELDS.items():
        value = values.get(field)
        try:
            number = float(value)
        except (TypeError, ValueError):
            errors.append(f"{column} must be numeric.")
            continue
        if not math.isfinite(number):
            errors.append(f"{column} must be finite.")
            continue
        if number < 0:
            errors.append(f"{column} cannot be negative.")
            continue
        if field == "soil_ph" and number > 14:
            errors.append("Soil_pH must be between 0 and 14.")
        if field != "soil_ph" and number > 10000:
            errors.append(f"{column} is outside a physically plausible sensor range.")
        normalized[field] = number
        low, high = TRAINING_RANGES[field]
        if number < low or number > high:
            warnings.append(f"Warning: {column} is outside the model training range ({low:g} to {high:g}).")
    return {"valid": not errors, "errors": errors, "warnings": warnings, "values": normalized}