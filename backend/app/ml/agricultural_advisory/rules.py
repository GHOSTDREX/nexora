"""Deterministic rule engine.

Recommendations are never generated ad hoc — every one comes from a
knowledge-base action entry (agricultural_advisory/knowledge_base/pests.json)
that already carries a `rule_id` and `source_ids`. This module's only job is
to (a) select which KB actions apply, and (b) adjust their priority based on
the computed RiskAssessment, using one explicit, documented table — never a
one-off if-statement per pest.
"""

from __future__ import annotations

from app.ml.agricultural_advisory.knowledge_base.loader import KnowledgeBase
from app.ml.agricultural_advisory.schemas import (
    Observation,
    Priority,
    Recommendation,
    RecommendationType,
    RiskAssessment,
    RiskLevel,
)

_PRIORITY_ORDER = [
    Priority.INFO,
    Priority.LOW,
    Priority.MODERATE,
    Priority.HIGH,
    Priority.URGENT,
]


def escalate_priority(base: Priority, risk_level: RiskLevel) -> Priority:
    """Priority escalation table (documented, not implicit):

    - risk HIGH:            bump one level, capped at HIGH (URGENT is reserved
                             for the explicit ESCALATE rule below, not a bumped MONITOR).
    - risk MODERATE:        unchanged.
    - risk LOW or NONE:     drop one level (floor at INFO).
    """
    idx = _PRIORITY_ORDER.index(base)
    if risk_level == RiskLevel.HIGH:
        idx = min(idx + 1, _PRIORITY_ORDER.index(Priority.HIGH))
    elif risk_level in (RiskLevel.LOW, RiskLevel.NONE):
        idx = max(idx - 1, 0)
    return _PRIORITY_ORDER[idx]


def generate_pest_recommendations(
    kb: KnowledgeBase, observation: Observation, risk: RiskAssessment
) -> list[Recommendation]:
    entry = kb.pests.get(observation.name)
    if entry is None:
        return []

    recommendations = []
    for action in entry.get("actions", []):
        base_priority = Priority(action["base_priority"])
        priority = escalate_priority(base_priority, risk.level)
        recommendations.append(
            Recommendation(
                rule_id=action["rule_id"],
                priority=priority,
                type=RecommendationType(action["type"]),
                action=action["action"],
                evidence={
                    "pest": observation.name,
                    "confidence": observation.confidence,
                    "count": observation.count,
                    "risk_level": risk.level.value,
                },
                source_ids=action.get("source_ids", []),
            )
        )

    if risk.level == RiskLevel.HIGH:
        escalation_text = entry.get("escalation_criteria")
        if escalation_text:
            # Reuses the same sources as the pest's own MONITOR rule for
            # traceability — the escalation criterion comes from the same
            # verified fact sheet, not a new, unsourced claim.
            monitor_action = next(
                (a for a in entry.get("actions", []) if a["type"] == "MONITOR"), None
            )
            source_ids = monitor_action.get("source_ids", []) if monitor_action else []
            recommendations.append(
                Recommendation(
                    rule_id=f"{entry['id'].upper()}_ESCALATE_001",
                    priority=Priority.URGENT,
                    type=RecommendationType.ESCALATE,
                    action=(
                        f"Risk indicator is HIGH for {entry['common_name']}. {escalation_text} "
                        "Consider contacting your local agricultural extension service for "
                        "field-level verification."
                    ),
                    evidence={
                        "pest": observation.name,
                        "confidence": observation.confidence,
                        "count": observation.count,
                        "risk_level": risk.level.value,
                    },
                    source_ids=source_ids,
                )
            )

    return recommendations
