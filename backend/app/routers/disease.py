import io
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

from app.db.models import Farm
from app.deps import get_current_farm
from app.ml.disease_detection import config
from app.ml.disease_detection.detector import DetectorLoadError, DiseaseDetector

logger = logging.getLogger("agrinova.disease_detection")
router = APIRouter(prefix="/api/disease", tags=["disease"])

try:
    detector = DiseaseDetector()
    _load_error: str | None = None
except DetectorLoadError as exc:
    logger.error("Disease detection model failed to load: %s", exc)
    detector = None
    _load_error = str(exc)


def _require_detector() -> DiseaseDetector:
    if detector is None:
        raise HTTPException(status_code=503, detail=f"Disease detection model unavailable: {_load_error}")
    return detector


@router.get("/model-info")
def model_info(farm: Farm = Depends(get_current_farm)):
    return _require_detector().model_info()


@router.post("/predict")
async def predict_disease(file: UploadFile = File(...), farm: Farm = Depends(get_current_farm)):
    det = _require_detector()

    if file.content_type not in config.ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported content type '{file.content_type}'. Allowed: JPG, PNG, WEBP.",
        )

    raw_bytes = await file.read()

    if len(raw_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(raw_bytes) > config.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.",
        )

    try:
        image = Image.open(io.BytesIO(raw_bytes))
        image.load()
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="File could not be decoded as a valid image.")
    except Exception:
        raise HTTPException(status_code=400, detail="File could not be decoded as a valid image.")

    try:
        return det.predict(image, raw_bytes)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Disease detection inference failed")
        raise HTTPException(status_code=500, detail="Inference failed.") from exc
