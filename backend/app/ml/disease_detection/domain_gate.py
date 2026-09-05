"""
Domain / subject gate — architectural placeholder, ported verbatim from the
reference Smart-Farming-AI backend (backend/domain_gate.py).

STATUS: NOT IMPLEMENTED, and per integration instructions must not be
activated here either. A real domain gate needs an in-domain reference
(real paddy leaf embeddings) that does not exist in this workspace.
Building one from OOD proxy data alone would be fabrication, not
validation. This module exists only so the pipeline shape (quality ->
readiness -> domain gate -> inference -> calibration -> uncertainty ->
recommendation) is represented end-to-end in API responses. It never
blocks a prediction and is not counted as a safety layer anywhere.
"""

from dataclasses import dataclass


@dataclass
class DomainGateResult:
    status: str = "not_implemented"
    note: str = (
        "Domain gate is not implemented — requires real paddy leaf embeddings "
        "as an in-domain reference, which do not exist in this workspace."
    )


def assess_domain(*_args, **_kwargs) -> DomainGateResult:
    """Always a pass-through. Present for architectural completeness only."""
    return DomainGateResult()
