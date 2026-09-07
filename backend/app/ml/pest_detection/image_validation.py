"""Pre-inference image validation.

Deliberately permissive: agricultural photos taken outdoors are often
imperfect (harsh sun, shade, motion). We only flag images that would make
detection meaningless, and we distinguish "unusable" (INVALID_IMAGE) from
"usable but questionable" (a quality warning attached to a normal result).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.ml.pest_detection.config import settings


class InvalidImageError(Exception):
    """Raised when an image cannot be used for inference at all."""


@dataclass
class QualityReport:
    warnings: list[str] = field(default_factory=list)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


def decode_image_bytes(data: bytes) -> np.ndarray:
    """Decode raw bytes into a BGR numpy array, raising InvalidImageError on failure."""
    import cv2

    if not data:
        raise InvalidImageError("Empty file: no image data provided.")
    if len(data) > settings.max_upload_bytes:
        raise InvalidImageError(
            f"File too large: {len(data)} bytes exceeds limit of "
            f"{settings.max_upload_bytes} bytes."
        )

    array = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError(
            "Could not decode image. File is corrupted or not a supported format."
        )
    return image


def validate_dimensions(image: np.ndarray) -> None:
    height, width = image.shape[:2]
    if height < settings.min_image_dimension or width < settings.min_image_dimension:
        raise InvalidImageError(
            f"Image too small ({width}x{height}); minimum is "
            f"{settings.min_image_dimension}px on each side."
        )
    if height > settings.max_image_dimension or width > settings.max_image_dimension:
        raise InvalidImageError(
            f"Image too large ({width}x{height}); maximum is "
            f"{settings.max_image_dimension}px on each side."
        )


def assess_quality(image: np.ndarray) -> QualityReport:
    """Flag (but do not reject) images that may produce unreliable detections."""
    import cv2

    report = QualityReport()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    mean_intensity = float(gray.mean())
    std_intensity = float(gray.std())

    if std_intensity < 2.0:
        report.warnings.append("Image appears blank or near-uniform in color.")
        return report

    if mean_intensity < settings.dark_pixel_mean_threshold:
        report.warnings.append("Image appears extremely dark.")
    elif mean_intensity > settings.bright_pixel_mean_threshold:
        report.warnings.append("Image appears extremely bright / overexposed.")

    blur_variance = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    if blur_variance < settings.blur_variance_threshold:
        report.warnings.append("Image appears severely blurred.")

    return report


def validate_and_load(data: bytes) -> tuple[np.ndarray, QualityReport]:
    """Full validation pipeline: decode -> dimension check -> quality assessment.

    Raises InvalidImageError for unusable images. Returns (image, quality_report)
    for usable images, where quality_report may still carry warnings.
    """
    image = decode_image_bytes(data)
    validate_dimensions(image)
    quality = assess_quality(image)
    return image, quality
