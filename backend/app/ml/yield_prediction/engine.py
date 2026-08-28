"""Yield Prediction service — UI-independent.

Trained by `Yield Prediction/src/train_model.py` (RandomForestRegressor, tuned
with time-aware cross-validation on 1997-2020 Indian crop-yield government
statistics). See models/yield_model_metadata.json for the exact feature list,
supported crop/state/season options, held-out evaluation, and documented
limitations — in particular that this is trained on state/district-aggregate
data, so single small-field predictions are an extrapolation best read as an
indicative regional outlook rather than a precise per-field forecast.
"""

from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.ml.yield_prediction.model_info import load_model_info
from app.ml.yield_prediction.validator import validate_inputs

MODEL_PATH = Path(__file__).resolve().parent / "models" / "final_yield_prediction_model.pkl"
_MODEL = None


def _load_model():
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found: {MODEL_PATH}")
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def predict_yield(**values: Any) -> dict[str, Any]:
    validation = validate_inputs(values)
    if not validation["valid"]:
        raise ValueError(" ".join(validation["errors"]))
    clean = validation["values"]
    model = _load_model()

    fertilizer_per_ha = clean["fertilizer_kg"] / clean["area_hectare"]
    pesticide_per_ha = clean["pesticide_kg"] / clean["area_hectare"]

    row = pd.DataFrame(
        [
            {
                "crop": clean["crop"],
                "state": clean["state"],
                "season": clean["season"],
                "year": clean["year"],
                "area": clean["area_hectare"],
                "fertilizer_per_ha": fertilizer_per_ha,
                "pesticide_per_ha": pesticide_per_ha,
            }
        ]
    )

    predicted_yield = max(float(model.predict(row)[0]), 0.0)
    estimated_total_production = predicted_yield * clean["area_hectare"]

    metadata = load_model_info()
    warnings = list(validation["warnings"])
    warnings.append(
        "Prototype trained on historical government statistics; field and agronomic "
        "validation are required before relying on this for planning decisions."
    )
    if clean["crop"].strip().lower() == "coconut":
        warnings.append(
            "Coconut yield in this dataset is reported in nuts/hectare, not "
            "tonnes/hectare like other crops — do not compare its value across crops."
        )

    return {
        "crop": clean["crop"],
        "state": clean["state"],
        "season": clean["season"],
        "year": clean["year"],
        "area_hectare": clean["area_hectare"],
        "predicted_yield": round(predicted_yield, 3),
        "estimated_total_production": round(estimated_total_production, 2),
        "fertilizer_per_ha": round(fertilizer_per_ha, 2),
        "pesticide_per_ha": round(pesticide_per_ha, 3),
        "warnings": warnings,
        "model_version": metadata.get("model_name", "prototype"),
    }
