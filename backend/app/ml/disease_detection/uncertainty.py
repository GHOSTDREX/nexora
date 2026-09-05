"""
Uncertainty signals derived from the same calibrated softmax output the
inference pipeline already computes — ported verbatim from the reference
Smart-Farming-AI backend (backend/uncertainty.py). No new model, no
retraining, no change to the trained checkpoint.
"""

import math
from dataclasses import dataclass

import torch


@dataclass
class UncertaintySignals:
    confidence: float          # max calibrated probability
    entropy: float             # raw Shannon entropy, nats
    normalized_entropy: float  # entropy / log(num_classes), in [0, 1]
    margin: float              # p(top1) - p(top2)


def compute_uncertainty_signals(probabilities: torch.Tensor) -> UncertaintySignals:
    """probabilities: 1D tensor of calibrated per-class probabilities (sums to 1)."""
    probs = probabilities.clamp(min=1e-12)
    entropy = float(-(probs * probs.log()).sum())
    max_entropy = math.log(probabilities.numel())
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0

    sorted_probs, _ = torch.sort(probabilities, descending=True)
    confidence = float(sorted_probs[0])
    margin = float(sorted_probs[0] - sorted_probs[1]) if sorted_probs.numel() > 1 else confidence

    return UncertaintySignals(
        confidence=confidence,
        entropy=entropy,
        normalized_entropy=normalized_entropy,
        margin=margin,
    )
