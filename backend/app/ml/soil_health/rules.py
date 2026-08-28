"""Rule evaluators backed by the single authoritative RULES table."""

from __future__ import annotations

from app.ml.soil_health.config import RULES


def classify_threshold(name: str, value: float) -> tuple[str, str]:
    threshold = RULES[name]["healthy_min"]
    if value >= threshold:
        return "Healthy", f"{name.replace('_', ' ').title()} is at or above the validated healthy threshold ({threshold:g})."
    return "Moderate Stress", f"{name.replace('_', ' ').title()} is below the validated healthy threshold ({threshold:g})."


def classify_range(name: str, value: float) -> tuple[str, str]:
    rule = RULES[name]
    low, high = rule["healthy_min"], rule["healthy_max"]
    label = name.replace("_", " ").title()
    if low <= value <= high:
        return "Healthy", f"{label} is inside the healthy range ({low:g}-{high:g})."
    return "Moderate Stress", f"{label} is outside the healthy range ({low:g}-{high:g})."


def evaluate(name: str, value: float) -> tuple[str, str]:
    return classify_range(name, value) if "healthy_max" in RULES[name] else classify_threshold(name, value)
