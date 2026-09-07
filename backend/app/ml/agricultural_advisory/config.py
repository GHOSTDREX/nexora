"""Centralized, environment-overridable configuration for the advisory engine.

Versioning note (see docs/AGRICULTURAL_ADVISORY.md, section "Versioning"):
the ML models, the knowledge base, and the rule set are versioned
independently. Editing a rule or adding a knowledge-base entry does not
require retraining any model, and vice versa.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
KNOWLEDGE_BASE_DIR = PACKAGE_ROOT / "knowledge_base"

ADVISORY_ENGINE_VERSION = "1.0.0"
KNOWLEDGE_BASE_VERSION = "1.0.0"
RULE_SET_VERSION = "1.0.0"


def _env_float(name: str, default: float) -> float:
    value = os.environ.get(name)
    return float(value) if value else default


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def _env_path(name: str, default: Path) -> Path:
    value = os.environ.get(name)
    return Path(value) if value else default


@dataclass(frozen=True)
class SensorRange:
    """Plausible physical range for a sensor/weather reading, used for OUT_OF_RANGE checks."""

    minimum: float
    maximum: float
    unit: str


@dataclass(frozen=True)
class Settings:
    # --- Disease model gating ---------------------------------------------
    # This threshold mirrors the production acceptance threshold stated for
    # the (not yet integrated) Paddy Doctor disease model. It is recorded
    # here as project specification, not independently re-validated against
    # a live model, since no disease model artifact exists in this repo yet.
    disease_confidence_threshold: float = field(
        default_factory=lambda: _env_float("ADVISORY_DISEASE_CONFIDENCE_THRESHOLD", 0.90)
    )

    # --- Data freshness -----------------------------------------------------
    sensor_stale_after_seconds: int = field(
        default_factory=lambda: _env_int("ADVISORY_SENSOR_STALE_SECONDS", 24 * 3600)
    )
    weather_stale_after_seconds: int = field(
        default_factory=lambda: _env_int("ADVISORY_WEATHER_STALE_SECONDS", 6 * 3600)
    )

    # --- Temporal / trend reasoning ------------------------------------------
    # A relative-change heuristic, not a statistical/epidemiological model.
    trend_increase_ratio: float = field(
        default_factory=lambda: _env_float("ADVISORY_TREND_INCREASE_RATIO", 1.2)
    )
    trend_decrease_ratio: float = field(
        default_factory=lambda: _env_float("ADVISORY_TREND_DECREASE_RATIO", 0.8)
    )
    min_observations_for_trend: int = field(
        default_factory=lambda: _env_int("ADVISORY_MIN_OBS_FOR_TREND", 2)
    )

    # --- Pest field-risk thresholds (distinct from pest_detection's
    # single-image severity heuristic; this folds in trend + context) ------
    pest_risk_moderate_score: float = field(
        default_factory=lambda: _env_float("ADVISORY_PEST_RISK_MODERATE", 0.35)
    )
    pest_risk_high_score: float = field(
        default_factory=lambda: _env_float("ADVISORY_PEST_RISK_HIGH", 0.65)
    )

    # --- History store (local, offline, append-only JSONL) -------------------
    history_path: Path = field(
        default_factory=lambda: _env_path(
            "ADVISORY_HISTORY_PATH", PACKAGE_ROOT / "data" / "history.jsonl"
        )
    )
    history_lookback: int = field(
        default_factory=lambda: _env_int("ADVISORY_HISTORY_LOOKBACK", 10)
    )

    # --- Plausible sensor/weather ranges (OUT_OF_RANGE detection) -----------
    sensor_ranges: dict = field(
        default_factory=lambda: {
            "soil_moisture": SensorRange(0.0, 100.0, "%"),
            "soil_temperature": SensorRange(-10.0, 60.0, "C"),
            "air_temperature": SensorRange(-10.0, 55.0, "C"),
            "humidity": SensorRange(0.0, 100.0, "%"),
            "rainfall": SensorRange(0.0, 1000.0, "mm"),
        }
    )


settings = Settings()
