"""Pest detection — ported from AGRINOVA_PEST_INTEGRATION/pest_detection/api.py.

That package shipped as its own standalone FastAPI app; here it's an
APIRouter mounted into the main app (see app/main.py), with the same
Depends(get_current_farm) auth gate every other route in this backend uses.
The detection logic itself (app/ml/pest_detection/detector.py) is
unmodified — only the HTTP wiring changed.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.db.models import Farm
from app.deps import get_current_farm
from app.ml.pest_detection.config import PROJECT_ROOT, settings
from app.ml.pest_detection.detector import ModelLoadError, get_detector
from app.ml.pest_detection.logging_config import get_logger
from app.ml.pest_detection.schemas import ResultStatus

logger = get_logger()

router = APIRouter(prefix="/api/pest", tags=["pest"])

_ANNOTATED_DIR = settings.model_path.parent.parent / "inference_results" / "api_annotated"

try:
    get_detector()
except ModelLoadError as exc:
    logger.error("Failed to load pest detection model at import time: %s", exc)


def _validate_filename(filename: str | None) -> str:
    if not filename:
        return "upload"
    from pathlib import Path
    return Path(filename).name or "upload"


@router.get("/model-info")
def model_info(farm: Farm = Depends(get_current_farm)) -> dict:
    detector = get_detector()
    try:
        model_ref = str(detector.model_path.relative_to(PROJECT_ROOT))
    except ValueError:
        model_ref = detector.model_path.name
    return {
        "model_reference": model_ref,
        "confidence_threshold": detector.confidence,
        "iou_threshold": detector.iou,
        "supported_classes": detector.class_names,
        "limitations": [
            "Supports exactly 12 pest classes; unsupported real-world pests are never returned.",
            "Trained on IP102-derived data; real-world performance may differ.",
            "Small or heavily occluded insects may be missed.",
            "Visually similar pests may be confused.",
            "Confidence is a model score, not a calibrated probability.",
            "Severity is an image-level heuristic, not a field-wide infestation measurement.",
        ],
    }


@router.post("/detect")
async def detect_pests(image: UploadFile = File(...), farm: Farm = Depends(get_current_farm)) -> JSONResponse:
    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    filename = _validate_filename(image.filename)
    data = await image.read()

    detector = get_detector()
    try:
        result = detector.detect(data, filename=filename)
    except Exception as exc:  # noqa: BLE001 - never leak raw tracebacks to clients
        logger.error("INFERENCE_ERROR filename=%s error=%s", filename, exc)
        raise HTTPException(status_code=500, detail="Pest detection failed unexpectedly.") from exc

    status_code = 400 if result.status == ResultStatus.INVALID_IMAGE else 200
    return JSONResponse(status_code=status_code, content=result.to_dict())


@router.post("/detect/annotated")
async def detect_pests_annotated(image: UploadFile = File(...), farm: Farm = Depends(get_current_farm)) -> FileResponse:
    """Returns the annotated image (boxes + labels) as a PNG file."""
    import cv2

    content_type = image.content_type or ""
    if not content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    data = await image.read()
    detector = get_detector()

    try:
        annotated = detector.render_annotated(data)
    except Exception as exc:  # noqa: BLE001 - never leak raw tracebacks/paths to clients
        logger.warning("ANNOTATED_RENDER_FAILED error=%s", exc)
        raise HTTPException(status_code=400, detail="Could not process this image.") from exc

    _ANNOTATED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = _ANNOTATED_DIR / f"{uuid.uuid4().hex}.png"
    cv2.imwrite(str(out_path), annotated)

    return FileResponse(out_path, media_type="image/png")
