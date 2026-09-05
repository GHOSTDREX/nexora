"""
Augmentation-strengthened fine-tune of the paddy disease checkpoint.

NOT run automatically and NOT part of the serving app — a one-off script,
same convention as app/ml/crop_recommendation/train.py. Invoked manually:

    python -m app.ml.disease_detection.train

What this does and does not do, by design:
  - Warm-starts from the EXISTING paddy_mobilenetv3_best.pth (fine-tune,
    not retrain-from-scratch) — faster convergence, lower risk of
    regressing what already works, appropriate for CPU-only training.
  - Trains on the SAME dataset the checkpoint already saw (no new
    real-world photos exist in this workspace) — this cannot teach the
    model anything it hasn't seen. What it CAN do is make the model more
    tolerant of photographic variation (crop/zoom, lighting, blur,
    sharpening, color balance) via heavier train-time augmentation than
    the original notebook used, which is the only lever available without
    new data.
  - Reuses the exact stratified 70/15/15 split (seed=42) and class-weighted
    loss from the reference training notebook, so val/test accuracy stays
    comparable to the historical numbers in calibration.json.
  - Recalibrates temperature (NLL minimization on the validation set) at
    the SAME confidence_threshold=0.90 policy — does not change the
    accept/reject philosophy, only re-fits it to the new weights.
  - Never overwrites paddy_mobilenetv3_best.pth or calibration.json.
    Writes paddy_mobilenetv3_finetuned.pth / calibration_finetuned.json
    alongside them. Promoting the result to serving is a separate,
    explicit step after reviewing the comparison report this prints.
"""

import json
import time
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import mobilenet_v3_small

from app.ml.disease_detection.config import (
    BEST_CHECKPOINT_PATH,
    CLASS_NAMES,
    CONFIDENCE_THRESHOLD,
    IMAGE_SIZE,
    IMAGENET_MEAN,
    IMAGENET_STD,
    MODELS_DIR,
    NUM_CLASSES,
)

# --- External dataset location (not copied into the repo — 2.1GB, the
# same data the checkpoint already trained on; see module docstring). ---
DATASET_DIR = Path(__file__).resolve().parents[4] / "Smart-Farming-AI" / "datasets" / "paddy-disease-classification"
TRAIN_CSV = DATASET_DIR / "train.csv"
TRAIN_IMAGES_DIR = DATASET_DIR / "train_images"

OUT_CHECKPOINT = MODELS_DIR / "paddy_mobilenetv3_finetuned.pth"
OUT_CALIBRATION = MODELS_DIR / "calibration_finetuned.json"
OUT_REPORT = MODELS_DIR / "finetune_report.json"

SEED = 42
BATCH_SIZE = 32
EPOCHS = 10
LEARNING_RATE = 3e-5  # lower than the original 1e-4 — warm-start, not from-scratch
WEIGHT_DECAY = 1e-4

torch.manual_seed(SEED)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

def build_splits() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = pd.read_csv(TRAIN_CSV)
    df["image_path"] = df.apply(lambda r: str(TRAIN_IMAGES_DIR / r["label"] / r["image_id"]), axis=1)

    train_df, temp_df = train_test_split(df, test_size=0.30, stratify=df["label"], random_state=SEED)
    val_df, test_df = train_test_split(temp_df, test_size=0.50, stratify=temp_df["label"], random_state=SEED)
    return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)


class PaddyDataset(Dataset):
    def __init__(self, dataframe: pd.DataFrame, class_to_idx: dict, transform):
        self.df = dataframe
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, index):
        row = self.df.iloc[index]
        image = Image.open(row["image_path"]).convert("RGB")
        label = self.class_to_idx[row["label"]]
        return self.transform(image), label


# Stronger than the reference notebook's train_transform (flip + rotate(15)
# + color jitter(0.2)) — adds random-resized-crop (zoom/framing variation),
# blur, sharpness and autocontrast jitter to simulate different cameras/
# focus/lighting, since that photographic variation — not new diseases —
# is the gap real-world photos exposed. Hue jitter stays small since lesion
# color is diagnostic. eval_transform is UNCHANGED from inference.py so
# val/test accuracy stays comparable and calibration stays valid.
train_transform = transforms.Compose([
    transforms.RandomResizedCrop(IMAGE_SIZE, scale=(0.7, 1.0)),
    transforms.RandomHorizontalFlip(p=0.5),
    transforms.RandomRotation(degrees=20),
    transforms.ColorJitter(brightness=0.35, contrast=0.35, saturation=0.35, hue=0.05),
    transforms.RandomApply([transforms.GaussianBlur(kernel_size=5, sigma=(0.1, 2.0))], p=0.3),
    transforms.RandomAdjustSharpness(sharpness_factor=2, p=0.3),
    transforms.RandomAutocontrast(p=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])

eval_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
])


# ---------------------------------------------------------------------------
# Train / eval loops (structurally identical to the reference notebook)
# ---------------------------------------------------------------------------

def train_one_epoch(model, loader, criterion, optimizer, device) -> tuple[float, float]:
    model.train()
    running_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        running_loss += loss.item() * images.size(0)
        correct += (outputs.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)
    return running_loss / total, correct / total


@torch.no_grad()
def evaluate(model, loader, criterion, device) -> tuple[float, float]:
    model.eval()
    running_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)
        running_loss += loss.item() * images.size(0)
        correct += (outputs.argmax(dim=1) == labels).sum().item()
        total += labels.size(0)
    return running_loss / total, correct / total


@torch.no_grad()
def collect_logits(model, loader, device):
    model.eval()
    all_logits, all_labels = [], []
    for images, labels in loader:
        all_logits.append(model(images.to(device)).cpu())
        all_labels.append(labels)
    return torch.cat(all_logits), torch.cat(all_labels)


