"""S4.1 Demand Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.collection.search_url_builder import (
    SEARCH_STRICTNESS_COLUMN,
    UNCONSTRAINED_DEMAND_DEDUCTION,
    UNCONSTRAINED_NOTE,
)
from src.models import ClusterAssignment, ClusterLabel, ExternalSignal, Keyword, SearchResult
from src.scoring.contracts import DemandScoreResult, ScoreComponent

_DEFAULT_CLUSTER_BOOST = 5.0
_DEFAULT_MIN_CLUSTER_SIZE = 3
_R1_STRICTNESS_EFFECTIVE_DATE = date(2026, 5, 30)


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


def _resolve_marketplace_snapshot(session: Session, keyword_id: int) -> tuple[float | None, str | None]:
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
        return float(max_total_result_row.total_result_count), strictness

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
        return float(fallback_count), None
    return None, None


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

        total_result_count = self._as_float(signals.get("total_result_count"))
        if total_result_count is not None:
            count_score = self._normalize_count(total_result_count)
            score_components["fiverr_count"] = ScoreComponent(
                value=count_score,
                weight=self._COUNT_WEIGHT,
                raw=total_result_count,
            )
            weighted_sum += count_score * self._COUNT_WEIGHT
            total_weight_available += self._COUNT_WEIGHT
            source_evidence.append("fiverr_search_results.total_result_count")
        else:
            missing_data_warnings.append("Missing Fiverr total result count.")

        autocomplete_position = self._as_int(signals.get("autocomplete_position"))
        if autocomplete_position is None:
            score_components["autocomplete"] = ScoreComponent(
                value=0.0,
                weight=self._AUTOCOMPLETE_WEIGHT,
                raw=None,
                note="not in Fiverr autocomplete",
            )
            weighted_sum += 0.0
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
            trends_score = min(100.0, trends_12mo_score * 1.15)
            score_components["google_trends"] = ScoreComponent(
                value=trends_score,
                weight=self._TRENDS_WEIGHT,
                raw=trends_12mo_score,
            )
            weighted_sum += trends_score * self._TRENDS_WEIGHT
            total_weight_available += self._TRENDS_WEIGHT
            source_evidence.append("external_signals.google_trends.trends_12mo_score")
        else:
            confidence_breakdown["missing_google_trends"] = -0.15
            missing_data_warnings.append("Missing Google Trends 12-month score.")

        reddit_demand_intent_score = self._as_float(signals.get("reddit_demand_intent_score"))
        if reddit_demand_intent_score is not None:
            reddit_score = max(0.0, min(100.0, reddit_demand_intent_score * 10.0))
            score_components["reddit_intent"] = ScoreComponent(
                value=reddit_score,
                weight=self._REDDIT_WEIGHT,
                raw=reddit_demand_intent_score,
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
        search_strictness_used = str(signals.get(SEARCH_STRICTNESS_COLUMN) or "").strip() or None
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
        total_result_count, search_strictness_used = _resolve_marketplace_snapshot(session, keyword_id)
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
        keyword_meta = keyword.metadata_json if keyword else {}
        return {
            "total_result_count": total_result_count,
            "autocomplete_position": self._as_int(keyword_meta.get("autocomplete_position")),
            "trends_12mo_score": self._signal_float(google_trends, "trends_12mo_score"),
            "reddit_demand_intent_score": self._signal_float(reddit_demand, "reddit_demand_intent_score"),
            SEARCH_STRICTNESS_COLUMN: search_strictness_used,
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
