from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from fertilizer_explanation_engine import explain_recommendation
from fertilizer_validator import FEATURE_COLUMNS, nutrient_status, validate_inputs
from model_info import load_model_info

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "models" / "fertilizer_recommendation_model.pkl"
MODEL = None


def load_model():
    global MODEL
    if MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
        MODEL = joblib.load(MODEL_PATH)
    return MODEL


def recommend_fertilizer(**values: Any) -> dict[str, Any]:
    validation = validate_inputs(values)
    if not validation["valid"]:
        raise ValueError(" ".join(validation["errors"]))
    clean = validation["values"]
    model = load_model()
    row = pd.DataFrame([{"Crop_Type": clean["crop_type"], "Soil_Type": clean["soil_type"], "Soil_pH": clean["soil_ph"], "Nitrogen_Level": clean["nitrogen_level"], "Phosphorus_Level": clean["phosphorus_level"], "Potassium_Level": clean["potassium_level"], "Electrical_Conductivity": clean["electrical_conductivity"], "Crop_Growth_Stage": clean["crop_growth_stage"]}], columns=FEATURE_COLUMNS)
    prediction = str(model.predict(row)[0])
    probability_map = dict(zip(model.classes_, model.predict_proba(row)[0]))
    probability = round(float(probability_map[prediction]) * 100, 2)
    statuses = nutrient_status(clean["nitrogen_level"], clean["phosphorus_level"], clean["potassium_level"], clean["soil_ph"])
    warnings = list(validation["warnings"])
    warnings.append("Prototype AI-assisted decision-support only. Field and agronomic validation are required before application.")
    if prediction == "SSP":
        warnings.append("SSP is a low-support class in the current training dataset. Additional agronomic validation is strongly recommended.")
    if probability >= 99.99:
        warnings.append("Decision Tree probabilities can be sharp and should not be interpreted as real-world certainty.")
    metadata = load_model_info()
    return {
        "crop": clean["crop_type"],
        "recommended_fertilizer": prediction,
        "model_probability": probability,
        "nutrient_status": statuses,
        "reason": explain_recommendation(prediction, statuses, clean["soil_ph"]),
        "validation": {"status": "warning" if validation["warnings"] else "valid", "warnings": validation["warnings"]},
        "model": {"name": metadata.get("model_name", "Tuned Decision Tree"), "version": metadata.get("training_date", "prototype"), "prototype": True},
        "warnings": warnings,
        "model_version": metadata.get("training_date", "prototype"),
        "prototype": True,
    }


if __name__ == "__main__":
    print(recommend_fertilizer(crop_type="Rice", soil_type="Loamy", soil_ph=6.5, nitrogen_level=45, phosphorus_level=55, potassium_level=70, electrical_conductivity=1.2, crop_growth_stage="Vegetative"))