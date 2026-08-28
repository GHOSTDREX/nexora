from datetime import datetime

from pydantic import BaseModel


class IrrigationPredictionOut(BaseModel):
    prediction: str
    confidence: float
    probabilities: dict
    mapped_features: dict
    indicators: list[str]
    timestamp: datetime

    class Config:
        from_attributes = True
