from datetime import datetime

from pydantic import BaseModel


class FertilizerRequest(BaseModel):
    crop: str  # Rice | Sugarcane


class FertilizerRecommendationOut(BaseModel):
    crop: str
    recommended_fertilizer: str
    model_probability: float
    nutrient_status: dict[str, str]
    reason: str
    input_features: dict
    warnings: list[str]
    timestamp: datetime | None = None