def fit_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Standard single-scalar temperature scaling via NLL minimization (LBFGS)."""
    temperature = torch.ones(1, requires_grad=True)
    optimizer = torch.optim.LBFGS([temperature], lr=0.01, max_iter=50)
    nll = nn.CrossEntropyLoss()

    def closure():
        optimizer.zero_grad()
        loss = nll(logits / temperature, labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(temperature.detach().clamp(min=0.05))


def accepted_metrics(logits: torch.Tensor, labels: torch.Tensor, temperature: float, threshold: float) -> dict:
    probs = torch.softmax(logits / temperature, dim=1)
    confidences, predictions = probs.max(dim=1)
    accepted = confidences >= threshold
    n_accepted = int(accepted.sum())
    accepted_correct = int((predictions[accepted] == labels[accepted]).sum()) if n_accepted else 0
    return {
        "accepted_rate": n_accepted / len(labels),
        "accepted_accuracy": (accepted_correct / n_accepted) if n_accepted else 0.0,
        "overall_accuracy": float((predictions == labels).float().mean()),
    }


def main():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Device: {device}")

    train_df, val_df, test_df = build_splits()
    classes = sorted(train_df["label"].unique())
    assert classes == CLASS_NAMES, f"Split classes {classes} != config.CLASS_NAMES {CLASS_NAMES}"
    class_to_idx = {c: i for i, c in enumerate(classes)}
    print(f"Train/val/test sizes: {len(train_df)}/{len(val_df)}/{len(test_df)}")

    train_loader = DataLoader(PaddyDataset(train_df, class_to_idx, train_transform), batch_size=BATCH_SIZE, shuffle=True, num_workers=0)
    val_loader = DataLoader(PaddyDataset(val_df, class_to_idx, eval_transform), batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader = DataLoader(PaddyDataset(test_df, class_to_idx, eval_transform), batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    class_counts = train_df["label"].value_counts().reindex(classes)
    class_weights = torch.tensor(len(train_df) / (len(classes) * class_counts.values), dtype=torch.float32)
    criterion = nn.CrossEntropyLoss(weight=class_weights.to(device))

    model = mobilenet_v3_small(weights=None)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, NUM_CLASSES)
    checkpoint = torch.load(BEST_CHECKPOINT_PATH, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.to(device)
    print(f"Warm-started from {BEST_CHECKPOINT_PATH} (epoch={checkpoint.get('epoch')}, val_acc={checkpoint.get('val_accuracy')})")

    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.3, patience=2)

    best_val_loss = float("inf")
    history = {"train_loss": [], "train_accuracy": [], "val_loss": [], "val_accuracy": []}

    for epoch in range(EPOCHS):
        t0 = time.time()
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = evaluate(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        history["train_loss"].append(train_loss)
        history["train_accuracy"].append(train_acc)
        history["val_loss"].append(val_loss)
        history["val_accuracy"].append(val_acc)

        elapsed = time.time() - t0
        print(f"Epoch {epoch + 1}/{EPOCHS}  train_loss={train_loss:.4f} train_acc={train_acc:.4f} "
              f"val_loss={val_loss:.4f} val_acc={val_acc:.4f}  ({elapsed:.0f}s)", flush=True)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch": epoch + 1,
                "model_state_dict": model.state_dict(),
                "classes": classes,
                "num_classes": NUM_CLASSES,
                "val_loss": val_loss,
                "val_accuracy": val_acc,
                "base_checkpoint": str(BEST_CHECKPOINT_PATH),
            }, OUT_CHECKPOINT)
            print(f"  -> saved new best to {OUT_CHECKPOINT}", flush=True)

    # Recalibrate on the best fine-tuned checkpoint.
    best = torch.load(OUT_CHECKPOINT, map_location=device, weights_only=False)
    model.load_state_dict(best["model_state_dict"])
    model.to(device)

    val_logits, val_labels = collect_logits(model, val_loader, device)
    temperature = fit_temperature(val_logits, val_labels)

    test_logits, test_labels = collect_logits(model, test_loader, device)
    test_metrics_uncalibrated = accepted_metrics(test_logits, test_labels, temperature=1.0, threshold=CONFIDENCE_THRESHOLD)
    test_metrics = accepted_metrics(test_logits, test_labels, temperature=temperature, threshold=CONFIDENCE_THRESHOLD)

    calibration = {
        "temperature": round(temperature, 4),
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "validation_accuracy": round(history["val_accuracy"][-1], 4),
        "accepted_rate": round(test_metrics["accepted_rate"], 4),
        "accepted_accuracy": round(test_metrics["accepted_accuracy"], 4),
        "test_accuracy": round(test_metrics["overall_accuracy"], 4),
        "model": "MobileNetV3 Small (fine-tuned, augmented)",
        "image_size": IMAGE_SIZE,
        "base_checkpoint": str(BEST_CHECKPOINT_PATH),
    }
    with open(OUT_CALIBRATION, "w", encoding="utf-8") as f:
        json.dump(calibration, f, indent=2)

    report = {
        "history": history,
        "best_epoch": best["epoch"],
        "temperature": temperature,
        "test_metrics_at_threshold": test_metrics,
        "test_metrics_uncalibrated_temp1": test_metrics_uncalibrated,
        "reference_calibration_for_comparison": json.loads((MODELS_DIR / "calibration.json").read_text()),
        "checkpoint_path": str(OUT_CHECKPOINT),
        "calibration_path": str(OUT_CALIBRATION),
    }
    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n=== DONE ===")
    print(json.dumps({"new": calibration, "reference": report["reference_calibration_for_comparison"]}, indent=2))


if __name__ == "__main__":
    main()
