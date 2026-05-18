"""S4.4 New Seller Feasibility Score calculator."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from src.models import SearchResult
from src.scoring.contracts import FeasibilityScoreResult, ScoreComponent


class NewSellerFeasibilityCalculator:
    """Calculate how feasible a keyword is for a brand-new seller."""

    DEFAULT_WEIGHT = 0.15
    _LEVEL1_RATIO_WEIGHT = 0.30
    _LOWEST_REVIEW_WEIGHT = 0.25
    _PRICE_DIVERSITY_WEIGHT = 0.15
    _LLM_WEAKNESS_WEIGHT = 0.20
    _LLM_ENTRY_GAP_WEIGHT = 0.10

    _TIER2_KEYWORD_MARKERS = ("python", "ai tool", "ai agent", "workflow", "scraping")

    def calculate(self, keyword_id: int, db: Any) -> FeasibilityScoreResult:
        """Calculate a feasibility score payload for the provided keyword."""
        signals = self._load_signals(keyword_id, db)
        score_components: dict[str, ScoreComponent] = {}
        missing_data_warnings: list[str] = []
        source_evidence: list[str] = []
        confidence_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight_available = 0.0

        level1_ratio = self._resolve_level1_ratio(signals)
        if level1_ratio is not None:
            level1_score = max(0.0, min(100.0, level1_ratio * 100.0))
            score_components["level1_or_new_ratio"] = ScoreComponent(
                value=level1_score,
                weight=self._LEVEL1_RATIO_WEIGHT,
                raw=level1_ratio,
            )
            weighted_sum += level1_score * self._LEVEL1_RATIO_WEIGHT
            total_weight_available += self._LEVEL1_RATIO_WEIGHT
            source_evidence.append("seller_profiles.level1_or_new_ratio_top10")
        else:
            missing_data_warnings.append("Missing Level 1 / no-level seller ratio in top 10.")

        lowest_review_count = self._as_float(signals.get("lowest_ranked_review_count_page1"))
        if lowest_review_count is not None:
            lowest_review_score = self._normalize_entry_review_barrier(lowest_review_count)
            score_components["lowest_ranked_review_barrier"] = ScoreComponent(
                value=lowest_review_score,
                weight=self._LOWEST_REVIEW_WEIGHT,
                raw=lowest_review_count,
            )
            weighted_sum += lowest_review_score * self._LOWEST_REVIEW_WEIGHT
            total_weight_available += self._LOWEST_REVIEW_WEIGHT
            source_evidence.append("gig_details.lowest_ranked_review_count_page1")
        else:
            missing_data_warnings.append("Missing review count of lowest-ranking gig on page 1.")

        price_diversity_signal = self._resolve_price_diversity_score(signals)
        if price_diversity_signal is not None:
            score_components["price_diversity"] = ScoreComponent(
                value=price_diversity_signal,
                weight=self._PRICE_DIVERSITY_WEIGHT,
                raw=signals.get("price_diversity_top10"),
            )
            weighted_sum += price_diversity_signal * self._PRICE_DIVERSITY_WEIGHT
            total_weight_available += self._PRICE_DIVERSITY_WEIGHT
            source_evidence.append("gig_details.price_diversity_top10")
        else:
            missing_data_warnings.append("Missing top-result price diversity signal.")

        llm_weakness_avg = self._as_float(signals.get("llm_gig_quality_weakness_avg_top10"))
        if llm_weakness_avg is not None:
            weakness_score = self._normalize_llm_score(llm_weakness_avg)
            score_components["llm_gig_weakness"] = ScoreComponent(
                value=weakness_score,
                weight=self._LLM_WEAKNESS_WEIGHT,
                raw=llm_weakness_avg,
            )
            weighted_sum += weakness_score * self._LLM_WEAKNESS_WEIGHT
            total_weight_available += self._LLM_WEAKNESS_WEIGHT
            source_evidence.append("llm.gig_quality_weakness_avg_top10")
        else:
            confidence_breakdown["missing_llm_gig_weakness"] = -0.10
            missing_data_warnings.append("llm_not_implemented: missing LLM gig weakness assessment.")

        llm_entry_gap_assessment = self._resolve_llm_entry_gap_assessment(signals)
        if llm_entry_gap_assessment is not None:
            llm_entry_score = self._normalize_llm_score(llm_entry_gap_assessment)
            score_components["llm_entry_gap"] = ScoreComponent(
                value=llm_entry_score,
                weight=self._LLM_ENTRY_GAP_WEIGHT,
                raw=llm_entry_gap_assessment,
            )
            weighted_sum += llm_entry_score * self._LLM_ENTRY_GAP_WEIGHT
            total_weight_available += self._LLM_ENTRY_GAP_WEIGHT
            source_evidence.append("llm.entry_gap_assessment")
        else:
            confidence_breakdown["missing_llm_entry_gap"] = -0.10
            missing_data_warnings.append("llm_not_implemented: missing LLM entry gap assessment.")

        niche_tier = self._resolve_niche_tier(signals)
        if total_weight_available < 0.30:
            return FeasibilityScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components=score_components,
                confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
                confidence_breakdown=confidence_breakdown,
                confidence_reason="Insufficient feasibility signal coverage (<30% available weight).",
                missing_data_warnings=missing_data_warnings,
                source_evidence=source_evidence,
                explanation_text="Insufficient data to generate a new seller feasibility explanation.",
                total_weight_available=total_weight_available,
                default_weight=self.DEFAULT_WEIGHT,
                niche_tier=niche_tier,
            )

        feasibility_score = round(min(100.0, max(0.0, weighted_sum / total_weight_available)), 2)
        tier_note = (
            "Tier 2 context: this signal is emphasized for new-seller entry decisions."
            if niche_tier == "tier2_standard"
            else "Tier 1 context: feasibility is informative but not dominant."
        )
        return FeasibilityScoreResult(
            keyword_id=keyword_id,
            score_value=feasibility_score,
            score_components=score_components,
            confidence_modifier=max(0.0, 1.0 + sum(confidence_breakdown.values())),
            confidence_breakdown=confidence_breakdown,
            confidence_reason=(
                "Feasibility calculated from marketplace entry signals with confidence deductions"
                " when LLM assessments are unavailable."
            ),
            missing_data_warnings=missing_data_warnings,
            source_evidence=source_evidence,
            explanation_text=(
                "Feasibility reflects entry accessibility for a new seller by combining level mix,"
                f" review barrier, price diversity, and LLM weakness/gap signals. {tier_note}"
            ),
            total_weight_available=total_weight_available,
            default_weight=self.DEFAULT_WEIGHT,
            niche_tier=niche_tier,
        )

    def _resolve_level1_ratio(self, signals: dict[str, Any]) -> float | None:
        explicit_ratio = self._as_float(signals.get("level1_or_new_ratio_top10"))
        if explicit_ratio is not None:
            return max(0.0, min(1.0, explicit_ratio))

        seller_levels = signals.get("top10_seller_levels")
        if not isinstance(seller_levels, list) or not seller_levels:
            return None

        accessible_count = 0
        for raw_level in seller_levels:
            level = str(raw_level or "").strip().lower()
            if level in {"", "none", "new", "new seller", "level 1", "level1", "1"}:
                accessible_count += 1
        return accessible_count / len(seller_levels)

    def _resolve_price_diversity_score(self, signals: dict[str, Any]) -> float | None:
        ratio = self._as_float(signals.get("price_diversity_top10"))
        if ratio is not None:
            if ratio <= 1.0:
                return max(0.0, min(100.0, ratio * 100.0))
            return max(0.0, min(100.0, ratio))

        prices = signals.get("top10_prices")
        if not isinstance(prices, list):
            return None
        valid_prices = [float(price) for price in prices if self._as_float(price) is not None]
        if len(valid_prices) < 2:
            return None
        avg_price = sum(valid_prices) / len(valid_prices)
        if avg_price <= 0:
            return 0.0
        variance = sum((price - avg_price) ** 2 for price in valid_prices) / len(valid_prices)
        coefficient_of_variation = math.sqrt(variance) / avg_price
        return max(0.0, min(100.0, coefficient_of_variation * 200.0))

    def _resolve_llm_entry_gap_assessment(self, signals: dict[str, Any]) -> float | None:
        value = self._as_float(signals.get("llm_entry_gap_assessment"))
        if value is not None:
            return value
        return self._llm_entry_gap_assessment_stub()

    @staticmethod
    def _llm_entry_gap_assessment_stub() -> float | None:
        return None

    def _resolve_niche_tier(self, signals: dict[str, Any]) -> str:
        explicit_tier = signals.get("niche_tier")
        if isinstance(explicit_tier, str) and explicit_tier.strip():
            return explicit_tier.strip()

        niche_name = str(signals.get("niche_name", "")).strip().lower()
        if any(marker in niche_name for marker in self._TIER2_KEYWORD_MARKERS):
            return "tier2_standard"
        return "tier1_full"

    @staticmethod
    def _normalize_entry_review_barrier(lowest_review_count: float) -> float:
        if lowest_review_count <= 0:
            return 100.0
        return max(0.0, min(100.0, 100.0 - (math.log10(lowest_review_count + 1.0) / 3.0) * 100.0))

    @staticmethod
    def _normalize_llm_score(raw_score: float) -> float:
        if raw_score <= 10.0:
            return max(0.0, min(100.0, raw_score * 10.0))
        return max(0.0, min(100.0, raw_score))

    def _load_signals(self, keyword_id: int, db: Any) -> dict[str, Any]:
        if db is None:
            return {}
        if isinstance(db, Session):
            return self._load_signals_from_db(keyword_id, db)
        if hasattr(db, "get_feasibility_inputs"):
            loaded = db.get_feasibility_inputs(keyword_id)
            return dict(loaded or {})
        if isinstance(db, Mapping):
            loaded = db.get(keyword_id, db)
            if isinstance(loaded, Mapping):
                return dict(loaded)
        return {}

    def _load_signals_from_db(self, keyword_id: int, session: Session) -> dict[str, Any]:
        top_results = (
            session.query(SearchResult)
            .filter(SearchResult.keyword_id == keyword_id, SearchResult.rank <= 10)
            .order_by(SearchResult.rank.asc())
            .all()
        )
        top_gigs = [result.gig for result in top_results if result.gig is not None]
        seller_levels = [str(gig.seller.level) for gig in top_gigs if gig.seller and gig.seller.level]
        accessible_levels = {"", "none", "new", "new seller", "level 1", "level1", "1"}
        accessible_count = sum(1 for level in seller_levels if level.strip().lower() in accessible_levels)
        review_candidates = [
            float(result.gig.review_count)
            for result in top_results
            if result.gig is not None and result.gig.review_count is not None
        ]
        prices = [float(gig.starting_price) for gig in top_gigs if gig.starting_price is not None]
        price_diversity = self._compute_price_diversity(prices)
        return {
            "level1_or_new_ratio_top10": (
                (accessible_count / len(seller_levels)) if seller_levels else None
            ),
            "top10_seller_levels": seller_levels or None,
            "lowest_ranked_review_count_page1": review_candidates[-1] if review_candidates else None,
            "price_diversity_top10": price_diversity,
            "top10_prices": prices or None,
            "llm_gig_quality_weakness_avg_top10": None,
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
    def _compute_price_diversity(prices: list[float]) -> float | None:
        if len(prices) < 2:
            return None
        avg_price = sum(prices) / len(prices)
        if avg_price <= 0:
            return 0.0
        variance = sum((price - avg_price) ** 2 for price in prices) / len(prices)
        std_dev = math.sqrt(variance)
        return max(0.0, min(1.0, std_dev / avg_price))
