"""
Deterministic inference pipeline — ported verbatim from the reference
Smart-Farming-AI backend (backend/inference.py): preprocess -> model ->
temperature scaling -> softmax -> top-3 -> confidence threshold.

Preprocessing matches the training notebook's eval_transform exactly:
Resize((224, 224)) -> ToTensor() -> Normalize(ImageNet mean/std). No
augmentation (flip/rotation/color-jitter) at inference time. Images are
always loaded via PIL's .convert("RGB") — same as the training dataset
class — so channel order matches training.
"""

import time
from dataclasses import dataclass
from typing import List

import torch
from PIL import Image
from torchvision import transforms

from app.ml.disease_detection.config import (
    CLASS_DISPLAY_NAMES,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    TEMPERATURE,
)
from app.ml.disease_detection.uncertainty import UncertaintySignals, compute_uncertainty_signals

_eval_transform = transforms.Compose(
    [
        transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ]
)


@dataclass
class ClassScore:
    class_name: str
    display_name: str
    confidence: float


@dataclass
class PredictionResult:
    prediction: str
    display_name: str
    confidence: float
    accepted: bool  # raw confidence >= threshold only; final gate is decision.decide()
    top3: List[ClassScore]
    inference_time_ms: float
    signals: UncertaintySignals


def preprocess(image: Image.Image) -> torch.Tensor:
    rgb_image = image.convert("RGB")
    tensor = _eval_transform(rgb_image)
    return tensor.unsqueeze(0)  # add batch dimension


@torch.no_grad()
def predict(model: torch.nn.Module, image: Image.Image, device: str = "cpu") -> PredictionResult:
    start = time.perf_counter()

    input_tensor = preprocess(image).to(device)

    logits = model(input_tensor)
    scaled_logits = logits / TEMPERATURE
    probabilities = torch.softmax(scaled_logits, dim=1)[0]

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    top_probs, top_indices = torch.topk(probabilities, k=3)
    top3 = [
        ClassScore(
            class_name=CLASS_NAMES[idx],
            display_name=CLASS_DISPLAY_NAMES[CLASS_NAMES[idx]],
            confidence=float(prob),
        )
        for prob, idx in zip(top_probs.tolist(), top_indices.tolist())
    ]

    best = top3[0]
    accepted = best.confidence >= CONFIDENCE_THRESHOLD
    signals = compute_uncertainty_signals(probabilities)

    return PredictionResult(
        prediction=best.class_name,
        display_name=best.display_name,
        confidence=best.confidence,
        accepted=accepted,
        top3=top3,
        inference_time_ms=elapsed_ms,
        signals=signals,
    )
