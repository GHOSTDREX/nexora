"""Advisory Engine: orchestrates observation -> context -> risk -> gates ->
recommendations -> explanation -> audit, as described in
docs/AGRICULTURAL_ADVISORY.md.

This module contains NO agricultural facts itself — every fact-bearing
sentence in a recommendation comes from agricultural_advisory/knowledge_base.
This module only sequences the pipeline and generates explanations built
strictly from the actual computed inputs (observation, risk, trend).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from app.ml.agricultural_advisory import observation as obs_module
from app.ml.agricultural_advisory import rules as rules_module
from app.ml.agricultural_advisory.config import (
    ADVISORY_ENGINE_VERSION,
    KNOWLEDGE_BASE_VERSION,
    RULE_SET_VERSION,
    settings,
)
from app.ml.agricultural_advisory.data_quality import classify_reading
from app.ml.agricultural_advisory.history_store import HistoryStore, get_history_store
from app.ml.agricultural_advisory.knowledge_base.loader import KnowledgeBase, load_knowledge_base
from app.ml.agricultural_advisory.risk import (
    DiseaseRiskEngine,
    EnvironmentalRiskEngine,
    PestRiskEngine,
    WaterStressEngine,
)
from app.ml.agricultural_advisory.safety import (
    crop_compatibility_gate,
    data_quality_gate,
    knowledge_base_gate,
)
from app.ml.agricultural_advisory.schemas import (
    AdvisoryResult,
    AdvisoryStatus,
    AuditRecord,
    DataQuality,
    Observation,
    Priority,
    Recommendation,
    RecommendationType,
    RiskAssessment,
    RiskLevel,
    SourceRef,
    TrendDirection,
)
from app.ml.agricultural_advisory.temporal import compute_trend


def _pest_detector_confidence_threshold() -> float:
    try:
        from pest_detection.config import settings as pest_settings

        return pest_settings.confidence_threshold
    except Exception:  # noqa: BLE001
        return 0.25


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _confidence_word(confidence: Optional[float]) -> str:
    if confidence is None:
        return "unknown"
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.5:
        return "moderate"
    return "low"


def _hedge_verb(confidence: Optional[float]) -> str:
    # Wording-only convention (see pest_detection frontend for the same
    # midpoint choice): never a detection cutoff — the detector/model has
    # already decided what counts as a detection at all.
    if confidence is not None and confidence < 0.5:
        return "possibly detected"
    return "detected"


def _pest_explanation(observation: Observation, risk: RiskAssessment, trend) -> str:
    name = observation.name or "This pest"
    parts = [
        f"{name.title()} was {_hedge_verb(observation.confidence)} with "
        f"{_confidence_word(observation.confidence)} AI confidence "
        f"({round((observation.confidence or 0.0) * 100)}%) in the submitted image."
    ]
    if observation.count and observation.count > 1:
        parts.append(f"{observation.count} individuals were counted in this image.")

    if trend.direction == TrendDirection.INCREASING:
        parts.append(
            "Detections of this pest have increased across recent observations at this "
            "field, which raises the monitoring priority."
        )
    elif trend.direction == TrendDirection.DECREASING:
        parts.append("Detections of this pest have decreased across recent observations at this field.")
    elif trend.direction == TrendDirection.STABLE:
        parts.append("Detections of this pest have remained stable across recent observations.")
    else:
        parts.append(
            "This is the first recorded observation of this pest at this field, so a trend "
            "cannot be assessed yet."
        )

    parts.append(f"Based on this evidence, the image-level risk indicator is {risk.level.value}.")
    return " ".join(parts)


class AdvisoryEngine:
    def __init__(self, kb: Optional[KnowledgeBase] = None, history_store: Optional[HistoryStore] = None):
        self._kb = kb or load_knowledge_base()
        self._history = history_store or get_history_store()
        self._pest_risk_engine = PestRiskEngine()
        self._disease_risk_engine = DiseaseRiskEngine()
        self._water_stress_engine = WaterStressEngine()
        self._environmental_risk_engine = EnvironmentalRiskEngine()

    # ------------------------------------------------------------------
    # Sensor/weather observation construction
    # ------------------------------------------------------------------

    def _build_environment_observation(
        self, key: str, sensor_data: dict, weather_data: dict, unit: str
    ) -> Observation:
        """Prefers a direct sensor reading; falls back to weather data for the
        same physical quantity. Never fabricates a value when both are absent.
        """
        source_dict = sensor_data.get(key) if isinstance(sensor_data.get(key), dict) else None
        weather_key = "temperature" if key == "air_temperature" else key
        weather_source = (
            weather_data.get(weather_key) if isinstance(weather_data.get(weather_key), dict) else None
        )

        chosen, source_label = (source_dict, "sensor") if source_dict else (weather_source, "weather")
        if chosen is None:
            return Observation(source="sensor", type="sensor", name=key, quality=DataQuality.MISSING, unit=unit)

        value = chosen.get("value")
        timestamp = chosen.get("timestamp")
        max_age = (
            settings.sensor_stale_after_seconds
            if source_label == "sensor"
            else settings.weather_stale_after_seconds
        )
        quality = classify_reading(value, sensor_key=key, timestamp=timestamp, max_age_seconds=max_age)
        return Observation(
            source=source_label, type=source_label, name=key, value=value, unit=unit,
            quality=quality, timestamp=timestamp,
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def analyze(self, request: dict[str, Any]) -> AdvisoryResult:
        timestamp = request.get("observation_timestamp") or _now()
        farm_id = request.get("farm_id")
        field_id = request.get("field_id")
        crop = request.get("crop")
        growth_stage = request.get("growth_stage")

        pest_result = request.get("pest_result")
        disease_result = request.get("disease_result")
        sensor_data = request.get("sensor_data") or {}
        weather_data = request.get("weather_data") or {}
        client_history = request.get("historical_observations") or []

        risk_assessments: list[RiskAssessment] = []
        recommendations: list[Recommendation] = []
        explanations: list[str] = []
        rules_triggered: list[str] = []
        used_source_ids: set[str] = set()

        pest_observations = (
            obs_module.pest_detection_result_to_observations(pest_result, timestamp)
            if pest_result
            else []
        )
        disease_observation = obs_module.disease_result_to_observation(disease_result, timestamp)

        # --- Pest pathway ---------------------------------------------------
        for pest_obs in pest_observations:
            dq_gate = data_quality_gate(pest_obs)
            if not dq_gate.passed:
                explanations.append(
                    f"Skipped '{pest_obs.name}': {dq_gate.reason}"
                )
                continue

            kb_gate = knowledge_base_gate(self._kb, pest_obs.name)
            if not kb_gate.passed:
                explanations.append(
                    f"'{pest_obs.name}' was detected, but the system does not yet have "
                    f"verified guidance for it: {kb_gate.reason}"
                )
                continue

            crop_gate = crop_compatibility_gate(self._kb, pest_obs.name, crop)
            if not crop_gate.passed:
                explanations.append(f"'{pest_obs.name}': {crop_gate.reason}")
                continue

            # Temporal reasoning: merge disk history + client-supplied history + this observation.
            past_records = self._history.query(farm_id, field_id, pest_obs.name)
            client_records = [
                h for h in client_history if h.get("pest_name") == pest_obs.name
            ]
            combined = past_records + client_records + [
                {"timestamp": pest_obs.timestamp, "count": pest_obs.count}
            ]
            trend = compute_trend(combined)

            risk = self._pest_risk_engine.assess(pest_obs, trend)
            risk_assessments.append(risk)

            pest_recommendations = rules_module.generate_pest_recommendations(
                self._kb, pest_obs, risk
            )
            recommendations.extend(pest_recommendations)
            rules_triggered.extend(r.rule_id for r in pest_recommendations)
            for r in pest_recommendations:
                used_source_ids.update(r.source_ids)

            explanations.append(self._pest_explanation_with_confidence_gate(pest_obs, risk, trend))

            self._history.append(
                {
                    "farm_id": farm_id,
                    "field_id": field_id,
                    "pest_name": pest_obs.name,
                    "timestamp": pest_obs.timestamp,
                    "count": pest_obs.count,
                    "confidence": pest_obs.confidence,
                }
            )

        # --- Disease pathway (interface-only; see observation.py) -----------
        if disease_observation is not None:
            disease_risk = self._disease_risk_engine.assess(disease_observation)
            if disease_risk is not None:
                risk_assessments.append(disease_risk)

            if disease_observation.quality == DataQuality.LOW_CONFIDENCE:
                rec = Recommendation(
                    rule_id="DISEASE_VERIFY_001",
                    priority=Priority.MODERATE,
                    type=RecommendationType.RECHECK,
                    action="Image requires further verification. Capture another clear image of the affected area.",
                    evidence={"disease": disease_observation.name, "confidence": disease_observation.confidence},
                    source_ids=["system_policy"],
                )
                recommendations.append(rec)
                rules_triggered.append(rec.rule_id)
                used_source_ids.add("system_policy")
                explanations.append(
                    f"'{disease_observation.name}' was suggested by the disease model, but its "
                    f"confidence ({round((disease_observation.confidence or 0.0) * 100)}%) is below "
                    f"the production acceptance threshold "
                    f"({round(settings.disease_confidence_threshold * 100)}%), so no disease-specific "
                    f"guidance is generated. Further verification is required."
                )
            else:
                kb_entry = self._kb.diseases.get(disease_observation.name)
                if kb_entry is None:
                    rec = Recommendation(
                        rule_id="DISEASE_KNOWLEDGE_GAP_001",
                        priority=Priority.INFO,
                        type=RecommendationType.INFORMATION,
                        action=(
                            f"'{disease_observation.name}' was detected with acceptable confidence, "
                            "but this system does not yet have verified agronomic guidance for it. "
                            "Consult your local agricultural extension service."
                        ),
                        evidence={
                            "disease": disease_observation.name,
                            "confidence": disease_observation.confidence,
                        },
                        source_ids=["system_policy"],
                    )
                    recommendations.append(rec)
                    rules_triggered.append(rec.rule_id)
                    used_source_ids.add("system_policy")
                    explanations.append(
                        f"'{disease_observation.name}' was detected with acceptable confidence, but "
                        f"no verified knowledge-base entry exists for it yet (knowledge gap)."
                    )

        # --- Water stress / irrigation ---------------------------------------
        water_stress_requested = any(
            k in sensor_data or k in weather_data
            for k in ("soil_moisture", "air_temperature", "temperature", "humidity", "rainfall")
        )
        if water_stress_requested:
            soil_moisture = self._build_environment_observation(
                "soil_moisture", sensor_data, weather_data, "%"
            )
            air_temperature = self._build_environment_observation(
                "air_temperature", sensor_data, weather_data, "C"
            )
            humidity = self._build_environment_observation("humidity", sensor_data, weather_data, "%")
            rainfall = self._build_environment_observation("rainfall", sensor_data, weather_data, "mm")

            water_result = self._water_stress_engine.assess(
                soil_moisture, air_temperature, humidity, rainfall
            )
            if water_result["decision"] != "INSUFFICIENT_DATA":
                priority = {
                    "IRRIGATE": Priority.MODERATE,
                    "WAIT": Priority.LOW,
                    "MONITOR": Priority.LOW,
                }[water_result["decision"]]
                rec = Recommendation(
                    rule_id=f"WATER_STRESS_{water_result['decision']}_001",
                    priority=priority,
                    type=RecommendationType.IRRIGATION_ACTION,
                    action=water_result["note"],
                    evidence={"decision": water_result["decision"]},
                    source_ids=["system_policy"],
                )
                recommendations.append(rec)
                rules_triggered.append(rec.rule_id)
                used_source_ids.add("system_policy")
            explanations.append(f"Irrigation guidance: {water_result['note']}")

            heat_risk = self._environmental_risk_engine.assess_heat_stress(air_temperature)
            excess_rain_risk = self._environmental_risk_engine.assess_excess_rain(rainfall)
            risk_assessments.append(heat_risk)
            risk_assessments.append(excess_rain_risk)

        # --- Status determination --------------------------------------------
        status = self._determine_status(
            pest_result, pest_observations, disease_observation, water_stress_requested, recommendations
        )

        sources = [
            SourceRef(
                id=s["id"], organization=s["organization"], title=s["title"], url=s["url"],
                reference_type=s.get("reference_type", "extension_publication"),
            )
            for sid, s in self._kb.sources.items()
            if sid in used_source_ids
        ]

        audit = AuditRecord(
            timestamp=timestamp,
            farm_id=farm_id,
            field_id=field_id,
            observation_id=str(uuid.uuid4()),
            inputs_summary={
                "crop": crop,
                "growth_stage": growth_stage,
                "pest_species_observed": [o.name for o in pest_observations],
                "disease_observed": disease_observation.name if disease_observation else None,
                "water_stress_data_provided": water_stress_requested,
            },
            risk_assessments=[r.to_dict() for r in risk_assessments],
            rules_triggered=rules_triggered,
            recommendation_count=len(recommendations),
            advisory_engine_version=ADVISORY_ENGINE_VERSION,
            knowledge_base_version=KNOWLEDGE_BASE_VERSION,
            rule_set_version=RULE_SET_VERSION,
        )

        return AdvisoryResult(
            status=status,
            risk_assessments=risk_assessments,
            recommendations=recommendations,
            explanations=explanations,
            sources=sources,
            audit=audit,
        )

    def _pest_explanation_with_confidence_gate(self, pest_obs, risk, trend) -> str:
        return _pest_explanation(pest_obs, risk, trend)

    def _determine_status(
        self,
        pest_result: Optional[dict],
        pest_observations: list[Observation],
        disease_observation: Optional[Observation],
        water_stress_requested: bool,
        recommendations: list[Recommendation],
    ) -> AdvisoryStatus:
        gave_any_input = (
            pest_result is not None or disease_observation is not None or water_stress_requested
        )
        if not gave_any_input:
            return AdvisoryStatus.INSUFFICIENT_EVIDENCE

        if recommendations:
            return AdvisoryStatus.ADVISORY_AVAILABLE

        if pest_result is not None and not pest_observations and disease_observation is None:
            return AdvisoryStatus.NO_PEST_OR_DISEASE_DETECTED

        if water_stress_requested:
            return AdvisoryStatus.INSUFFICIENT_EVIDENCE

        if not recommendations:
            return AdvisoryStatus.KNOWLEDGE_GAP

        return AdvisoryStatus.ADVISORY_AVAILABLE


_default_engine: Optional[AdvisoryEngine] = None


def get_advisory_engine() -> AdvisoryEngine:
    global _default_engine
    if _default_engine is None:
        _default_engine = AdvisoryEngine()
    return _default_engine
