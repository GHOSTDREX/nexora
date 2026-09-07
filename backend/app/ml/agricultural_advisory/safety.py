"""Safety gates.

Every advisory must pass through these gates, in order, before any
recommendation is produced. A failed gate never causes the engine to guess —
it produces an explicit "insufficient evidence" / "further observation
required" / "knowledge gap" outcome instead. See docs/AGRICULTURAL_ADVISORY.md,
"Safety gates."

    DATA QUALITY GATE
          |
    MODEL CONFIDENCE GATE
          |
    CROP COMPATIBILITY GATE
          |
    KNOWLEDGE BASE GATE
          |
    CHEMICAL-CONTENT SAFETY GATE   (applied to the loaded KB itself, at load time)
          |
    ADVISORY
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from app.ml.agricultural_advisory.knowledge_base.loader import KnowledgeBase
from app.ml.agricultural_advisory.schemas import DataQuality, Observation


@dataclass
class GateResult:
    passed: bool
    reason: str = ""


def data_quality_gate(observation: Observation) -> GateResult:
    """Blocks INVALID or completely MISSING observations from generating advice."""
    if observation.quality in (DataQuality.INVALID, DataQuality.MISSING):
        return GateResult(
            passed=False,
            reason=f"Observation quality is {observation.quality.value}; cannot generate advice from it.",
        )
    return GateResult(passed=True)


def confidence_gate(observation: Observation, required_threshold: float) -> GateResult:
    """Blocks recommendations built on low-confidence AI output.

    `required_threshold` must be sourced from the producing model's own
    configuration — this function never invents a cutoff.
    """
    if observation.confidence is None:
        return GateResult(passed=False, reason="No confidence value available.")
    if observation.confidence < required_threshold:
        return GateResult(
            passed=False,
            reason=(
                f"Confidence {observation.confidence:.2f} is below the required "
                f"threshold {required_threshold:.2f}; further verification is needed "
                f"before treatment-oriented advice is given."
            ),
        )
    return GateResult(passed=True)


def crop_compatibility_gate(
    kb: KnowledgeBase, pest_class_name: str, crop: Optional[str]
) -> GateResult:
    """Checks whether the knowledge base has rules applicable to the stated crop.

    A missing/unstated crop, or a pest entry that lists "general" as a
    supported crop, does not block the gate — it only means recommendations
    will be presented as general rather than crop-specific.
    """
    entry = kb.pests.get(pest_class_name)
    if entry is None:
        return GateResult(passed=False, reason="No knowledge-base entry for this pest.")

    supported = entry.get("supported_crops", [])
    if not crop or "general" in supported:
        return GateResult(passed=True, reason="No specific crop stated; using general guidance.")
    if crop.lower() in [c.lower() for c in supported]:
        return GateResult(passed=True)
    return GateResult(
        passed=False,
        reason=(
            f"This pest's verified guidance covers {supported}, not the stated crop "
            f"'{crop}'. Recommendations are not shown to avoid misapplying cross-crop advice."
        ),
    )


def knowledge_base_gate(kb: KnowledgeBase, pest_class_name: str) -> GateResult:
    if pest_class_name not in kb.pests:
        return GateResult(
            passed=False,
            reason=(
                "No verified knowledge-base entry exists for this pest class. "
                "This is a knowledge gap, not a system error."
            ),
        )
    entry = kb.pests[pest_class_name]
    if not entry.get("actions"):
        return GateResult(passed=False, reason="Knowledge-base entry has no verified actions.")
    return GateResult(passed=True)
