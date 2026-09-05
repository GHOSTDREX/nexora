"""The single authoritative Soil Health decision engine."""

from __future__ import annotations

from typing import Any

from app.ml.soil_health.config import DISCLAIMER, RULE_SOURCE, RULE_VERSION
from app.ml.soil_health.explanations import explain
from app.ml.soil_health.rules import evaluate
from app.ml.soil_health.scoring import calculate_score, overall_status
from app.ml.soil_health.validation import validate_reading

DISPLAY_NAMES = {"nitrogen": "Nitrogen", "phosphorus": "Phosphorus", "potassium": "Potassium", "soil_moisture": "Soil Moisture", "humidity": "Humidity", "temperature": "Temperature", "soil_ph": "Soil pH"}

# Mirrors frontend/src/i18n/locales/{hi,mr}.json's soil_health.factor_* keys
# — the stressed-factor sentences built in explanations.py need the same
# display names in the reply's own language, not the raw English ones.
_DISPLAY_NAMES_TR = {
    "hi": {"nitrogen": "नाइट्रोजन", "phosphorus": "फॉस्फोरस", "potassium": "पोटैशियम",
           "soil_moisture": "मृदा नमी", "humidity": "आर्द्रता", "temperature": "तापमान", "soil_ph": "मृदा pH"},
    "mr": {"nitrogen": "नायट्रोजन", "phosphorus": "फॉस्फरस", "potassium": "पोटॅशियम",
           "soil_moisture": "मातीतील ओलावा", "humidity": "आर्द्रता", "temperature": "तापमान", "soil_ph": "मातीचा pH"},
}


def predict_soil_health(language: str = "en", **readings: Any) -> dict[str, Any]:
    names = _DISPLAY_NAMES_TR.get(language, DISPLAY_NAMES)
    checked = validate_reading(readings)
    if not checked["valid"]:
        raise ValueError("Input validation failed: " + " ".join(checked["errors"]))
    values = checked["values"]
    evaluated: list[dict[str, Any]] = []
    factors: dict[str, dict[str, Any]] = {}
    for name in ("nitrogen", "phosphorus", "potassium", "soil_moisture", "humidity", "temperature"):
        status, reason = evaluate(name, values[name])
        item = {"name": names[name], "value": values[name], "status": status, "evaluated": True, "reason": reason}
        factors[name] = item
        evaluated.append(item)
    if "soil_ph" in values:
        status, reason = evaluate("soil_ph", values["soil_ph"])
        item = {"name": names["soil_ph"], "value": values["soil_ph"], "status": status, "evaluated": True, "reason": reason}
        factors["soil_ph"] = item
        evaluated.append(item)
    else:
        factors["soil_ph"] = {"name": names["soil_ph"], "value": None, "status": "Not evaluated", "evaluated": False, "reason": "Soil pH was not provided."}
    stressed = [item for item in evaluated if item["status"] == "Moderate Stress"]
    status = overall_status(evaluated)
    explanation, recommendation, primary = explain(status, stressed, language)
    return {"overall_status": status, "health_score": calculate_score(evaluated), "factors": factors, "stress_factors": [item["name"] for item in stressed], "primary_issue": primary, "recommendation": recommendation, "explanation": explanation, "rule_version": RULE_VERSION, "rule_source": RULE_SOURCE, "disclaimer": DISCLAIMER}
