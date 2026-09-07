"""Image-level infestation severity heuristic.

PROTOTYPE HEURISTIC — NOT AN AGRONOMIC MODEL.

The YOLO model has no concept of "severity"; it only detects individual
pests in a single still image. Everything in this module is an
application-level guess at how concerning a given image looks, based on
what is visible in that one frame. It says nothing about the health of a
field, a crop, or a farm.

This is intentionally isolated so it can be swapped for a real agronomic
model later without touching the detector.
"""

from __future__ import annotations

from app.ml.pest_detection.config import settings
from app.ml.pest_detection.schemas import Detection, SeverityLevel, SeverityResult

# Relative weights for the heuristic score (0..1). Tune via config, not here,
# if these need to change per-deployment.
_COUNT_WEIGHT = 0.4
_CONFIDENCE_WEIGHT = 0.25
_SPECIES_WEIGHT = 0.15
_COVERAGE_WEIGHT = 0.2

_COUNT_SATURATION = 8  # detections at/above this count contribute full weight
_SPECIES_SATURATION = 3  # distinct species at/above this count contribute full weight


def calculate_severity(
    detections: list[Detection], image_width: int, image_height: int
) -> SeverityResult:
    """Derive a LOW / MODERATE / HIGH image-level indicator from raw detections."""
    if not detections:
        return SeverityResult(level=SeverityLevel.NONE, score=0.0)

    count_score = min(len(detections) / _COUNT_SATURATION, 1.0)

    confidences = [d.confidence for d in detections]
    confidence_score = sum(confidences) / len(confidences)

    species_count = len({d.name for d in detections})
    species_score = min(species_count / _SPECIES_SATURATION, 1.0)

    image_area = max(image_width * image_height, 1)
    covered_area = sum(d.bbox.area for d in detections)
    coverage_score = min(covered_area / image_area, 1.0)

    score = (
        _COUNT_WEIGHT * count_score
        + _CONFIDENCE_WEIGHT * confidence_score
        + _SPECIES_WEIGHT * species_score
        + _COVERAGE_WEIGHT * coverage_score
    )

    thresholds = settings.severity
    if score >= thresholds.high_score:
        level = SeverityLevel.HIGH
    elif score >= thresholds.moderate_score:
        level = SeverityLevel.MODERATE
    else:
        level = SeverityLevel.LOW

    return SeverityResult(level=level, score=score)
