"""Advisory API router.

Deliberately NOT its own FastAPI app — this follows the existing project's
convention of a single FastAPI application (see pest_detection/api.py),
which mounts this router via `app.include_router(advisory_router)`. This
endpoint never runs model inference itself; it only consumes already-computed
pest/disease detection results.
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from app.ml.agricultural_advisory.engine import get_advisory_engine
from app.ml.agricultural_advisory.logging_config import get_logger

logger = get_logger()

router = APIRouter(prefix="/api/advisory", tags=["advisory"])


class AdvisoryRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    farm_id: Optional[str] = None
    field_id: Optional[str] = None
    crop: Optional[str] = None
    growth_stage: Optional[str] = None
    observation_timestamp: Optional[str] = None
    pest_result: Optional[dict[str, Any]] = None
    disease_result: Optional[dict[str, Any]] = None
    sensor_data: Optional[dict[str, Any]] = None
    weather_data: Optional[dict[str, Any]] = None
    historical_observations: Optional[list[dict[str, Any]]] = None


@router.post("/analyze")
def analyze(request: AdvisoryRequest) -> dict:
    engine = get_advisory_engine()
    try:
        result = engine.analyze(request.model_dump(exclude_none=True))
    except Exception as exc:  # noqa: BLE001 - never leak internals to the client
        logger.error("ADVISORY_ANALYSIS_ERROR error=%s", exc)
        return {
            "status": "insufficient_evidence",
            "risk_assessments": [],
            "recommendations": [],
            "explanations": [],
            "sources": [],
            "audit": None,
            "message": "Unable to generate an advisory for this request. Please try again.",
        }
    logger.info(
        "ADVISORY_ANALYSIS_COMPLETE status=%s recommendations=%d",
        result.status.value,
        len(result.recommendations),
    )
    return result.to_dict()


@router.get("/knowledge-base/versions")
def knowledge_base_versions() -> dict:
    from agricultural_advisory.config import (
        ADVISORY_ENGINE_VERSION,
        KNOWLEDGE_BASE_VERSION,
        RULE_SET_VERSION,
    )

    return {
        "advisory_engine_version": ADVISORY_ENGINE_VERSION,
        "knowledge_base_version": KNOWLEDGE_BASE_VERSION,
        "rule_set_version": RULE_SET_VERSION,
    }
