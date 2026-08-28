"""Model metadata access."""

import json
from pathlib import Path


def load_model_info() -> dict:
    path = Path(__file__).resolve().parent / "models" / "fertilizer_model_metadata.json"
    if not path.exists():
        return {"model_name": "Tuned Decision Tree", "supported_crops": ["Rice", "Sugarcane"]}
    return json.loads(path.read_text(encoding="utf-8"))
