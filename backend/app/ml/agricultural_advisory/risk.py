"""Risk engines.

Each engine here computes an application-level RISK assessment — "how
concerning is the agricultural situation given available evidence" — which
is explicitly NOT the same as AI model CONFIDENCE ("how sure is the model of
its own output"). See docs/AGRICULTURAL_ADVISORY.md, "Confidence vs risk."

All thresholds are configuration (agricultural_advisory/config.py), not
inline magic numbers, and every engine is a heuristic over the evidence it
is actually given — none of them invent sensor values, weather forecasts,
or agronomic facts not present in the input.
"""

from __future__ import annotations

from typing import Optional

from app.ml.agricultural_advisory.config import settings
from app.ml.agricultural_advisory.schemas import (
    DataQuality,
    Observation,
    RiskAssessment,
    RiskCategory,
    RiskLevel,
    TrendDirection,
    TrendResult,
)

_COUNT_SATURATION = 8  # detections at/above this count contribute full weight to the count factor


def _trend_factor(trend: TrendResult) -> float:
    return {
        TrendDirection.INCREASING: 1.0,
        TrendDirection.STABLE: 0.4,
        TrendDirection.DECREASING: 0.1,
        TrendDirection.INSUFFICIENT_DATA: 0.3,
    }[trend.direction]


def _evidence_confidence_label(trend: TrendResult) -> str:
    if trend.observation_count >= 3:
        return "high"
    if trend.observation_count == 2:
        return "moderate"
    return "low"


def _score_to_level(score: float) -> RiskLevel:
    if score >= settings.pest_risk_high_score:
        return RiskLevel.HIGH
    if score >= settings.pest_risk_moderate_score:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


class PestRiskEngine:
    """Image-level pest PRESSURE, optionally strengthened by repeated observations.

    Deliberately does NOT fold in crop growth stage as a numeric factor: this
    engine has no verified, pest-specific data on stage susceptibility, and
    inventing one would violate the "do not invent context" rule. Growth
    stage is still carried through to the explanation/evidence for the
    farmer's own judgment and for the crop-compatibility gate.
    """

    def assess(self, observation: Observation, trend: TrendResult) -> RiskAssessment:
        confidence_component = observation.confidence or 0.0
        count_component = min((observation.count or 0) / _COUNT_SATURATION, 1.0)
        trend_component = _trend_factor(trend)

        score = 0.35 * confidence_component + 0.35 * count_component + 0.30 * trend_component
        level = _score_to_level(score)
        scope = "image_and_field_observation" if trend.observation_count >= 2 else "image_only"

        note_parts = [
            f"Based on {observation.count or 0} detection(s) of "
            f"'{observation.name}' at {round(confidence_component * 100)}% AI confidence."
        ]
        if trend.direction != TrendDirection.INSUFFICIENT_DATA:
            note_parts.append(f"Recent observation trend: {trend.direction.value.lower()}.")
        else:
            note_parts.append("Not enough repeated observations yet to assess a trend.")

        return RiskAssessment(
            category=RiskCategory.PEST_PRESSURE,
            level=level,
            scope=scope,
            evidence_confidence=_evidence_confidence_label(trend),
            score=score,
            note=" ".join(note_parts),
        )


class DiseaseRiskEngine:
    """Gated strictly on the disease model's own confidence threshold.

    If confidence is below threshold, this NEVER produces a disease-specific
    risk — it returns a verification-required result instead. See
    docs/AGRICULTURAL_ADVISORY.md, "Disease detection status", for why no
    live disease model backs this engine yet.
    """

    def assess(self, observation: Optional[Observation]) -> Optional[RiskAssessment]:
        if observation is None:
            return None

        if observation.quality == DataQuality.LOW_CONFIDENCE:
            return RiskAssessment(
                category=RiskCategory.DISEASE_RISK,
                level=RiskLevel.NONE,
                scope="image_only",
                evidence_confidence="low",
                score=0.0,
                note=(
                    "Disease confidence is below the production acceptance threshold. "
                    "Image requires further verification before any disease-specific "
                    "guidance can be given."
                ),
            )

        # Confidence is acceptable, but this only reflects model certainty —
        # whether verified guidance exists is decided by the knowledge-base
        # gate in engine.py, not here.
        return RiskAssessment(
            category=RiskCategory.DISEASE_RISK,
            level=RiskLevel.MODERATE,
            scope="image_only",
            evidence_confidence="high",
            score=observation.confidence or 0.0,
            note=(
                f"'{observation.name}' detected with acceptable confidence "
                f"({round((observation.confidence or 0.0) * 100)}%)."
            ),
        )


