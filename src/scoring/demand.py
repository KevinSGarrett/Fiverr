"""S4.1 Demand Score calculator."""

from __future__ import annotations

import logging
import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.analysis.external_signals import (
    _classify_autocomplete_absence,
    _compute_fiverr_relevance_qualifier,
    _qualify_reddit_score,
    estimate_buyer_intent_ratio,
)
from src.collection.search_url_builder import (
    SEARCH_STRICTNESS_COLUMN,
    UNCONSTRAINED_DEMAND_DEDUCTION,
    UNCONSTRAINED_NOTE,
)
from src.config.models import ExternalSignalsConfig
from src.models import ClusterAssignment, ClusterLabel, ExternalSignal, Keyword, SearchResult
from src.scoring.contracts import DemandScoreResult, ScoreComponent
from src.scoring.result_set_relevance import apply_trc_adjustments, get_result_set_validation

_DEFAULT_CLUSTER_BOOST = 5.0
_DEFAULT_MIN_CLUSTER_SIZE = 3
_R1_STRICTNESS_EFFECTIVE_DATE = date(2026, 5, 30)
_EMERGING_MIN = 3
log = logging.getLogger(__name__)


def _coerce_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _coerce_float(value: Any, default: float) -> float:
    if isinstance(value, bool) or value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int) -> int:
    if isinstance(value, bool) or value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _demand_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return {}
    demand_cfg = scoring_cfg.get("demand")
    if not isinstance(demand_cfg, Mapping):
        return {}
    return dict(demand_cfg)


def _relevance_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {"enable_sponsored_exclusion": True}
    relevance_cfg = config.get("relevance")
    if not isinstance(relevance_cfg, Mapping):
        return {"enable_sponsored_exclusion": True}
    return {"enable_sponsored_exclusion": bool(relevance_cfg.get("enable_sponsored_exclusion", True))}


def _external_signals_config(config: dict[str, Any] | None) -> ExternalSignalsConfig:
    defaults = ExternalSignalsConfig()
    if not isinstance(config, Mapping):
        return defaults
    analysis_cfg = config.get("analysis")
    if not isinstance(analysis_cfg, Mapping):
        return defaults

    raw_nested = analysis_cfg.get("external_signals")
    nested = dict(raw_nested) if isinstance(raw_nested, Mapping) else {}
    nested["enabled"] = bool(analysis_cfg.get("external_signals_enabled", defaults.enabled))
    try:
        return ExternalSignalsConfig.model_validate(nested)
    except Exception:
        return defaults


# R4.1 (DEMAND_SCORE.md "TRC Reliability Qualifier") deduction schedule. The spec is an
# ADDITIVE model stacking deductions from 1.0 - the previous implementation took min()
# of the legacy R3 multiplicative band factors instead (raw RSV as the multiplier, R3's
# 10%/20%/35% sponsored bands, zero CATEGORY penalty, no extreme-TRC factor), which the
# spec explicitly supersedes ("Replaces the R3 sponsored-fraction bands once R4 ships.
# Never stack both."). Concretely, RSV=0.50 yielded 0.50 instead of the intended 0.85,
# suppressing Demand Score far more aggressively than designed (SCRUM-1101).
_TRC_STRICTNESS_DEDUCTIONS = {"NONE": 0.15, "CATEGORY": 0.05, "SUBCATEGORY": 0.0}
_TRC_RELEVANCE_DEDUCTION_WEIGHT = 0.30
_TRC_SPONSORED_THRESHOLD = 0.35
_TRC_SPONSORED_DEDUCTION = 0.10
_TRC_EXTREME_COUNT_THRESHOLD = 100_000.0
_TRC_EXTREME_COUNT_DEDUCTION = 0.05


