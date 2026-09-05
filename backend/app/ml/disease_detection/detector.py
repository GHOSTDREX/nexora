"""
Single entry point wrapping the reference Smart-Farming-AI pipeline:
quality -> readiness -> domain gate (pass-through) -> inference+calibration
-> uncertainty/OOD -> decision -> recommendation. Mirrors the reference
backend/main.py's predict_endpoint response shape exactly.

Loaded once as a module-level singleton (app/routers/disease.py), same
pattern as CropRecommender() in app/routers/crop.py — the checkpoint is
never re-read per request.
"""

import logging

import torch
from PIL import Image

from app.ml.disease_detection import config
from app.ml.disease_detection.decision import decide
from app.ml.disease_detection.domain_gate import assess_domain
from app.ml.disease_detection.image_quality import assess_quality
from app.ml.disease_detection.image_readiness import assess_readiness
from app.ml.disease_detection.inference import predict
from app.ml.disease_detection.model import ModelLoadError, load_checkpoint
from app.ml.disease_detection.recommendations import get_recommendation

logger = logging.getLogger("agrinova.disease_detection")

DetectorLoadError = ModelLoadError


class DiseaseDetector:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model, self.checkpoint_metadata = load_checkpoint(
            config.BEST_CHECKPOINT_PATH, device=self.device
        )

    def model_info(self) -> dict:
        return {
            "model": config.MODEL_NAME,
            "framework": config.FRAMEWORK,
            "input_size": {"width": config.IMAGE_SIZE, "height": config.IMAGE_SIZE},
            "num_classes": config.NUM_CLASSES,
            "class_mapping": {str(i): name for i, name in enumerate(config.CLASS_NAMES)},
            "temperature": config.TEMPERATURE,
            "confidence_threshold": config.CONFIDENCE_THRESHOLD,
            "verified_evaluation": {
                "label": "VERIFIED MODEL EVALUATION (historical, from training/test run — not per-image accuracy)",
                "validation_accuracy": config.VERIFIED_VALIDATION_ACCURACY,
                "test_accuracy": config.VERIFIED_TEST_ACCURACY,
                "accepted_rate_at_threshold": config.VERIFIED_ACCEPTED_RATE,
                "accepted_accuracy_at_threshold": config.VERIFIED_ACCEPTED_ACCURACY,
            },
            "checkpoint": self.checkpoint_metadata,
        }

    def predict(self, image: Image.Image, raw_bytes: bytes) -> dict:
        width, height = image.size

        quality = assess_quality(image)
        readiness = assess_readiness(image) if config.ENABLE_READINESS_CHECK else None
        domain_gate = assess_domain()

        result = predict(self.model, image, device=self.device)
        decision = decide(quality, readiness, result)
        recommendation = get_recommendation(result.prediction) if decision.accepted else None

        return {
            "prediction": result.prediction,
            "display_name": result.display_name,
            "confidence": round(result.confidence, 4),
            "accepted": decision.accepted,
            "decision_state": decision.state,
            "decision_message": decision.message,
            "guidance": decision.guidance,
            "top3": [
                {"class": c.class_name, "display_name": c.display_name, "confidence": round(c.confidence, 4)}
                for c in result.top3
            ],
            "image": {
                "width": width,
                "height": height,
                "megapixels": round((width * height) / 1_000_000, 2),
                "file_size_bytes": len(raw_bytes),
            },
            "quality": {
                "status": quality.status,
                "brightness": quality.brightness,
                "blur_score": quality.blur_score,
                "reasons": quality.reasons,
            },
            "readiness": (
                {
                    "status": readiness.status,
                    "vegetation_ratio": readiness.vegetation_ratio,
                    "largest_component_ratio": readiness.largest_component_ratio,
                    "reasons": readiness.reasons,
                    "guidance": readiness.guidance,
                    "note": "Heuristic, not validated against real paddy photos.",
                }
                if readiness is not None
                else None
            ),
            "uncertainty": {
                "normalized_entropy": round(result.signals.normalized_entropy, 4),
                "margin": round(result.signals.margin, 4),
                "ood_flagged": decision.ood_flagged,
            },
            "domain_gate": {
                "status": domain_gate.status,
                "note": domain_gate.note,
            },
            "inference_time_ms": round(result.inference_time_ms, 2),
            "recommendation": recommendation,
        }
