"""Centralized, environment-overridable configuration.

Nothing else in this package should hard-code a model path, threshold, or
severity cutoff. Change behavior here (or via environment variables).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Package-relative (not the original integration package's PROJECT_ROOT,
# which was one level up from pest_detection/ — here the package now owns
# its own models/ subfolder directly, same as app.ml.disease_detection).
PROJECT_ROOT = Path(__file__).resolve().parent


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


@dataclass(frozen=True)
class SeverityThresholds:
    """Cutoffs for the image-level infestation heuristic. See pest_detection/severity.py."""

    moderate_score: float = field(
        default_factory=lambda: _env_float("PEST_SEVERITY_MODERATE_SCORE", 0.35)
    )
    high_score: float = field(
        default_factory=lambda: _env_float("PEST_SEVERITY_HIGH_SCORE", 0.65)
    )


@dataclass(frozen=True)
class Settings:
    model_path: Path = field(
        default_factory=lambda: _env_path(
            "PEST_MODEL_PATH", PROJECT_ROOT / "models" / "best.pt"
        )
    )
    # Raised from the model's raw training-default of 0.25: at that level the
    # detector occasionally produces a weak, spurious box on completely
    # out-of-domain images (e.g. a photo of people, ~0.26 confidence) since
    # it has no "not a pest" class. This does not eliminate every possible
    # false positive on unrelated photos (no fixed threshold can, since weak
    # true and false detections overlap) — verified trade-off: it also
    # suppresses one genuine-but-weak detection in the regression set
    # (asiatic rice borer at 0.32 confidence on IP000000010.jpg), which
    # tests/test_regression.py accounts for explicitly. Chosen deliberately
    # over strict "must preserve every current detection" because the
    # far more common failure mode in practice is noise on irrelevant
    # photos, not missing a borderline-confidence real pest.
    confidence_threshold: float = field(
        default_factory=lambda: _env_float("PEST_CONFIDENCE_THRESHOLD", 0.35)
    )
    iou_threshold: float = field(
        default_factory=lambda: _env_float("PEST_IOU_THRESHOLD", 0.45)
    )
    max_image_dimension: int = field(
        default_factory=lambda: _env_int("PEST_MAX_IMAGE_DIMENSION", 8000)
    )
    min_image_dimension: int = field(
        default_factory=lambda: _env_int("PEST_MIN_IMAGE_DIMENSION", 32)
    )
    max_upload_bytes: int = field(
        default_factory=lambda: _env_int("PEST_MAX_UPLOAD_BYTES", 15 * 1024 * 1024)
    )
    dark_pixel_mean_threshold: float = field(
        default_factory=lambda: _env_float("PEST_DARK_MEAN_THRESHOLD", 20.0)
    )
    bright_pixel_mean_threshold: float = field(
        default_factory=lambda: _env_float("PEST_BRIGHT_MEAN_THRESHOLD", 235.0)
    )
    blur_variance_threshold: float = field(
        default_factory=lambda: _env_float("PEST_BLUR_VARIANCE_THRESHOLD", 15.0)
    )
    severity: SeverityThresholds = field(default_factory=SeverityThresholds)

    SUPPORTED_IMAGE_EXTENSIONS: tuple = (".jpg", ".jpeg", ".png", ".bmp")


settings = Settings()
