"""S4.1 Demand Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from src.models import ExternalSignal, Keyword, SearchResult
from src.scoring.contracts import DemandScoreResult, ScoreComponent


class DemandScoreCalculator:
    """Calculate demand score from Fiverr, trends, and Reddit signals."""

    _COUNT_WEIGHT = 0.50
    _AUTOCOMPLETE_WEIGHT = 0.20
    _TRENDS_WEIGHT = 0.20
    _REDDIT_WEIGHT = 0.10

    def calculate(self, keyword_id: int, db: Any) -> DemandScoreResult:
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

        demand_score = weighted_sum / total_weight_available
        demand_score = round(min(100.0, max(0.0, demand_score)), 2)
        confidence_modifier = max(0.0, 1.0 + sum(confidence_breakdown.values()))
        confidence_reason = (
            "Demand calculated from available components with deductions for missing external signals."
            if confidence_breakdown
            else "Demand calculated with full component coverage."
        )
        return DemandScoreResult(
            keyword_id=keyword_id,
            score_value=demand_score,
            score_components=score_components,
            confidence_modifier=confidence_modifier,
            confidence_breakdown=confidence_breakdown,
            confidence_reason=confidence_reason,
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Demand combines Fiverr volume/autocomplete with Google Trends and Reddit intent"
                " signals where available."
            ),
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
        total_result_count = session.query(SearchResult).filter(SearchResult.keyword_id == keyword_id).count()
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
            "total_result_count": float(total_result_count) if total_result_count > 0 else None,
            "autocomplete_position": self._as_int(keyword_meta.get("autocomplete_position")),
            "trends_12mo_score": self._signal_float(google_trends, "trends_12mo_score"),
            "reddit_demand_intent_score": self._signal_float(reddit_demand, "reddit_demand_intent_score"),
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
