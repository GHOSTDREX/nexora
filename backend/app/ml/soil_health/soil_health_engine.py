"""The single authoritative Soil Health decision engine."""

from __future__ import annotations

from typing import Any

from app.ml.soil_health.config import DISCLAIMER, RULE_SOURCE, RULE_VERSION
from app.ml.soil_health.explanations import explain
from app.ml.soil_health.rules import evaluate
from app.ml.soil_health.scoring import calculate_score, overall_status
from app.ml.soil_health.validation import validate_reading

DISPLAY_NAMES = {"nitrogen": "Nitrogen", "phosphorus": "Phosphorus", "potassium": "Potassium", "soil_moisture": "Soil Moisture", "humidity": "Humidity", "temperature": "Temperature", "soil_ph": "Soil pH"}


def predict_soil_health(**readings: Any) -> dict[str, Any]:
    checked = validate_reading(readings)
    if not checked["valid"]:
        raise ValueError("Input validation failed: " + " ".join(checked["errors"]))
    values = checked["values"]
    evaluated: list[dict[str, Any]] = []
    factors: dict[str, dict[str, Any]] = {}
    for name in ("nitrogen", "phosphorus", "potassium", "soil_moisture", "humidity", "temperature"):
        status, reason = evaluate(name, values[name])
        item = {"name": DISPLAY_NAMES[name], "value": values[name], "status": status, "evaluated": True, "reason": reason}
        factors[name] = item
        evaluated.append(item)
    if "soil_ph" in values:
        status, reason = evaluate("soil_ph", values["soil_ph"])
        item = {"name": DISPLAY_NAMES["soil_ph"], "value": values["soil_ph"], "status": status, "evaluated": True, "reason": reason}
        factors["soil_ph"] = item
        evaluated.append(item)
    else:
        factors["soil_ph"] = {"name": DISPLAY_NAMES["soil_ph"], "value": None, "status": "Not evaluated", "evaluated": False, "reason": "Soil pH was not provided."}
    stressed = [item for item in evaluated if item["status"] == "Moderate Stress"]
    status = overall_status(evaluated)
    explanation, recommendation, primary = explain(status, stressed)
    return {"overall_status": status, "health_score": calculate_score(evaluated), "factors": factors, "stress_factors": [item["name"] for item in stressed], "primary_issue": primary, "recommendation": recommendation, "explanation": explanation, "rule_version": RULE_VERSION, "rule_source": RULE_SOURCE, "disclaimer": DISCLAIMER}
