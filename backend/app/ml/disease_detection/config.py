"""
Paddy disease detection — configuration, ported from the reference
Smart-Farming-AI backend (backend/config.py). Values are unchanged from the
reference; only paths are adjusted to live under AgriNova's own package.

Per integration instructions: only paddy_mobilenetv3_best.pth is used
(never *_latest.pth or checkpoint_320.pth), and calibration.json is loaded
verbatim, never hardcoded or edited.
"""

import json
import os
from pathlib import Path

# Reference backend's own fix for a torch/Anaconda OpenMP conflict — harmless
# no-op on a plain venv, kept as a defensive default since it costs nothing.
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

PACKAGE_DIR = Path(__file__).resolve().parent
MODELS_DIR = PACKAGE_DIR / "models"

BEST_CHECKPOINT_PATH = MODELS_DIR / "paddy_mobilenetv3_best.pth"
CALIBRATION_PATH = MODELS_DIR / "calibration.json"
RECOMMENDATIONS_PATH = PACKAGE_DIR / "recommendations.json"

# Class mapping — VERIFIED against checkpoint["classes"] in
# paddy_mobilenetv3_best.pth. DO NOT reorder.
CLASS_NAMES = [
    "bacterial_leaf_blight",
    "bacterial_leaf_streak",
    "bacterial_panicle_blight",
    "blast",
    "brown_spot",
    "dead_heart",
    "downy_mildew",
    "hispa",
    "normal",
    "tungro",
]

CLASS_DISPLAY_NAMES = {
    "bacterial_leaf_blight": "Bacterial Leaf Blight",
    "bacterial_leaf_streak": "Bacterial Leaf Streak",
    "bacterial_panicle_blight": "Bacterial Panicle Blight",
    "blast": "Blast",
    "brown_spot": "Brown Spot",
    "dead_heart": "Dead Heart",
    "downy_mildew": "Downy Mildew",
    "hispa": "Hispa",
    "normal": "Normal",
    "tungro": "Tungro",
}

NUM_CLASSES = len(CLASS_NAMES)

# Preprocessing — VERIFIED from the training notebook's eval_transform:
# Resize((224,224)) -> ToTensor() -> Normalize(ImageNet). No CenterCrop.
IMAGE_SIZE = 224
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

MODEL_NAME = "MobileNetV3 Small"
FRAMEWORK = "PyTorch"


def _load_calibration() -> dict:
    if not CALIBRATION_PATH.exists():
        raise FileNotFoundError(
            f"calibration.json not found at {CALIBRATION_PATH}. "
            "Cannot start without verified calibration values."
        )
    with open(CALIBRATION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


CALIBRATION = _load_calibration()

TEMPERATURE = float(CALIBRATION["temperature"])
CONFIDENCE_THRESHOLD = float(CALIBRATION["confidence_threshold"])
VERIFIED_VALIDATION_ACCURACY = float(CALIBRATION["validation_accuracy"])
VERIFIED_TEST_ACCURACY = float(CALIBRATION["test_accuracy"])
VERIFIED_ACCEPTED_RATE = float(CALIBRATION.get("accepted_rate", 0.0))
VERIFIED_ACCEPTED_ACCURACY = float(CALIBRATION.get("accepted_accuracy", 0.0))

# Model readiness heuristic (image_readiness.py) — classical CV, not trained
# on paddy data. Conservative by design; see that module's docstring.
READINESS_PROXY_SIZE = 96
READINESS_MIN_VEGETATION_RATIO_UNSUITABLE = 0.03
READINESS_MIN_COMPONENT_RATIO_UNSUITABLE = 0.02
READINESS_MIN_VEGETATION_RATIO_SUITABLE = 0.15
READINESS_MIN_COMPONENT_RATIO_SUITABLE = 0.08

# OOD heuristic (uncertainty.py + decision.py) — derived from a proxy
# experiment against non-paddy images, not real paddy data. See decision.py.
OOD_NORMALIZED_ENTROPY_THRESHOLD = 0.97
OOD_MARGIN_THRESHOLD = 0.04
OOD_CONFIDENCE_THRESHOLD = 0.25

# Feature flags — both True reproduces the reference's Phase-15 pipeline
# exactly. Setting both False reduces to Phase 1 (confidence-only gate).
ENABLE_READINESS_CHECK = True
ENABLE_OOD_HEURISTIC = True

# Upload limits / validation
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