class WaterStressEngine:
    """Combines soil moisture with at least one other environmental signal.

    Per the project spec: never decide from soil moisture alone. If soil
    moisture or all secondary signals (temperature/humidity/rainfall) are
    missing, this returns INSUFFICIENT_DATA rather than guessing.
    """

    LOW_MOISTURE_PCT = 30.0
    HIGH_MOISTURE_PCT = 70.0
    SIGNIFICANT_RAINFALL_MM = 10.0
    HIGH_TEMPERATURE_C = 33.0

    def assess(
        self,
        soil_moisture: Optional[Observation],
        air_temperature: Optional[Observation] = None,
        humidity: Optional[Observation] = None,
        rainfall: Optional[Observation] = None,
    ) -> dict:
        if soil_moisture is None or soil_moisture.quality != DataQuality.VALID:
            return {
                "decision": "INSUFFICIENT_DATA",
                "note": "Soil moisture reading is missing or invalid; cannot assess irrigation need.",
            }

        secondary = [
            obs for obs in (air_temperature, humidity, rainfall)
            if obs is not None and obs.quality == DataQuality.VALID
        ]
        if not secondary:
            return {
                "decision": "INSUFFICIENT_DATA",
                "note": (
                    "Only soil moisture is available. Per policy, irrigation decisions are "
                    "not made from soil moisture alone; temperature, humidity, or rainfall "
                    "data is also needed."
                ),
            }

        moisture = soil_moisture.value or 0.0
        recent_rain = (rainfall.value or 0.0) if (rainfall and rainfall.quality == DataQuality.VALID) else None
        hot = (
            air_temperature.value is not None
            and air_temperature.quality == DataQuality.VALID
            and air_temperature.value >= self.HIGH_TEMPERATURE_C
        )

        if recent_rain is not None and recent_rain >= self.SIGNIFICANT_RAINFALL_MM:
            return {
                "decision": "WAIT",
                "note": (
                    f"Recent rainfall ({recent_rain:.0f}mm) was significant. "
                    "Delay irrigation and recheck soil moisture after the rainfall is absorbed."
                ),
            }

        if moisture <= self.LOW_MOISTURE_PCT and (hot or recent_rain == 0.0):
            return {
                "decision": "IRRIGATE",
                "note": (
                    f"Soil moisture is low ({moisture:.0f}%) with no offsetting recent rainfall"
                    + (" and high temperature" if hot else "")
                    + ". Irrigation is likely warranted; confirm against local crop water-need guidance."
                ),
            }

        if moisture >= self.HIGH_MOISTURE_PCT:
            return {
                "decision": "WAIT",
                "note": f"Soil moisture is already high ({moisture:.0f}%). Delay irrigation.",
            }

        return {
            "decision": "MONITOR",
            "note": f"Soil moisture ({moisture:.0f}%) is in a moderate range; monitor and recheck.",
        }


class EnvironmentalRiskEngine:
    """Simple, modular, threshold-based checks over ACTUAL supplied readings.

    These are generic agronomic heuristics (not crop-specific, not sourced
    from a peer-reviewed threshold study) intended as coarse triage signals,
    not forecasts. They never estimate or predict a value that wasn't
    supplied.
    """

    HEAT_STRESS_TEMP_C = 38.0
    EXCESS_RAIN_MM = 100.0

    def assess_heat_stress(self, air_temperature: Optional[Observation]) -> RiskAssessment:
        if air_temperature is None or air_temperature.quality != DataQuality.VALID:
            return RiskAssessment(
                category=RiskCategory.HEAT_STRESS,
                level=RiskLevel.NONE,
                scope="sensor_or_weather_data",
                evidence_confidence="low",
                score=0.0,
                note="No valid temperature reading available; heat-stress risk cannot be assessed.",
            )
        value = air_temperature.value or 0.0
        level = RiskLevel.HIGH if value >= self.HEAT_STRESS_TEMP_C else RiskLevel.LOW
        return RiskAssessment(
            category=RiskCategory.HEAT_STRESS,
            level=level,
            scope="sensor_or_weather_data",
            evidence_confidence="high",
            score=min(value / (self.HEAT_STRESS_TEMP_C * 1.2), 1.0),
            note=f"Reported air temperature: {value:.1f}C.",
        )

    def assess_excess_rain(self, rainfall: Optional[Observation]) -> RiskAssessment:
        if rainfall is None or rainfall.quality != DataQuality.VALID:
            return RiskAssessment(
                category=RiskCategory.EXCESS_RAIN,
                level=RiskLevel.NONE,
                scope="sensor_or_weather_data",
                evidence_confidence="low",
                score=0.0,
                note="No valid rainfall reading available; excess-rain risk cannot be assessed.",
            )
        value = rainfall.value or 0.0
        level = RiskLevel.HIGH if value >= self.EXCESS_RAIN_MM else RiskLevel.LOW
        return RiskAssessment(
            category=RiskCategory.EXCESS_RAIN,
            level=level,
            scope="sensor_or_weather_data",
            evidence_confidence="high",
            score=min(value / (self.EXCESS_RAIN_MM * 1.2), 1.0),
            note=f"Reported rainfall: {value:.1f}mm.",
        )
