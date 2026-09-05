"""
Deterministic recommendation lookup — ported from the reference
Smart-Farming-AI backend (backend/recommendations/service.py).

Not an AI recommendation model — a static, hand-curated knowledge base
(recommendations.json, IRRI Rice Knowledge Bank sourced) keyed by the exact
classifier class name. No generation, inference, or interpolation.
"""

import json
from functools import lru_cache
from typing import Optional

from app.ml.disease_detection.config import RECOMMENDATIONS_PATH


@lru_cache(maxsize=1)
def _load_recommendations() -> dict:
    if not RECOMMENDATIONS_PATH.exists():
        raise FileNotFoundError(f"recommendations.json not found at {RECOMMENDATIONS_PATH}")
    with open(RECOMMENDATIONS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_recommendation(class_name: str) -> Optional[dict]:
    """Returns the recommendation entry for a class, or None if absent —
    callers must treat that as missing data, not an empty/normal case."""
    return _load_recommendations().get(class_name)
