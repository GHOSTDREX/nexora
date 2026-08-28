"""Validation for Yield Prediction inputs, backed by the trained model's own metadata
(models/yield_model_metadata.json) so supported crops/states/seasons can never drift
out of sync with what the fitted OneHotEncoder actually knows.
"""

from __future__ import annotations

import math
from typing import Any

from app.ml.yield_prediction.model_info import load_model_info

_metadata = load_model_info()
_options = _metadata.get("categorical_options", {})
SUPPORTED_CROPS = tuple(_options.get("crop", []))
SUPPORTED_STATES = tuple(_options.get("state", []))
SUPPORTED_SEASONS = tuple(_options.get("season", []))
_TRAIN_YEAR_RANGE = _metadata.get("training_year_range", [1997, 2020])
MAX_TRAIN_YEAR = int(_TRAIN_YEAR_RANGE[1])

NUMERIC_BOUNDS = {
    "area_hectare": (0.01, 10_000_000.0),
    "fertilizer_kg": (0.0, 10_000_000_000.0),
    "pesticide_kg": (0.0, 100_000_000.0),
}
SMALL_FIELD_WARNING_THRESHOLD_HA = 5.0


def validate_inputs(values: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    normalized: dict[str, Any] = {}

    crop = values.get("crop")
    if crop not in SUPPORTED_CROPS:
        errors.append(f"crop must be one of the {len(SUPPORTED_CROPS)} supported crops.")
    else:
        normalized["crop"] = crop

    state = values.get("state")
    if state not in SUPPORTED_STATES:
        errors.append(f"state must be one of the {len(SUPPORTED_STATES)} supported Indian states.")
    else:
        normalized["state"] = state

    season = values.get("season")
    if season not in SUPPORTED_SEASONS:
        errors.append(f"season must be one of: {', '.join(SUPPORTED_SEASONS)}.")
    else:
        normalized["season"] = season

    for field, (low, high) in NUMERIC_BOUNDS.items():
        value = values.get(field)
        try:
            number = float(value)
        except (TypeError, ValueError):
            errors.append(f"{field} must be numeric.")
            continue
        if not math.isfinite(number) or not (low <= number <= high):
            errors.append(f"{field} must be finite and within {low:g} to {high:g}.")
            continue
        normalized[field] = number

    year = values.get("year")
    try:
        year = int(year)
    except (TypeError, ValueError):
        errors.append("year must be an integer.")
    else:
        normalized["year"] = year
        if year > MAX_TRAIN_YEAR:
            warnings.append(
                f"Year {year} is beyond the model's training data (through {MAX_TRAIN_YEAR}); "
                "recent-year trends are extrapolated as flat rather than projected forward."
            )

    if "area_hectare" in normalized and normalized["area_hectare"] < SMALL_FIELD_WARNING_THRESHOLD_HA:
        warnings.append(
            "This model was trained on state/district-aggregate government records "
            "(median area ~9,300 ha) — a small field's prediction is an extrapolation "
            "and is best read as an indicative regional outlook, not a precise forecast."
        )

    return {"valid": not errors, "errors": errors, "warnings": warnings, "values": normalized}
