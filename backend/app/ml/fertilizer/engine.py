"""Fertilizer category recommendation — UI-independent service.

Ported from `Fertilizer Recommendation/src/fertilizer_engine.py`. Predicts a
fertilizer category (not a validated dose) for Rice or Sugarcane using the
trained Pipeline(ColumnTransformer + OneHotEncoder + DecisionTreeClassifier)
artifact. See models/fertilizer_model_metadata.json for training details and
known limitations (prototype dataset, SSP low-support class).
"""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.ml.fertilizer.explanation_engine import explain_recommendation
from app.ml.fertilizer.model_info import load_model_info
from app.ml.fertilizer.validator import FEATURE_COLUMNS, nutrient_status, validate_inputs

MODEL_PATH = Path(__file__).resolve().parent / "models" / "fertilizer_recommendation_model.pkl"
_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def recommend_fertilizer(**values: Any) -> dict[str, Any]:
    validation = validate_inputs(values)
    if not validation["valid"]:
        raise ValueError(" ".join(validation["errors"]))
    clean = validation["values"]
    model = _load_model()
    row = pd.DataFrame(
        [
            {
                "Crop_Type": clean["crop_type"],
                "Soil_Type": clean["soil_type"],
                "Soil_pH": clean["soil_ph"],
                "Nitrogen_Level": clean["nitrogen_level"],
                "Phosphorus_Level": clean["phosphorus_level"],
                "Potassium_Level": clean["potassium_level"],
                "Electrical_Conductivity": clean["electrical_conductivity"],
                "Crop_Growth_Stage": clean["crop_growth_stage"],
            }
        ],
        columns=FEATURE_COLUMNS,
    )
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
        "input_features": {
            "soil_type": clean["soil_type"],
            "crop_growth_stage": clean["crop_growth_stage"],
            "soil_ph": clean["soil_ph"],
            "nitrogen_level": clean["nitrogen_level"],
            "phosphorus_level": clean["phosphorus_level"],
            "potassium_level": clean["potassium_level"],
            "electrical_conductivity": clean["electrical_conductivity"],
        },
        "warnings": warnings,
        "model_version": metadata.get("training_date", "prototype"),
    }
