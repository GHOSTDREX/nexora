"""Temporal reasoning over historical observations of the same pest/species.

This is a relative-change heuristic over recorded counts, intended to raise
or lower monitoring priority — it is explicitly NOT an epidemiological model
and makes no claim about infestation rate, spread speed, or population
dynamics. See docs/AGRICULTURAL_ADVISORY.md, "Temporal reasoning."
"""

from __future__ import annotations

from app.ml.agricultural_advisory.config import settings
from app.ml.agricultural_advisory.schemas import TrendDirection, TrendResult


def compute_trend(history: list[dict]) -> TrendResult:
    """`history` is a list of {"timestamp": str, "count": int, ...} dicts for
    ONE species/pest at ONE field, ordered oldest-first or unordered (we sort
    here). Records with a missing/invalid count or timestamp are dropped.
    """
    usable = [
        h for h in history
        if isinstance(h.get("count"), (int, float)) and h.get("timestamp")
    ]
    usable.sort(key=lambda h: h["timestamp"])

    if not usable:
        return TrendResult(direction=TrendDirection.INSUFFICIENT_DATA, observation_count=0)

    first_detected = usable[0]["timestamp"]
    last_detected = usable[-1]["timestamp"]

    if len(usable) < settings.min_observations_for_trend:
        return TrendResult(
            direction=TrendDirection.INSUFFICIENT_DATA,
            first_detected=first_detected,
            last_detected=last_detected,
            observation_count=len(usable),
            current_count=int(usable[-1]["count"]),
            note=(
                f"Only {len(usable)} observation(s) recorded; at least "
                f"{settings.min_observations_for_trend} are needed to assess a trend."
            ),
        )

    previous_count = int(usable[-2]["count"])
    current_count = int(usable[-1]["count"])

    if previous_count == 0:
        direction = TrendDirection.INCREASING if current_count > 0 else TrendDirection.STABLE
    else:
        ratio = current_count / previous_count
        if ratio >= settings.trend_increase_ratio:
            direction = TrendDirection.INCREASING
        elif ratio <= settings.trend_decrease_ratio:
            direction = TrendDirection.DECREASING
        else:
            direction = TrendDirection.STABLE

    return TrendResult(
        direction=direction,
        first_detected=first_detected,
        last_detected=last_detected,
        observation_count=len(usable),
        previous_count=previous_count,
        current_count=current_count,
        note=(
            f"Count changed from {previous_count} to {current_count} across the "
            f"last two recorded observations."
        ),
    )
