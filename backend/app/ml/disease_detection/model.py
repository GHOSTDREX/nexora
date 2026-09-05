"""
Model construction and checkpoint loading — ported verbatim from the
reference Smart-Farming-AI backend (backend/model.py).

    model = torchvision.models.mobilenet_v3_small(weights=...)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)

Checkpoint is a dict with keys: epoch, model_state_dict, optimizer_state_dict,
classes, num_classes, val_loss, val_accuracy. Only "model_state_dict" and
"classes" are needed for inference; loading is strict=True.
"""

import logging

import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_small

from app.ml.disease_detection.config import CLASS_NAMES, NUM_CLASSES

logger = logging.getLogger("agrinova.disease_detection")


class ModelLoadError(RuntimeError):
    pass


def build_architecture(num_classes: int = NUM_CLASSES) -> nn.Module:
    model = mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    return model


def load_checkpoint(checkpoint_path, device: str = "cpu"):
    """Returns (model, checkpoint_metadata). Raises ModelLoadError on any
    structural mismatch instead of silently continuing."""
    if not checkpoint_path.exists():
        raise ModelLoadError(f"Checkpoint not found at {checkpoint_path}")

    try:
        checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    except Exception as exc:  # noqa: BLE001 - surface exact torch.load failure
        raise ModelLoadError(f"torch.load failed for {checkpoint_path}: {exc}") from exc

    if not isinstance(checkpoint, dict) or "model_state_dict" not in checkpoint:
        raise ModelLoadError(
            f"Unexpected checkpoint structure at {checkpoint_path}: "
            f"expected a dict with 'model_state_dict', got keys="
            f"{list(checkpoint.keys()) if isinstance(checkpoint, dict) else type(checkpoint)}"
        )

    checkpoint_classes = checkpoint.get("classes")
    if checkpoint_classes is not None and list(checkpoint_classes) != CLASS_NAMES:
        raise ModelLoadError(
            "Checkpoint class list does not match config.CLASS_NAMES. "
            f"Checkpoint: {checkpoint_classes}\nConfigured: {CLASS_NAMES}\n"
            "Refusing to load — class mapping mismatch would silently mislabel predictions."
        )

    num_classes = checkpoint.get("num_classes", NUM_CLASSES)
    model = build_architecture(num_classes=num_classes)

    result = model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    missing = getattr(result, "missing_keys", [])
    unexpected = getattr(result, "unexpected_keys", [])
    if missing or unexpected:
        raise ModelLoadError(
            f"Checkpoint state dict mismatch. missing_keys={missing} unexpected_keys={unexpected}"
        )

    model.to(device)
    model.eval()

    metadata = {
        "epoch": checkpoint.get("epoch"),
        "val_loss": checkpoint.get("val_loss"),
        "val_accuracy": checkpoint.get("val_accuracy"),
        "checkpoint_path": str(checkpoint_path),
        "device": device,
    }

    logger.info(
        "Loaded paddy disease checkpoint from %s (epoch=%s, val_accuracy=%s) on device=%s",
        checkpoint_path, metadata["epoch"], metadata["val_accuracy"], device,
    )

    return model, metadata
