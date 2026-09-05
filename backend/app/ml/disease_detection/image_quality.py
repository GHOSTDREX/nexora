"""
Basic image-quality assessment — ported verbatim from the reference
Smart-Farming-AI backend (backend/image_quality.py). NOT a disease detector
and does NOT verify the image contains a paddy leaf; only checks generic
technical properties (resolution, brightness, blur/focus).
"""

from dataclasses import dataclass, field
from typing import List

import numpy as np
from PIL import Image

MIN_USABLE_DIMENSION = 224
VERY_SMALL_DIMENSION = 96

DARK_BRIGHTNESS_THRESHOLD = 0.15
BRIGHT_BRIGHTNESS_THRESHOLD = 0.90

BLUR_POOR_THRESHOLD = 15.0
BLUR_WARNING_THRESHOLD = 60.0

_LAPLACIAN_KERNEL = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)


def _laplacian_variance(gray: np.ndarray) -> float:
    h, w = gray.shape
    if h < 3 or w < 3:
        return 0.0

    out = np.zeros((h - 2, w - 2), dtype=np.float32)
    for (dy, dx), weight in np.ndenumerate(_LAPLACIAN_KERNEL):
        if weight == 0:
            continue
        out += weight * gray[dy : dy + h - 2, dx : dx + w - 2]

    return float(out.var())


@dataclass
class QualityResult:
    status: str  # "good" | "warning" | "poor"
    brightness: float
    blur_score: float
    width: int
    height: int
    megapixels: float
    reasons: List[str] = field(default_factory=list)


def assess_quality(image: Image.Image) -> QualityResult:
    width, height = image.size
    megapixels = round((width * height) / 1_000_000, 2)

    gray = np.asarray(image.convert("L"), dtype=np.float32)
    brightness = round(float(gray.mean() / 255.0), 4)
    blur_score = round(_laplacian_variance(gray), 2)

    reasons: List[str] = []
    status = "good"

    if min(width, height) < VERY_SMALL_DIMENSION:
        status = "poor"
        reasons.append(f"Image is very small ({width}x{height}px).")
    elif min(width, height) < MIN_USABLE_DIMENSION:
        status = "warning"
        reasons.append(
            f"Image resolution ({width}x{height}px) is below the model's "
            f"input size ({MIN_USABLE_DIMENSION}x{MIN_USABLE_DIMENSION}px); "
            "it will be upscaled, which may reduce detail."
        )

    if brightness < DARK_BRIGHTNESS_THRESHOLD / 2:
        status = "poor"
        reasons.append("Image appears extremely dark.")
    elif brightness < DARK_BRIGHTNESS_THRESHOLD:
        status = max(status, "warning", key=_severity)
        reasons.append("Image appears very dark.")
    elif brightness > BRIGHT_BRIGHTNESS_THRESHOLD:
        status = max(status, "warning", key=_severity)
        reasons.append("Image appears overexposed / very bright.")

    if blur_score < BLUR_POOR_THRESHOLD:
        status = max(status, "warning", key=_severity)
        reasons.append("Image appears very blurry or out of focus.")
    elif blur_score < BLUR_WARNING_THRESHOLD:
        status = max(status, "warning", key=_severity)
        reasons.append("Image may be slightly out of focus.")

    return QualityResult(
        status=status,
        brightness=brightness,
        blur_score=blur_score,
        width=width,
        height=height,
        megapixels=megapixels,
        reasons=reasons,
    )


def _severity(level: str) -> int:
    return {"good": 0, "warning": 1, "poor": 2}[level]
