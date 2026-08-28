"""
AgriNova — Crop Recommendation Inference Wrapper
"""

import os

import joblib
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODULE_DIR, "model.joblib")

FEATURES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]


class CropRecommender:
    def __init__(self, model_path: str | None = None):
        model_path = model_path or MODEL_PATH
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Crop recommendation model not found at {model_path}. "
                "Run: python -m app.ml.crop_recommendation.train"
            )
        self.model = joblib.load(model_path)

    def recommend(self, n: float, p: float, k: float, temperature: float, humidity: float, ph: float, rainfall: float, top_k: int = 4) -> dict:
        row = pd.DataFrame(
            [[n, p, k, temperature, humidity, ph, rainfall]], columns=FEATURES
        )
        probs = self.model.predict_proba(row)[0]
        classes = self.model.classes_

        ranked = sorted(zip(classes, probs), key=lambda pair: pair[1], reverse=True)
        top_crop, top_conf = ranked[0]
        alternatives = [
            {"crop": crop, "confidence": round(float(conf) * 100, 1)}
            for crop, conf in ranked[1 : top_k]
        ]

        return {
            "top_crop": str(top_crop),
            "confidence": round(float(top_conf) * 100, 1),
            "alternatives": alternatives,
            "input_features": {
                "N": n, "P": p, "K": k, "temperature": temperature,
                "humidity": humidity, "ph": ph, "rainfall": rainfall,
            },
        }
