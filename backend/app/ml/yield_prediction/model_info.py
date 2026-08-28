"""Model metadata access."""

import json
from pathlib import Path


def load_model_info() -> dict:
    path = Path(__file__).resolve().parent / "models" / "yield_model_metadata.json"
    if not path.exists():
        return {"model_name": "RandomForestRegressor", "categorical_options": {}, "training_year_range": [1997, 2020]}
    return json.loads(path.read_text(encoding="utf-8"))
