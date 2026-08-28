from datetime import datetime

from pydantic import BaseModel


class SoilHealthFactor(BaseModel):
    name: str
    value: float | None
    status: str
    evaluated: bool
    reason: str


class SoilHealthOut(BaseModel):
    overall_status: str
    health_score: int
    factors: dict[str, SoilHealthFactor]
    stress_factors: list[str]
    primary_issue: str | None
    recommendation: str
    explanation: str
    rule_version: str
    rule_source: str
    disclaimer: str
    timestamp: datetime | None = None
