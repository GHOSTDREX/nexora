"""
Layered decision engine — ported verbatim from the reference
Smart-Farming-AI backend (backend/decision.py).

image -> technical quality -> model readiness -> domain gate (pass-through,
not implemented) -> inference + calibration (unchanged) -> uncertainty/OOD
heuristic -> final decision_state -> recommendation ONLY on "accepted".

Feature-flagged and reversible: with ENABLE_READINESS_CHECK and
ENABLE_OOD_HEURISTIC both False, this reduces exactly to the original
Phase-1 rule (confidence >= threshold).
"""

from dataclasses import dataclass, field
from typing import List, Optional

from app.ml.disease_detection.config import (
    CONFIDENCE_THRESHOLD,
    ENABLE_OOD_HEURISTIC,
    ENABLE_READINESS_CHECK,
    OOD_CONFIDENCE_THRESHOLD,
    OOD_MARGIN_THRESHOLD,
    OOD_NORMALIZED_ENTROPY_THRESHOLD,
)
from app.ml.disease_detection.image_quality import QualityResult
from app.ml.disease_detection.image_readiness import ReadinessResult
from app.ml.disease_detection.inference import PredictionResult

ACCEPTED = "accepted"
UNCERTAIN = "uncertain"
IMAGE_UNSUITABLE = "image_unsuitable"
SUBJECT_UNSUITABLE = "subject_unsuitable"


@dataclass
class Decision:
    state: str
    accepted: bool  # True only for ACCEPTED — drives whether a recommendation is looked up
    message: str
    guidance: List[str] = field(default_factory=list)
    ood_flagged: bool = False


def _is_ood_by_heuristic(confidence: float, normalized_entropy: float, margin: float) -> bool:
    return (
        normalized_entropy > OOD_NORMALIZED_ENTROPY_THRESHOLD
        and margin < OOD_MARGIN_THRESHOLD
        and confidence < OOD_CONFIDENCE_THRESHOLD
    )


def decide(
    quality: QualityResult,
    readiness: Optional[ReadinessResult],
    prediction: PredictionResult,
) -> Decision:
    if quality.status == "poor":
        return Decision(
            state=IMAGE_UNSUITABLE,
            accepted=False,
            message="Image quality is too low for a reliable analysis.",
            guidance=quality.reasons or ["Please retake the photo with better lighting and focus."],
        )

    if ENABLE_READINESS_CHECK and readiness is not None and readiness.status == "unsuitable":
        return Decision(
            state=IMAGE_UNSUITABLE,
            accepted=False,
            message="The leaf isn't clearly visible enough in this photo for a reliable analysis.",
            guidance=readiness.guidance
            or ["Move closer to the leaf and make sure it fills most of the frame."],
        )

    ood_flagged = ENABLE_OOD_HEURISTIC and _is_ood_by_heuristic(
        prediction.confidence, prediction.signals.normalized_entropy, prediction.signals.margin
    )

    if ood_flagged:
        return Decision(
            state=SUBJECT_UNSUITABLE,
            accepted=False,
            message="This image does not appear suitable for paddy disease analysis.",
            guidance=[
                "Make sure the photo shows a paddy (rice) leaf clearly and up close.",
            ],
            ood_flagged=True,
        )

    if prediction.confidence < CONFIDENCE_THRESHOLD:
        return Decision(
            state=UNCERTAIN,
            accepted=False,
            message="Prediction confidence is below 90%.",
            guidance=[
                "Upload a clearer image with the affected leaf closer to the camera and with better lighting.",
            ],
        )

    return Decision(
        state=ACCEPTED,
        accepted=True,
        message="Prediction accepted.",
    )
