from pydantic import BaseModel


class CropConditionRequest(BaseModel):
    crop: str  # rice | sugarcane


class CropRecommendationOut(BaseModel):
    top_crop: str
    confidence: float
    alternatives: list[dict]
    input_features: dict
