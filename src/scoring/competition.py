"""S4.2 Competition Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from src.scoring.contracts import CompetitionScoreResult, ScoreComponent


class CompetitionScoreCalculator:
    """Calculate competition strength from marketplace and seller signals."""

    _COUNT_WEIGHT = 0.20
    _REVIEWS_WEIGHT = 0.25
    _SELLER_LEVEL_WEIGHT = 0.20
    _HUNDRED_PLUS_WEIGHT = 0.15
    _PRO_VERIFIED_WEIGHT = 0.10
    _PRICE_WEIGHT = 0.05
    _LLM_WEIGHT = 0.05

    _LEVEL_MAP = {
        "level 1": 20.0,
        "level1": 20.0,
        "1": 20.0,
        "level 2": 60.0,
        "level2": 60.0,
        "2": 60.0,
        "top rated": 100.0,
        "top rated seller": 100.0,
        "trs": 100.0,
        "pro": 100.0,
    }

    def calculate(self, keyword_id: int, db: Any) -> CompetitionScoreResult:
        """Calculate a competition score payload for the provided keyword."""
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

        avg_review_count_top10 = self._as_float(signals.get("avg_review_count_top10"))
        if avg_review_count_top10 is not None:
            review_score = self._normalize_review_count(avg_review_count_top10)
            score_components["avg_reviews"] = ScoreComponent(
                value=review_score,
                weight=self._REVIEWS_WEIGHT,
                raw=avg_review_count_top10,
            )
            weighted_sum += review_score * self._REVIEWS_WEIGHT
            total_weight_available += self._REVIEWS_WEIGHT
            source_evidence.append("gig_details.avg_review_count_top10")
        else:
            missing_data_warnings.append("Missing average review count for top 10 gigs.")

        avg_seller_level_top10 = signals.get("avg_seller_level_top10")
        seller_level_score = self._normalize_seller_level(avg_seller_level_top10)
        if seller_level_score is not None:
            score_components["seller_level"] = ScoreComponent(
                value=seller_level_score,
                weight=self._SELLER_LEVEL_WEIGHT,
                raw=avg_seller_level_top10,
            )
            weighted_sum += seller_level_score * self._SELLER_LEVEL_WEIGHT
            total_weight_available += self._SELLER_LEVEL_WEIGHT
            source_evidence.append("seller_profiles.avg_seller_level_top10")
        else:
            missing_data_warnings.append("Missing average seller level in top 10 gigs.")

        proportion_with_100_plus_reviews = self._as_float(signals.get("proportion_with_100_plus_reviews"))
        if proportion_with_100_plus_reviews is not None:
            clamped_ratio = max(0.0, min(1.0, proportion_with_100_plus_reviews))
            ratio_score = clamped_ratio * 100.0
            score_components["hundred_plus_review_ratio"] = ScoreComponent(
                value=ratio_score,
                weight=self._HUNDRED_PLUS_WEIGHT,
                raw=proportion_with_100_plus_reviews,
            )
            weighted_sum += ratio_score * self._HUNDRED_PLUS_WEIGHT
            total_weight_available += self._HUNDRED_PLUS_WEIGHT
            source_evidence.append("gig_details.proportion_with_100_plus_reviews")
        else:
            missing_data_warnings.append("Missing 100+ reviews ratio in top 10 gigs.")

        pro_verified_presence_ratio = self._as_float(signals.get("pro_verified_presence_ratio"))
        if pro_verified_presence_ratio is not None:
            pro_ratio_score = max(0.0, min(1.0, pro_verified_presence_ratio)) * 100.0
            score_components["pro_verified_presence"] = ScoreComponent(
                value=pro_ratio_score,
                weight=self._PRO_VERIFIED_WEIGHT,
                raw=pro_verified_presence_ratio,
            )
            weighted_sum += pro_ratio_score * self._PRO_VERIFIED_WEIGHT
            total_weight_available += self._PRO_VERIFIED_WEIGHT
            source_evidence.append("seller_profiles.pro_verified_presence_ratio")
        else:
            missing_data_warnings.append("Missing pro-verified seller presence ratio.")

        avg_starting_price_top10 = self._as_float(signals.get("avg_starting_price_top10"))
        if avg_starting_price_top10 is not None:
            price_score = self._normalize_price(avg_starting_price_top10)
            score_components["avg_starting_price"] = ScoreComponent(
                value=price_score,
                weight=self._PRICE_WEIGHT,
                raw=avg_starting_price_top10,
            )
            weighted_sum += price_score * self._PRICE_WEIGHT
            total_weight_available += self._PRICE_WEIGHT
            source_evidence.append("gig_details.avg_starting_price_top10")
        else:
            missing_data_warnings.append("Missing average starting price for top 10 gigs.")

        llm_competitor_strength_rating = self._as_float(signals.get("llm_competitor_strength_rating"))
        if llm_competitor_strength_rating is not None:
            llm_score = self._normalize_llm_competitor_strength(llm_competitor_strength_rating)
            score_components["llm_competitor_strength"] = ScoreComponent(
                value=llm_score,
                weight=self._LLM_WEIGHT,
                raw=llm_competitor_strength_rating,
            )
            weighted_sum += llm_score * self._LLM_WEIGHT
            total_weight_available += self._LLM_WEIGHT
            source_evidence.append("llm.competitor_strength_rating")
        else:
            confidence_breakdown["missing_llm_competitor_strength"] = -0.10
            missing_data_warnings.append("Missing LLM competitor strength rating.")

        missing_gig_detail_fields = [
            "avg_review_count_top10",
            "avg_seller_level_top10",
            "proportion_with_100_plus_reviews",
            "pro_verified_presence_ratio",
            "avg_starting_price_top10",
        ]
        if not any(self._has_value(signals.get(field_name)) for field_name in missing_gig_detail_fields):
            confidence_breakdown["missing_gig_detail_dataset"] = -0.20

        if total_weight_available < 0.30:
            return CompetitionScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient competition signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate a competition explanation.",
                total_weight_available=total_weight_available,
            )

        competition_score = weighted_sum / total_weight_available
        competition_score = round(min(100.0, max(0.0, competition_score)), 2)
        return CompetitionScoreResult(
            keyword_id=keyword_id,
            score_value=competition_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Competition calculated from available marketplace strength signals"
                " with confidence penalties for missing data."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Competition reflects how entrenched the top listings are by review density,"
                " seller seniority, pro presence, pricing, and optional LLM synthesis."
            ),
            total_weight_available=total_weight_available,
        )

    @staticmethod
    def _normalize_count(total_result_count: float) -> float:
        if total_result_count <= 0:
            return 0.0
        return min(100.0, (math.log10(total_result_count + 1.0) / 4.0) * 100.0)

    @staticmethod
    def _normalize_review_count(avg_review_count: float) -> float:
        if avg_review_count <= 0:
            return 0.0
        return min(100.0, (math.log10(avg_review_count + 1.0) / 4.0) * 100.0)

    def _normalize_seller_level(self, raw_level: Any) -> float | None:
        if raw_level is None:
            return None
        if isinstance(raw_level, int | float):
            if raw_level <= 3:
                return max(0.0, min(100.0, float(raw_level) * 20.0))
            return max(0.0, min(100.0, float(raw_level)))
        if isinstance(raw_level, str):
            normalized = raw_level.strip().lower()
            return self._LEVEL_MAP.get(normalized)
        return None

    @staticmethod
    def _normalize_price(avg_price: float) -> float:
        if avg_price <= 0:
            return 0.0
        return min(100.0, avg_price * 2.0)

    @staticmethod
    def _normalize_llm_competitor_strength(raw_rating: float) -> float:
        if raw_rating <= 10.0:
            return max(0.0, min(100.0, raw_rating * 10.0))
        return max(0.0, min(100.0, raw_rating))

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if hasattr(db, "get_competition_inputs"):
            loaded = db.get_competition_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    @staticmethod
    def _as_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _has_value(value: Any) -> bool:
        return value is not None
