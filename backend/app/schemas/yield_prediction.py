from datetime import datetime

from pydantic import BaseModel, Field


class YieldPredictionRequest(BaseModel):
    crop: str
    state: str
    season: str
    year: int
    area_hectare: float = Field(gt=0)
    fertilizer_kg: float = Field(ge=0)
    pesticide_kg: float = Field(ge=0)


class YieldPredictionOut(BaseModel):
    crop: str
    state: str
    season: str
    year: int
    area_hectare: float
    predicted_yield: float
    estimated_total_production: float
    fertilizer_per_ha: float
    pesticide_per_ha: float
    warnings: list[str]
    timestamp: datetime | None = None
