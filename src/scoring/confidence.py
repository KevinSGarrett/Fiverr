"""S4.11 Confidence Score modifier calculator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ConfidenceScoreModifier:
    """Calculate confidence modifier used by final recommendation scoring."""

    def __init__(self) -> None:
        self.last_breakdown: dict[str, float] = {}

    def calculate(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> float:
        """Return the confidence modifier in range [0.0, 1.0]."""
        modifier, breakdown = self.calculate_with_breakdown(keyword_id, run_context, db)
        self.last_breakdown = breakdown
        return modifier

    def calculate_with_breakdown(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> tuple[float, dict[str, float]]:
        """Return confidence modifier and deduction breakdown."""
        context = self._load_context(keyword_id, run_context, db)

        completeness = self._clamp_0_1(self._as_float(context.get("data_completeness_ratio"), 1.0))
        freshness = self._clamp_0_1(self._as_float(context.get("data_freshness_score"), 1.0))
        diversity = self._clamp_0_1(self._as_float(context.get("source_diversity_score"), 1.0))
        llm_completion = self._clamp_0_1(self._as_float(context.get("llm_analysis_completion_ratio"), 1.0))

        base_modifier = ((completeness * 0.50) + (freshness * 0.30) + (diversity * 0.20)) * llm_completion

        deductions: dict[str, float] = {}
        if not self._as_bool(context.get("google_trends_available"), True):
            deductions["missing_google_trends"] = -0.15
        if not self._as_bool(context.get("gig_detail_collected"), True):
            deductions["missing_gig_detail"] = -0.20
        if not self._as_bool(context.get("seller_profiles_collected"), True):
            deductions["missing_seller_profiles"] = -0.10
        if not self._as_bool(context.get("reddit_signals_available"), True):
            deductions["missing_reddit_signals"] = -0.05

        incomplete_gig_count = max(0.0, self._as_float(context.get("llm_gig_quality_incomplete_count"), 0.0))
        llm_gig_quality_penalty = max(-0.20, -(incomplete_gig_count * 0.08))
        if llm_gig_quality_penalty < 0:
            deductions["llm_gig_quality_incomplete"] = llm_gig_quality_penalty

        if self._as_bool(context.get("llm_competitor_synthesis_failed"), False):
            deductions["llm_competitor_synthesis_failed"] = -0.10

        data_age_hours = self._as_float(context.get("data_age_hours"), 0.0)
        data_ttl_hours = self._as_float(context.get("data_ttl_hours"), 168.0)
        if data_ttl_hours > 0 and data_age_hours > (2.0 * data_ttl_hours):
            deductions["data_stale_over_2x_ttl"] = -0.15

        mode = str(context.get("mode", "")).strip().lower()
        if mode in {"keyword_only", "feasibility"}:
            deductions["partial_depth_mode"] = -0.25

        deduction_total = sum(deductions.values())
        raw_modifier = base_modifier + deduction_total
        final_modifier = self._clamp_0_1(raw_modifier)

        breakdown: dict[str, float] = {
            "data_completeness_ratio": completeness,
            "data_freshness_score": freshness,
            "source_diversity_score": diversity,
            "llm_analysis_completion_ratio": llm_completion,
            "base_modifier": round(base_modifier, 4),
        }
        breakdown.update({key: round(value, 4) for key, value in deductions.items()})
        breakdown["deduction_total"] = round(deduction_total, 4)
        breakdown["remaining_modifier"] = round(final_modifier, 4)

        return round(final_modifier, 4), breakdown

    def _load_context(
        self,
        keyword_id: int,
        run_context: dict[str, Any] | None,
        db: Any,
    ) -> dict[str, Any]:
        context = dict(run_context or {})
        if context:
            return context
        if db is not None and hasattr(db, "get_confidence_inputs"):
            loaded = db.get_confidence_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            if value is None:
                return default
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_bool(value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return default
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        return default

    @staticmethod
    def _clamp_0_1(value: float) -> float:
        return max(0.0, min(1.0, value))