def _compute_trc_reliability(
    rsv_relevance: float | None,
    sponsored_fraction: float | None,
    strictness: str | None,
    total_result_count: float | None = None,
    *,
    weights: dict[str, float] | None = None,
) -> float:
    """R4.1: single authoritative 0.0-1.0 reliability multiplier for raw TRC.

    Additively stacks deductions from 1.0 per DEMAND_SCORE.md:
      strictness NONE -0.15 / CATEGORY -0.05 / SUBCATEGORY 0
      relevance   max(0, (1.0 - rsv) * 0.30)
      sponsored   -0.10 when sponsored_fraction > 0.35
      extreme TRC -0.05 when total_result_count > 100,000
    Missing (None) inputs contribute no deduction.
    """
    del weights
    deductions = 0.0
    normalized_strictness = _normalize_search_strictness(strictness)
    if normalized_strictness is not None:
        deductions += _TRC_STRICTNESS_DEDUCTIONS.get(normalized_strictness, 0.0)
    if rsv_relevance is not None:
        deductions += max(0.0, (1.0 - _clamp01(rsv_relevance)) * _TRC_RELEVANCE_DEDUCTION_WEIGHT)
    if sponsored_fraction is not None and sponsored_fraction > _TRC_SPONSORED_THRESHOLD:
        deductions += _TRC_SPONSORED_DEDUCTION
    if total_result_count is not None and total_result_count > _TRC_EXTREME_COUNT_THRESHOLD:
        deductions += _TRC_EXTREME_COUNT_DEDUCTION
    return _clamp01(1.0 - deductions)


def _classify_autocomplete_state(suggestions: list[str] | None) -> str:
    if suggestions is None:
        return "present"
    normalized = {
        suggestion.strip().lower()
        for suggestion in suggestions
        if isinstance(suggestion, str) and suggestion.strip()
    }
    if not normalized:
        return "absent"
    if len(normalized) < _EMERGING_MIN:
        return "emerging"
    return "present"


def _autocomplete_state_multiplier(state: str) -> float:
    if state == "absent":
        return 0.80
    if state == "emerging":
        return 0.95
    return 1.0


def _trends_platform_qualifier(trends_signal: Any) -> float:
    if trends_signal is None:
        return 1.0
    if isinstance(trends_signal, Mapping):
        for key in ("platform_fit", "platform_qualifier", "fit", "score"):
            raw = trends_signal.get(key)
            if raw is None:
                continue
            try:
                value = float(raw)
                return _clamp01(value if value <= 1.0 else value / 100.0)
            except (TypeError, ValueError):
                continue
        trends_12mo = trends_signal.get("trends_12mo_score")
        if trends_12mo is not None:
            try:
                return _clamp01(float(trends_12mo) / 100.0)
            except (TypeError, ValueError):
                return 1.0
        return 1.0
    try:
        value = float(trends_signal)
    except (TypeError, ValueError):
        return 1.0
    return _clamp01(value if value <= 1.0 else value / 100.0)


