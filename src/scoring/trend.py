"""S4.9 Trend Score calculator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from src.models import ExternalSignal
from src.scoring.contracts import ScoreComponent, TrendScoreResult


class TrendScoreCalculator:
    """Calculate trend momentum from Google Trends plus placeholder external signals."""

    DEFAULT_WEIGHT = 0.05
    _SLOPE_WEIGHT = 0.40
    _ACCELERATION_WEIGHT = 0.25
    _REDDIT_TREND_WEIGHT = 0.15
    _LLM_TREND_WEIGHT = 0.20

    _LLM_CLASSIFICATION_MAP = {
        "STRONGLY_RISING": 100.0,
        "RISING": 75.0,
        "STABLE": 50.0,
        "DECLINING": 25.0,
        "STRONGLY_DECLINING": 0.0,
    }

    def calculate(self, keyword_id: int, db: Any) -> TrendScoreResult:
        """Calculate trend score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        slope_value = self._resolve_google_trends_slope(signals)
        if slope_value is not None:
            slope_score = self._normalize_slope_to_score(slope_value)
            score_components["google_trends_slope"] = ScoreComponent(
                value=slope_score,
                weight=self._SLOPE_WEIGHT,
                raw=slope_value,
            )
            weighted_sum += slope_score * self._SLOPE_WEIGHT
            total_weight_available += self._SLOPE_WEIGHT
            source_evidence.append("external_signals.google_trends.slope")
        else:
            confidence_breakdown["missing_google_trends"] = -0.15
            missing_data_warnings.append("Missing Google Trends slope signal.")

        acceleration_score = self._resolve_acceleration_score(signals)
        if acceleration_score is not None:
            score_components["google_trends_acceleration"] = ScoreComponent(
                value=acceleration_score,
                weight=self._ACCELERATION_WEIGHT,
                raw={
                    "trends_3mo_avg": signals.get("trends_3mo_avg"),
                    "trends_12mo_avg": signals.get("trends_12mo_avg"),
                    "trends_3mo_series": signals.get("google_trends_3mo_series"),
                    "trends_12mo_series": signals.get("google_trends_12mo_series"),
                },
            )
            weighted_sum += acceleration_score * self._ACCELERATION_WEIGHT
            total_weight_available += self._ACCELERATION_WEIGHT
            source_evidence.append("external_signals.google_trends.acceleration")

        reddit_score = self._resolve_reddit_trend_score(signals)
        if reddit_score is not None:
            score_components["reddit_activity_trend"] = ScoreComponent(
                value=reddit_score,
                weight=self._REDDIT_TREND_WEIGHT,
                raw={
                    "reddit_recent_post_volume": signals.get("reddit_recent_post_volume"),
                    "reddit_historical_post_volume": signals.get("reddit_historical_post_volume"),
                },
            )
            weighted_sum += reddit_score * self._REDDIT_TREND_WEIGHT
            total_weight_available += self._REDDIT_TREND_WEIGHT
            source_evidence.append("external_signals.reddit.activity")
        else:
            missing_data_warnings.append("reddit_not_implemented: missing Reddit activity trend signal.")

        llm_classification = self._resolve_llm_trend_classification(signals, missing_data_warnings)
        llm_score = self._LLM_CLASSIFICATION_MAP[llm_classification]
        score_components["llm_trend_classification"] = ScoreComponent(
            value=llm_score,
            weight=self._LLM_TREND_WEIGHT,
            raw=llm_classification,
        )
        weighted_sum += llm_score * self._LLM_TREND_WEIGHT
        total_weight_available += self._LLM_TREND_WEIGHT
        source_evidence.append("llm.trend_classification")

        if total_weight_available < 0.30:
            return TrendScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient trend signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate trend score.",
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
            )

        trend_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        return TrendScoreResult(
            keyword_id=keyword_id,
            score_value=trend_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason="Trend score blends slope, acceleration, Reddit activity, and LLM class.",
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text="Higher trend score indicates stronger demand momentum.",
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
        )

    def _resolve_google_trends_slope(self, signals: dict[str, Any]) -> float | None:
        explicit_slope = self._as_float(signals.get("google_trends_slope"))
        if explicit_slope is not None:
            return explicit_slope
        series = self._coerce_numeric_list(signals.get("google_trends_12mo_series"))
        if len(series) >= 2:
            return self._linear_slope(series)
        return None

    def _resolve_acceleration_score(self, signals: dict[str, Any]) -> float | None:
        avg_3mo = self._as_float(signals.get("trends_3mo_avg"))
        avg_12mo = self._as_float(signals.get("trends_12mo_avg"))

        if avg_3mo is None:
            series_3mo = self._coerce_numeric_list(signals.get("google_trends_3mo_series"))
            if series_3mo:
                avg_3mo = sum(series_3mo) / len(series_3mo)
        if avg_12mo is None:
            series_12mo = self._coerce_numeric_list(signals.get("google_trends_12mo_series"))
            if series_12mo:
                avg_12mo = sum(series_12mo) / len(series_12mo)

        if avg_3mo is None or avg_12mo is None or avg_12mo <= 0:
            return None

        ratio = avg_3mo / avg_12mo
        if ratio >= 1.30:
            return 100.0
        if ratio >= 1.10:
            return 75.0
        if ratio >= 0.95:
            return 50.0
        if ratio >= 0.80:
            return 25.0
        return 0.0

    def _resolve_reddit_trend_score(self, signals: dict[str, Any]) -> float | None:
        explicit_score = self._as_float(signals.get("reddit_activity_trend_score"))
        if explicit_score is not None:
            return self._normalize_percentage_score(explicit_score)

        recent_volume = self._as_float(signals.get("reddit_recent_post_volume"))
        historical_volume = self._as_float(signals.get("reddit_historical_post_volume"))
        if recent_volume is None or historical_volume is None or historical_volume <= 0:
            return None

        ratio = recent_volume / historical_volume
        raw = 50.0 + ((ratio - 1.0) * 100.0)
        return max(0.0, min(100.0, raw))

    def _resolve_llm_trend_classification(
        self,
        signals: dict[str, Any],
        warnings: list[str],
    ) -> str:
        raw_classification = signals.get("llm_trend_classification")
        if isinstance(raw_classification, str):
            normalized = raw_classification.strip().upper()
            if normalized in self._LLM_CLASSIFICATION_MAP:
                return normalized
        warnings.append("llm_not_implemented: defaulted llm_trend_classification to STABLE.")
        return "STABLE"

    @staticmethod
    def _linear_slope(values: list[float]) -> float:
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        x2_sum = sum(index * index for index in range(n))
        xy_sum = sum(index * value for index, value in enumerate(values))
        denominator = (n * x2_sum) - (x_sum * x_sum)
        if denominator == 0:
            return 0.0
        return ((n * xy_sum) - (x_sum * y_sum)) / denominator

    @staticmethod
    def _normalize_slope_to_score(slope: float) -> float:
        if slope <= -50.0:
            return 0.0
        if slope >= 50.0:
            return 100.0
        return max(0.0, min(100.0, 50.0 + slope))

    @staticmethod
    def _normalize_percentage_score(raw_value: float) -> float:
        if raw_value <= 1.0:
            return max(0.0, min(100.0, raw_value * 100.0))
        if raw_value <= 10.0:
            return max(0.0, min(100.0, raw_value * 10.0))
        return max(0.0, min(100.0, raw_value))

    @staticmethod
    def _coerce_numeric_list(value: Any) -> list[float]:
        if not isinstance(value, list):
            return []
        numeric_values: list[float] = []
        for item in value:
            try:
                numeric_values.append(float(item))
            except (TypeError, ValueError):
                continue
        return numeric_values

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_trend_inputs"):
            loaded = db.get_trend_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        google_trends = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type == "google_trends",
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        reddit = (
            session.query(ExternalSignal)
            .filter(
                ExternalSignal.keyword_id == keyword_id,
                ExternalSignal.signal_type.in_(["reddit_demand", "reddit_activity"]),
            )
            .order_by(ExternalSignal.created_at.desc())
            .first()
        )
        trends_raw = google_trends.raw_value_json if google_trends and isinstance(google_trends.raw_value_json, dict) else {}
        reddit_raw = reddit.raw_value_json if reddit and isinstance(reddit.raw_value_json, dict) else {}
        return {
            "trends_12mo_score": self._as_float(trends_raw.get("trends_12mo_score")),
            "trends_3mo_score": self._as_float(trends_raw.get("trends_3mo_score")),
            "trends_3mo_avg": self._as_float(trends_raw.get("trends_3mo_avg")),
            "trends_12mo_avg": self._as_float(trends_raw.get("trends_12mo_avg")),
            "google_trends_3mo_series": trends_raw.get("google_trends_3mo_series"),
            "google_trends_12mo_series": trends_raw.get("google_trends_12mo_series"),
            "google_trends_slope": self._as_float(trends_raw.get("google_trends_slope")),
            "reddit_activity_trend_score": self._as_float(
                reddit_raw.get("reddit_activity_trend_score", reddit_raw.get("reddit_activity_trend"))
            ),
            "reddit_recent_post_volume": self._as_float(reddit_raw.get("reddit_recent_post_volume")),
            "reddit_historical_post_volume": self._as_float(reddit_raw.get("reddit_historical_post_volume")),
        }

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
