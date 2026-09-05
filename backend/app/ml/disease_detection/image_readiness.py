"""
Model-readiness heuristic — ported verbatim from the reference
Smart-Farming-AI backend (backend/image_readiness.py). A classical
computer-vision heuristic (vegetation-like color mask + largest connected
component), NOT a trained segmentation model. Advisory only — the model
always sees the original resized frame, never a cropped ROI.

CALIBRATION STATUS: thresholds are not derived from paddy data (none
existed in the source workspace) — conservative by design, sanity-checked
only against non-paddy plant/non-plant photos. Treat "unsuitable"/
"borderline" verdicts as advisory.
"""

from dataclasses import dataclass, field
from typing import List

import numpy as np
from PIL import Image

from app.ml.disease_detection.config import (
    READINESS_MIN_COMPONENT_RATIO_SUITABLE,
    READINESS_MIN_COMPONENT_RATIO_UNSUITABLE,
    READINESS_MIN_VEGETATION_RATIO_SUITABLE,
    READINESS_MIN_VEGETATION_RATIO_UNSUITABLE,
    READINESS_PROXY_SIZE,
)


@dataclass
class ReadinessResult:
    status: str  # "suitable" | "borderline" | "unsuitable"
    vegetation_ratio: float
    largest_component_ratio: float
    reasons: List[str] = field(default_factory=list)
    guidance: List[str] = field(default_factory=list)


def _vegetation_like_mask(hsv: np.ndarray) -> np.ndarray:
    hue_deg = hsv[:, :, 0].astype(np.float32) / 255.0 * 360.0
    sat = hsv[:, :, 1].astype(np.float32) / 255.0
    val = hsv[:, :, 2].astype(np.float32) / 255.0

    hue_ok = (hue_deg >= 25.0) & (hue_deg <= 165.0)
    sat_ok = sat >= 0.15
    val_ok = (val >= 0.08) & (val <= 0.97)

    return hue_ok & sat_ok & val_ok


def _largest_connected_component_ratio(mask: np.ndarray) -> float:
    h, w = mask.shape
    visited = np.zeros_like(mask, dtype=bool)
    best_size = 0
    total = h * w

    for start_y in range(h):
        for start_x in range(w):
            if not mask[start_y, start_x] or visited[start_y, start_x]:
                continue

            stack = [(start_y, start_x)]
            visited[start_y, start_x] = True
            size = 0

            while stack:
                y, x = stack.pop()
                size += 1
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        stack.append((ny, nx))

            if size > best_size:
                best_size = size

    return best_size / total if total else 0.0


def assess_readiness(image: Image.Image) -> ReadinessResult:
    proxy = image.convert("RGB").resize((READINESS_PROXY_SIZE, READINESS_PROXY_SIZE))
    hsv = np.asarray(proxy.convert("HSV"))

    mask = _vegetation_like_mask(hsv)
    vegetation_ratio = round(float(mask.mean()), 4)
    largest_component_ratio = round(_largest_connected_component_ratio(mask), 4)

    reasons: List[str] = []
    guidance: List[str] = []

    if (
        vegetation_ratio < READINESS_MIN_VEGETATION_RATIO_UNSUITABLE
        or largest_component_ratio < READINESS_MIN_COMPONENT_RATIO_UNSUITABLE
    ):
        status = "unsuitable"
        reasons.append("Little to no leaf-like plant material was detected in the frame.")
        guidance.extend(
            [
                "Move closer to the leaf and make sure it is the main subject.",
                "Make sure the leaf occupies most of the frame.",
                "Avoid excessive background (soil, sky, hands, other objects).",
            ]
        )
    elif (
        vegetation_ratio < READINESS_MIN_VEGETATION_RATIO_SUITABLE
        or largest_component_ratio < READINESS_MIN_COMPONENT_RATIO_SUITABLE
    ):
        status = "borderline"
        reasons.append("A plant-like region was found but it may be small or partly out of frame.")
        guidance.extend(
            [
                "Try moving closer so the leaf fills more of the frame.",
                "Keep one or two leaves as the main subject rather than the whole plant.",
            ]
        )
    else:
        status = "suitable"

    return ReadinessResult(
        status=status,
        vegetation_ratio=vegetation_ratio,
        largest_component_ratio=largest_component_ratio,
        reasons=reasons,
        guidance=guidance,
    )
