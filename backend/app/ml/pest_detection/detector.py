"""Pest detector service: loads the frozen YOLO model once and reuses it.

Usage:

    from pest_detection.detector import get_detector

    detector = get_detector()          # loads model on first call, cached after
    result = detector.detect(image_bytes, filename="field_001.jpg")

`get_detector()` is the intended entry point everywhere (CLI, API). It is
process-wide and thread-safe to construct, but Ultralytics' `model.predict`
itself is not guaranteed thread-safe for concurrent calls — a production
deployment serving concurrent requests should serialize calls (e.g. via a
lock or a single-worker inference process) rather than sharing one model
instance across threads unprotected.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import numpy as np

from app.ml.pest_detection.config import settings
from app.ml.pest_detection.image_validation import InvalidImageError, validate_and_load
from app.ml.pest_detection.logging_config import get_logger
from app.ml.pest_detection.schemas import (
    BoundingBox,
    Detection,
    DetectionResult,
    ImageInfo,
    ResultStatus,
    SpeciesSummary,
    TimingInfo,
)
from app.ml.pest_detection.severity import calculate_severity

logger = get_logger()


class ModelLoadError(Exception):
    """Raised when the YOLO model file cannot be loaded."""


class InferenceError(Exception):
    """Raised when the model runs but inference itself fails."""


def _group_by_species(detections: list[Detection]) -> list[SpeciesSummary]:
    by_name: dict[str, list[Detection]] = {}
    for det in detections:
        by_name.setdefault(det.name, []).append(det)

    summaries = []
    for name, dets in by_name.items():
        confidences = [d.confidence for d in dets]
        summaries.append(
            SpeciesSummary(
                name=name,
                count=len(dets),
                average_confidence=sum(confidences) / len(confidences),
                max_confidence=max(confidences),
                min_confidence=min(confidences),
            )
        )
    summaries.sort(key=lambda s: s.count, reverse=True)
    return summaries


class PestDetectorService:
    """Thin, testable wrapper around the frozen Ultralytics YOLO model."""

    def __init__(self, model_path: Path | None = None, confidence: float | None = None):
        self.model_path = Path(model_path) if model_path else settings.model_path
        self.confidence = confidence if confidence is not None else settings.confidence_threshold
        self.iou = settings.iou_threshold
        self._model = None
        self._class_names: dict[int, str] = {}

    def load(self) -> None:
        if self._model is not None:
            return

        if not self.model_path.exists():
            raise ModelLoadError(f"Model file not found: {self.model_path}")

        try:
            from ultralytics import YOLO

            self._model = YOLO(str(self.model_path))
            self._class_names = dict(self._model.names)
        except Exception as exc:  # noqa: BLE001 - surface as our own typed error
            raise ModelLoadError(f"Failed to load model from {self.model_path}: {exc}") from exc

        logger.info(
            "MODEL_LOADED path=%s classes=%d", self.model_path, len(self._class_names)
        )

    @property
    def class_names(self) -> dict[int, str]:
        self.load()
        return self._class_names

    def detect(self, image_bytes: bytes, filename: str = "upload") -> DetectionResult:
        """Run the full validate -> infer -> analyze pipeline on raw image bytes."""
        t_start = time.perf_counter()

        try:
            image, quality = validate_and_load(image_bytes)
        except InvalidImageError as exc:
            logger.warning("INVALID_IMAGE filename=%s reason=%s", filename, exc)
            return DetectionResult(status=ResultStatus.INVALID_IMAGE, message=str(exc))

        t_validated = time.perf_counter()

        height, width = image.shape[:2]
        image_info = ImageInfo(filename=filename, width=width, height=height)

        self.load()

        logger.info("INFERENCE_STARTED filename=%s size=%dx%d", filename, width, height)

        try:
            raw_results = self._model.predict(
                source=image,
                conf=self.confidence,
                iou=self.iou,
                verbose=False,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("INFERENCE_ERROR filename=%s error=%s", filename, exc)
            return DetectionResult(
                status=ResultStatus.INFERENCE_ERROR,
                image=image_info,
                message="Inference failed. See server logs for details.",
            )

        t_inferred = time.perf_counter()

        detections = self._extract_detections(raw_results)

        species = _group_by_species(detections)
        severity = calculate_severity(detections, width, height)

        t_end = time.perf_counter()
        timing = TimingInfo(
            preprocessing_ms=(t_validated - t_start) * 1000,
            inference_ms=(t_inferred - t_validated) * 1000,
            postprocessing_ms=(t_end - t_inferred) * 1000,
            total_ms=(t_end - t_start) * 1000,
        )

        if not detections:
            logger.info("NO_DETECTION filename=%s", filename)
            status = ResultStatus.NO_PEST_DETECTED
        elif quality.has_warnings:
            logger.info(
                "DETECTIONS_FOUND filename=%s count=%d quality_warnings=%s",
                filename, len(detections), quality.warnings,
            )
            status = ResultStatus.IMAGE_QUALITY_WARNING
        else:
            logger.info(
                "DETECTIONS_FOUND filename=%s count=%d", filename, len(detections)
            )
            status = ResultStatus.DETECTIONS_FOUND

        return DetectionResult(
            status=status,
            image=image_info,
            detections=detections,
            species=species,
            severity=severity,
            timing=timing,
            message="; ".join(quality.warnings) if quality.has_warnings else None,
        )

    def _extract_detections(self, raw_results) -> list[Detection]:
        detections: list[Detection] = []
        for result in raw_results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                xyxy = box.xyxy[0]
                x1, y1, x2, y2 = (float(v) for v in xyxy)
                name = self._class_names.get(class_id, f"class_{class_id}")
                detections.append(
                    Detection(
                        class_id=class_id,
                        name=name,
                        confidence=confidence,
                        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    )
                )
        return detections

    def render_annotated(self, image_bytes: bytes) -> np.ndarray:
        """Return a BGR numpy array with boxes/labels drawn, for display or saving."""
        image, _ = validate_and_load(image_bytes)
        self.load()
        raw_results = self._model.predict(
            source=image, conf=self.confidence, iou=self.iou, verbose=False
        )
        return raw_results[0].plot()


_detector_lock = threading.Lock()
_detector_instance: PestDetectorService | None = None


def get_detector() -> PestDetectorService:
    """Process-wide singleton accessor. Loads the model on first use only."""
    global _detector_instance
    if _detector_instance is None:
        with _detector_lock:
            if _detector_instance is None:
                instance = PestDetectorService()
                instance.load()
                _detector_instance = instance
    return _detector_instance