def _extract_cluster_context(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    cluster_id = payload.get("cluster_id")
    if cluster_id is None:
        return None
    return {
        "cluster_id": cluster_id,
        "keyword_count": payload.get("cluster_keyword_count", payload.get("keyword_count")),
        "label_text": payload.get("cluster_label_text", payload.get("label_text")),
        "opportunity_narrative": payload.get(
            "cluster_opportunity_narrative",
            payload.get("opportunity_narrative"),
        ),
    }


def _load_cluster_context_from_session(keyword_id: int, session: Session) -> dict[str, Any] | None:
    assignment = (
        session.query(ClusterAssignment)
        .filter(ClusterAssignment.keyword_id == keyword_id)
        .order_by(ClusterAssignment.assigned_at.desc(), ClusterAssignment.id.desc())
        .first()
    )
    if assignment is None:
        return None

    cluster_id = int(assignment.cluster_id)
    if cluster_id < 0:
        return {
            "cluster_id": cluster_id,
            "keyword_count": 0,
            "label_text": None,
            "opportunity_narrative": None,
            "niche_id": assignment.niche_id,
            "run_id": assignment.run_id,
        }

    label = (
        session.query(ClusterLabel)
        .filter(
            ClusterLabel.niche_id == assignment.niche_id,
            ClusterLabel.cluster_id == cluster_id,
            ClusterLabel.run_id == assignment.run_id,
        )
        .order_by(ClusterLabel.created_at.desc(), ClusterLabel.id.desc())
        .first()
    )
    if label is None:
        label = (
            session.query(ClusterLabel)
            .filter(
                ClusterLabel.niche_id == assignment.niche_id,
                ClusterLabel.cluster_id == cluster_id,
            )
            .order_by(ClusterLabel.created_at.desc(), ClusterLabel.id.desc())
            .first()
        )

    keyword_count = (
        int(label.keyword_count)
        if label is not None and label.keyword_count is not None
        else session.query(ClusterAssignment)
        .filter(
            ClusterAssignment.niche_id == assignment.niche_id,
            ClusterAssignment.cluster_id == cluster_id,
            ClusterAssignment.run_id == assignment.run_id,
        )
        .count()
    )
    return {
        "cluster_id": cluster_id,
        "keyword_count": keyword_count,
        "label_text": label.label_text if label is not None else None,
        "opportunity_narrative": label.opportunity_narrative if label is not None else None,
        "niche_id": assignment.niche_id,
        "run_id": assignment.run_id,
    }


def _load_cluster_context(keyword_id: int, db: Any) -> dict[str, Any] | None:
    if db is None:
        return None

    if isinstance(db, Session):
        try:
            return _load_cluster_context_from_session(keyword_id, db)
        except Exception:
            return None

    if hasattr(db, "get_cluster_assignment"):
        loaded = db.get_cluster_assignment(keyword_id)
        if isinstance(loaded, Mapping):
            return dict(loaded)

    if hasattr(db, "get_demand_inputs"):
        loaded = db.get_demand_inputs(keyword_id)
        if isinstance(loaded, Mapping):
            extracted = _extract_cluster_context(loaded)
            if extracted is not None:
                return extracted

    if isinstance(db, Mapping):
        loaded = db.get(keyword_id, db)
        if isinstance(loaded, Mapping):
            return _extract_cluster_context(loaded)

    return None


def _compute_cluster_demand_boost(
    keyword_id: int,
    db: Any,
    config: dict[str, Any] | None,
) -> tuple[float, dict[str, Any] | None]:
    demand_cfg = _demand_config(config)
    use_cluster_boost = _coerce_bool(demand_cfg.get("use_cluster_boost"), True)
    if not use_cluster_boost:
        return 0.0, None

    cluster_context = _load_cluster_context(keyword_id, db)
    if cluster_context is None:
        return 0.0, None

    cluster_id = _coerce_int(cluster_context.get("cluster_id"), -1)
    if cluster_id < 0:
        return 0.0, cluster_context

    min_cluster_size = max(1, _coerce_int(demand_cfg.get("min_cluster_size"), _DEFAULT_MIN_CLUSTER_SIZE))
    keyword_count = max(0, _coerce_int(cluster_context.get("keyword_count"), 0))
    if keyword_count < min_cluster_size:
        return 0.0, cluster_context

    configured_boost = _coerce_float(demand_cfg.get("cluster_boost"), _DEFAULT_CLUSTER_BOOST)
    boost = max(0.0, min(10.0, configured_boost))
    if boost <= 0.0:
        return 0.0, cluster_context

    normalized_context = dict(cluster_context)
    normalized_context["cluster_id"] = cluster_id
    normalized_context["keyword_count"] = keyword_count
    return boost, normalized_context


def get_cluster_demand_boost(keyword_id: int, db: Any, config: dict[str, Any] | None) -> float:
    """Returns 0.0–10.0 demand boost based on cluster membership and cluster size."""
    boost, _ = _compute_cluster_demand_boost(keyword_id, db, config)
    return boost


def _normalize_search_strictness(value: Any) -> str | None:
    if isinstance(value, str):
        normalized = value.strip().upper()
        if normalized:
            return normalized
    return None


def _is_post_r1_none_strictness(row: SearchResult) -> bool:
    collected_at = row.collected_at
    if isinstance(collected_at, datetime):
        return collected_at.date() >= _R1_STRICTNESS_EFFECTIVE_DATE
    return False


def _resolve_marketplace_snapshot(
    session: Session,
    keyword_id: int,
) -> tuple[float | None, str | None, int | None, int | None]:
    """Resolve demand count and paired strictness from the same source row."""
    max_total_result_row = (
        session.query(SearchResult)
        .filter(
            SearchResult.keyword_id == keyword_id,
            SearchResult.total_result_count.isnot(None),
        )
        .order_by(SearchResult.total_result_count.desc(), SearchResult.collected_at.desc(), SearchResult.id.desc())
        .first()
    )
    if max_total_result_row is not None and max_total_result_row.total_result_count is not None:
        strictness = _normalize_search_strictness(max_total_result_row.search_strictness_used)
        # Legacy rows can carry migration defaults ("NONE") that were never explicitly collected.
        if strictness == "NONE" and not _is_post_r1_none_strictness(max_total_result_row):
            strictness = None
        sponsored_gig_count = (
            int(max_total_result_row.sponsored_gig_count)
            if max_total_result_row.sponsored_gig_count is not None
            else None
        )
        total_gig_count: int | None = None
        if (
            max_total_result_row.sponsored_gig_count is not None
            and max_total_result_row.organic_gig_count is not None
        ):
            total_gig_count = int(max_total_result_row.sponsored_gig_count + max_total_result_row.organic_gig_count)
        elif isinstance(max_total_result_row.gig_cards, list):
            total_gig_count = len(max_total_result_row.gig_cards)
        return float(max_total_result_row.total_result_count), strictness, sponsored_gig_count, total_gig_count

    # Only use row-count as a coarse fallback when we have broad top-result coverage.
    # Sparse partial rows (e.g. 1-2 persisted cards) understate true marketplace volume
    # and can suppress demand unfairly.
    fallback_count = (
        session.query(SearchResult)
        .filter(
            SearchResult.keyword_id == keyword_id,
            SearchResult.rank.isnot(None),
            SearchResult.rank <= 10,
        )
        .count()
    )
    if fallback_count >= 10:
        return float(fallback_count), None, None, None
    return None, None, None, None


def trc_adjustment(
    sponsored_gig_count: int | None,
    total: int | None,
    config: dict[str, Any] | None,
    strictness_used: str | None,
) -> float:
    """
    R3 sponsored-fraction multiplier.

    SUPERSEDED by R4.1 TRC reliability multiplier. Replace this body in R4.1;
    do not stack both adjustments (DL-209).
    """
    if not _relevance_config(config).get("enable_sponsored_exclusion", True):
        return 1.0
    if strictness_used is None:
        # Preserve the C051 migration-default NONE guard behavior for legacy rows.
        return 1.0
    if sponsored_gig_count is None or total is None:
        return 1.0
    sponsored_fraction = float(sponsored_gig_count) / max(float(total), 1.0)
    if sponsored_fraction <= 0.10:
        return 1.00
    if sponsored_fraction <= 0.20:
        return 0.90
    if sponsored_fraction <= 0.35:
        return 0.80
    return 0.70


class DemandScoreCalculator:
    """Calculate demand score from Fiverr, trends, and Reddit signals."""

    _COUNT_WEIGHT = 0.50
    _AUTOCOMPLETE_WEIGHT = 0.20
    _TRENDS_WEIGHT = 0.20
    _REDDIT_WEIGHT = 0.10

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        config: dict[str, Any] | None = None,
    ) -> DemandScoreResult:
        """Calculate a demand score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0
        demand_cfg = _demand_config(config)
        use_trc_reliability = _coerce_bool(demand_cfg.get("use_trc_reliability"), False)
        use_signal_qualifiers = _coerce_bool(demand_cfg.get("use_signal_qualifiers"), False)
        external_signals_config = _external_signals_config(config)
        external_signals_enabled = bool(external_signals_config.enabled)
        trc_reliability: float | None = None
        rsv = get_result_set_validation(keyword_id, db)
        rsv_relevance = (
            float(rsv.result_set_relevance_score)
            if rsv is not None and rsv.result_set_relevance_score is not None
            else None
        )

        total_result_count = self._as_float(signals.get("total_result_count"))
        search_strictness_used = str(signals.get(SEARCH_STRICTNESS_COLUMN) or "").strip() or None
        sponsored_exclusion_enabled = _relevance_config(config).get("enable_sponsored_exclusion", True)
        count_multiplier = 1.0
        if not use_trc_reliability:
            count_multiplier = trc_adjustment(
                sponsored_gig_count=self._as_int(signals.get("sponsored_gig_count")),
                total=self._as_int(signals.get("total_gig_count")),
                config=config,
                strictness_used=search_strictness_used,
            )
        if total_result_count is not None:
            sponsored_gig_count = self._as_int(signals.get("sponsored_gig_count"))
            total_gig_count = self._as_int(signals.get("total_gig_count"))
            sponsored_fraction = (
                float(sponsored_gig_count) / max(float(total_gig_count), 1.0)
                if sponsored_exclusion_enabled
                and sponsored_gig_count is not None
                and total_gig_count is not None
                else None
            )
            adjusted_trc = total_result_count * count_multiplier
            if use_trc_reliability:
                trc_reliability = _compute_trc_reliability(
                    rsv_relevance=rsv_relevance,
                    sponsored_fraction=sponsored_fraction,
                    strictness=search_strictness_used,
                    total_result_count=total_result_count,
                )
                adjusted_trc = total_result_count * trc_reliability
                # R4.1: low reliability also dents confidence (DEMAND_SCORE.md line
                # "trc_reliability < 0.70 -> confidence_breakdown[...] = -0.05") -
                # previously never implemented anywhere (SCRUM-1101).
                if trc_reliability < 0.70:
                    confidence_breakdown["trc_reliability_low"] = -0.05
            elif rsv is not None:
                adjusted_trc = apply_trc_adjustments(
                    trc=total_result_count,
                    rsv=rsv,
                    sponsored_fraction=sponsored_fraction,
                )
                if adjusted_trc != total_result_count:
                    log.debug(
                        "demand: qualified_trc=%s (rsv=%.2f) kw=%s",
                        adjusted_trc,
                        float(rsv.result_set_relevance_score or 1.0),
                        keyword_id,
                    )
            count_score = self._normalize_count(adjusted_trc)
            score_components["fiverr_count"] = ScoreComponent(
                value=count_score,
                weight=self._COUNT_WEIGHT,
                raw=total_result_count,
                note=(
                    f"TRC adjusted from {total_result_count:.2f} to {adjusted_trc:.2f}"
                    if adjusted_trc != total_result_count
                    else ""
                ),
            )
            weighted_sum += count_score * self._COUNT_WEIGHT
            total_weight_available += self._COUNT_WEIGHT
            source_evidence.append("fiverr_search_results.total_result_count")
        else:
            missing_data_warnings.append("Missing Fiverr total result count.")

        autocomplete_position = self._as_int(signals.get("autocomplete_position"))
        autocomplete_data = signals.get("autocomplete_data")
        keyword_text = str(signals.get("keyword_text", ""))
        niche_id = str(signals.get("niche_id", ""))
        if autocomplete_position is None:
            autocomplete_score = 0.0
            autocomplete_note = "not in Fiverr autocomplete"
            if external_signals_enabled:
                autocomplete_score = float(
                    _classify_autocomplete_absence(
                        keyword_text,
                        niche_id,
                        autocomplete_data if isinstance(autocomplete_data, dict) else None,
                    )
                )
                autocomplete_note = "R7 autocomplete absence classifier applied"
            score_components["autocomplete"] = ScoreComponent(
                value=autocomplete_score,
                weight=self._AUTOCOMPLETE_WEIGHT,
                raw=None,
                note=autocomplete_note,
            )
            weighted_sum += autocomplete_score * self._AUTOCOMPLETE_WEIGHT
            total_weight_available += self._AUTOCOMPLETE_WEIGHT
            source_evidence.append("keywords.autocomplete_position(absent)")
        else:
            position_score = self._normalize_autocomplete_position(autocomplete_position)
            score_components["autocomplete"] = ScoreComponent(
                value=position_score,
                weight=self._AUTOCOMPLETE_WEIGHT,
                raw=autocomplete_position,
            )
            weighted_sum += position_score * self._AUTOCOMPLETE_WEIGHT
            total_weight_available += self._AUTOCOMPLETE_WEIGHT
            source_evidence.append("keywords.autocomplete_position")

        trends_12mo_score = self._as_float(signals.get("trends_12mo_score"))
        if trends_12mo_score is not None:
            raw_trends_score = min(100.0, trends_12mo_score * 1.15)
            trends_score = raw_trends_score
            trends_note = ""
            if external_signals_enabled:
                trends_signal = signals.get("trends_signal")
                trends_payload = trends_signal if isinstance(trends_signal, Mapping) else {}
                trend_direction = str(trends_payload.get("trend_direction", "FLAT"))
                is_fiverr_relevant = bool(trends_payload.get("is_fiverr_relevant", True))
                qualifier = _compute_fiverr_relevance_qualifier(
                    rsv=(rsv_relevance if rsv_relevance is not None else 1.0),
                    is_fiverr_relevant=is_fiverr_relevant,
                    trend_direction=trend_direction,
                    keyword=keyword_text,
                    config=external_signals_config,
                )
                trends_score = raw_trends_score * qualifier
                trends_note = f"R7 trends qualifier={qualifier:.3f} applied pre-demand"
            score_components["google_trends"] = ScoreComponent(
                value=trends_score,
                weight=self._TRENDS_WEIGHT,
                raw=trends_12mo_score,
                note=trends_note,
            )
            weighted_sum += trends_score * self._TRENDS_WEIGHT
            total_weight_available += self._TRENDS_WEIGHT
            source_evidence.append("external_signals.google_trends.trends_12mo_score")
        else:
            confidence_breakdown["missing_google_trends"] = -0.15
            missing_data_warnings.append("Missing Google Trends 12-month score.")

        reddit_demand_intent_score = self._as_float(signals.get("reddit_demand_intent_score"))
        if reddit_demand_intent_score is not None:
            reddit_score_raw = max(0.0, min(100.0, reddit_demand_intent_score * 10.0))
            reddit_score = reddit_score_raw
            reddit_note = ""
            if external_signals_enabled:
                ratio_value = signals.get("reddit_buyer_intent_ratio")
                if isinstance(ratio_value, bool):
                    ratio_value = None
                buyer_intent_ratio = (
                    max(0.0, min(1.0, float(ratio_value)))
                    if isinstance(ratio_value, int | float)
                    else estimate_buyer_intent_ratio(
                        signals.get("reddit_signal") if isinstance(signals.get("reddit_signal"), Mapping) else None
                    )
                )
                reddit_score = _qualify_reddit_score(
                    raw_score=reddit_score_raw,
                    buyer_intent_ratio=buyer_intent_ratio,
                    config=external_signals_config,
                )
                reddit_note = f"R7 reddit intent ratio={buyer_intent_ratio:.3f}"
            score_components["reddit_intent"] = ScoreComponent(
                value=reddit_score,
                weight=self._REDDIT_WEIGHT,
                raw=reddit_demand_intent_score,
                note=reddit_note,
            )
            weighted_sum += reddit_score * self._REDDIT_WEIGHT
            total_weight_available += self._REDDIT_WEIGHT
            source_evidence.append("external_signals.reddit_demand.reddit_demand_intent_score")
        else:
            confidence_breakdown["missing_reddit_intent"] = -0.05
            missing_data_warnings.append("Missing Reddit demand intent score.")

        if total_weight_available < 0.30:
            return DemandScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient demand signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate a demand explanation.",
                total_weight_available=total_weight_available,
            )

        base_demand_score = weighted_sum / total_weight_available
        if use_signal_qualifiers:
            autocomplete_state = _classify_autocomplete_state(signals.get("autocomplete_suggestions"))
            multiplier = _autocomplete_state_multiplier(autocomplete_state)
            trends_signal = signals.get("trends_signal")
            if trends_signal is None:
                trends_signal = {"trends_12mo_score": trends_12mo_score} if trends_12mo_score is not None else None
            multiplier *= _trends_platform_qualifier(trends_signal)
            base_demand_score *= multiplier
        if search_strictness_used == "NONE":
            confidence_breakdown["unconstrained_search"] = UNCONSTRAINED_DEMAND_DEDUCTION
            score_components["unconstrained_search"] = ScoreComponent(
                value=UNCONSTRAINED_DEMAND_DEDUCTION,
                weight=0.0,
                raw=search_strictness_used,
                note=UNCONSTRAINED_NOTE,
            )
            source_evidence.append(f"search_results.{SEARCH_STRICTNESS_COLUMN}")

        cluster_boost, cluster_context = _compute_cluster_demand_boost(keyword_id, db, config)
        cluster_explanation = ""
        if cluster_boost > 0.0 and cluster_context is not None:
            keyword_count = max(0, _coerce_int(cluster_context.get("keyword_count"), 0))
            label_text = cluster_context.get("label_text")
            if not isinstance(label_text, str) or not label_text.strip():
                label_text = f"cluster-{_coerce_int(cluster_context.get('cluster_id'), 0)}"
            opportunity_narrative = cluster_context.get("opportunity_narrative")
            if not isinstance(opportunity_narrative, str) or not opportunity_narrative.strip():
                opportunity_narrative = ""
            cluster_explanation = (
                f"Keyword belongs to cluster '{label_text}' ({keyword_count} related keywords). "
                f"Cluster membership boosts demand signal by {cluster_boost:.1f}."
            )
            if opportunity_narrative:
                cluster_explanation = (
                    f"{cluster_explanation} Cluster opportunity narrative: {opportunity_narrative.strip()}."
                )
            score_components["cluster_boost"] = ScoreComponent(
                value=cluster_boost,
                weight=0.0,
                raw=cluster_context.get("cluster_id"),
                note=cluster_explanation,
            )
            source_evidence.extend(
                [
                    "cluster_assignments.cluster_id",
                    "cluster_labels.keyword_count",
                ]
            )

        demand_score = round(min(100.0, max(0.0, base_demand_score + cluster_boost)), 2)
        confidence_modifier = max(0.0, 1.0 + sum(confidence_breakdown.values()))
        confidence_reason = (
            "Demand calculated from available components with deductions for missing external signals."
            if confidence_breakdown
            else "Demand calculated with full component coverage."
        )
        explanation_text = (
            "Demand combines Fiverr volume/autocomplete with Google Trends and Reddit intent"
            " signals where available."
        )
        if cluster_explanation:
            explanation_text = f"{explanation_text} {cluster_explanation}"
        return DemandScoreResult(
            keyword_id=keyword_id,
            score_value=demand_score,
            score_components=score_components,
            confidence_modifier=confidence_modifier,
            confidence_breakdown=confidence_breakdown,
            confidence_reason=confidence_reason,
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=explanation_text,
            total_weight_available=total_weight_available,
            trc_reliability=trc_reliability,
        )

    @staticmethod
    def _normalize_count(total_result_count: float) -> float:
        if total_result_count <= 0:
            return 0.0
        return min(100.0, (math.log10(total_result_count + 1.0) / 4.0) * 100.0)

    @staticmethod
    def _normalize_autocomplete_position(position: int) -> float:
        return max(0.0, 100.0 - float(position - 1) * 10.0)

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_demand_inputs"):
            loaded = db.get_demand_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        keyword = session.query(Keyword).filter(Keyword.id == keyword_id).first()
        total_result_count, search_strictness_used, sponsored_gig_count, total_gig_count = _resolve_marketplace_snapshot(
            session,
            keyword_id,
        )
        google_trends = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "google_trends",
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        reddit_demand = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "reddit_demand",
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        autocomplete_signal = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "autocomplete_position",
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        keyword_meta = keyword.metadata_json if keyword else {}
        return {
            "total_result_count": total_result_count,
            "autocomplete_position": self._as_int(keyword_meta.get("autocomplete_position")),
            "trends_12mo_score": self._signal_float(google_trends, "trends_12mo_score"),
            "reddit_demand_intent_score": self._signal_float(reddit_demand, "reddit_demand_intent_score"),
            "reddit_buyer_intent_ratio": self._signal_float(reddit_demand, "buyer_intent_ratio")
            or self._signal_float(reddit_demand, "intent_ratio"),
            "trends_signal": self._signal_json(google_trends),
            "reddit_signal": self._signal_json(reddit_demand),
            "autocomplete_data": self._signal_json(autocomplete_signal),
            "keyword_text": str(keyword.keyword) if keyword is not None else "",
            "niche_id": str(keyword.niche_id) if keyword is not None else "",
            SEARCH_STRICTNESS_COLUMN: search_strictness_used,
            "sponsored_gig_count": sponsored_gig_count,
            "total_gig_count": total_gig_count,
        }

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _signal_float(signal: ExternalSignal | None, key: str) -> float | None:
        if signal is None:
            return None
        raw_json = signal.raw_value_json if isinstance(signal.raw_value_json, dict) else {}
        raw_value = raw_json.get(key, signal.normalized_value)
        try:
            if raw_value is None:
                return None
            return float(raw_value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _signal_json(signal: ExternalSignal | None) -> dict[str, Any] | None:
        if signal is None:
            return None
        raw_json = signal.raw_value_json if isinstance(signal.raw_value_json, dict) else None
        if raw_json is not None:
            return raw_json
        return None
