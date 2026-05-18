"""S4.13 scoring orchestrator."""

from __future__ import annotations

import logging
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.confidence import ConfidenceScoreModifier
from src.scoring.contracts import ScoreDimension, ScoringInput, ScoringOutput, ScoringRunResult
from src.scoring.demand import DemandScoreCalculator
from src.scoring.feasibility import NewSellerFeasibilityCalculator
from src.scoring.final import FinalRecommendationScoreCalculator
from src.scoring.intent import ConversionIntentScoreCalculator
from src.scoring.opportunity import OpportunityScoreCalculator
from src.scoring.profitability import ProfitabilityScoreCalculator
from src.scoring.ranking import KeywordRanker
from src.scoring.saturation_score import SaturationScoreCalculator
from src.scoring.trend import TrendScoreCalculator
from src.scoring.weakness import GigQualityWeaknessScoreCalculator
from src.utils.datetime import timestamp_stamp

logger = logging.getLogger(__name__)


class ScoringOrchestrator:
    """Run the full scoring stack (S4.1-S4.13) for keyword batches."""

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        demand_calculator: DemandScoreCalculator | None = None,
        competition_calculator: CompetitionScoreCalculator | None = None,
        opportunity_calculator: OpportunityScoreCalculator | None = None,
        feasibility_calculator: NewSellerFeasibilityCalculator | None = None,
        profitability_calculator: ProfitabilityScoreCalculator | None = None,
        intent_calculator: ConversionIntentScoreCalculator | None = None,
        saturation_calculator: SaturationScoreCalculator | None = None,
        weakness_calculator: GigQualityWeaknessScoreCalculator | None = None,
        trend_calculator: TrendScoreCalculator | None = None,
        confidence_modifier: ConfidenceScoreModifier | None = None,
        final_calculator: FinalRecommendationScoreCalculator | None = None,
        keyword_ranker: KeywordRanker | None = None,
    ) -> None:
        self._weights = weights or {}
        self._demand_calculator = demand_calculator or DemandScoreCalculator()
        self._competition_calculator = competition_calculator or CompetitionScoreCalculator()
        self._opportunity_calculator = opportunity_calculator or OpportunityScoreCalculator()
        self._feasibility_calculator = feasibility_calculator or NewSellerFeasibilityCalculator()
        self._profitability_calculator = profitability_calculator or ProfitabilityScoreCalculator()
        self._intent_calculator = intent_calculator or ConversionIntentScoreCalculator()
        self._saturation_calculator = saturation_calculator or SaturationScoreCalculator()
        self._weakness_calculator = weakness_calculator or GigQualityWeaknessScoreCalculator()
        self._trend_calculator = trend_calculator or TrendScoreCalculator()
        self._confidence_modifier = confidence_modifier or ConfidenceScoreModifier()
        self._final_calculator = final_calculator or FinalRecommendationScoreCalculator()
        self._keyword_ranker = keyword_ranker or KeywordRanker()

    def run(self, keyword_ids: list[int], db: Any, profile: str = "default") -> ScoringRunResult:
        """Run all calculators, final score, and ranking for a keyword batch."""
        started_at = datetime.fromtimestamp(time.time(), tz=UTC)
        run_id = f"score_run_{timestamp_stamp(started_at)}"
        errors: list[str] = []
        keyword_results: list[dict[str, Any]] = []
        calculator_db: Any = db if isinstance(db, Session) else db

        for keyword_id in keyword_ids:
            try:
                demand_result = self._demand_calculator.calculate(keyword_id, calculator_db)
                competition_result = self._competition_calculator.calculate(keyword_id, calculator_db)
                opportunity_result = self._opportunity_calculator.calculate(
                    keyword_id,
                    calculator_db,
                    demand_result=demand_result,
                    competition_result=competition_result,
                )
                feasibility_result = self._feasibility_calculator.calculate(keyword_id, calculator_db)
                profitability_result = self._profitability_calculator.calculate(keyword_id, calculator_db)
                intent_result = self._intent_calculator.calculate(keyword_id, calculator_db)
                saturation_result = self._saturation_calculator.calculate(keyword_id, calculator_db)
                weakness_result = self._weakness_calculator.calculate(keyword_id, calculator_db)
                trend_result = self._trend_calculator.calculate(keyword_id, calculator_db)

                run_context = self._build_run_context(
                    demand_result=demand_result,
                    competition_result=competition_result,
                    opportunity_result=opportunity_result,
                    feasibility_result=feasibility_result,
                    profitability_result=profitability_result,
                    intent_result=intent_result,
                    saturation_result=saturation_result,
                    weakness_result=weakness_result,
                    trend_result=trend_result,
                )

                confidence_modifier = self._confidence_modifier.calculate(keyword_id, run_context, calculator_db)
                confidence_breakdown = dict(self._confidence_modifier.last_breakdown)

                component_scores = {
                    "demand_score": demand_result.score_value,
                    "competition_score": competition_result.score_value,
                    "opportunity_score": opportunity_result.score_value,
                    "feasibility_score": feasibility_result.score_value,
                    "profitability_score": profitability_result.score_value,
                    "intent_score": intent_result.score_value,
                    "saturation_score": saturation_result.score_value,
                    "weakness_score": weakness_result.score_value,
                    "trend_score": trend_result.score_value,
                    "confidence_modifier": confidence_modifier,
                }
                final_payload = self._final_calculator.calculate(
                    keyword_id=keyword_id,
                    profile=profile,
                    db={keyword_id: component_scores},
                )

                missing_warnings = (
                    demand_result.missing_data_warnings
                    + competition_result.missing_data_warnings
                    + opportunity_result.missing_data_warnings
                    + feasibility_result.missing_data_warnings
                    + profitability_result.missing_data_warnings
                    + intent_result.missing_data_warnings
                    + saturation_result.missing_data_warnings
                    + weakness_result.missing_data_warnings
                    + trend_result.missing_data_warnings
                )
                llm_warning_count = sum(
                    1 for warning in missing_warnings if "llm_not_implemented" in warning
                )
                if llm_warning_count:
                    errors.append(
                        f"keyword_id={keyword_id}: encountered {llm_warning_count} LLM stub warnings."
                    )

                keyword_results.append(
                    {
                        "keyword_id": keyword_id,
                        "profile_used": profile,
                        "scores": component_scores,
                        "confidence_breakdown": confidence_breakdown,
                        "missing_data_warnings": missing_warnings,
                        "final_score": final_payload["final_score"],
                        "tag": final_payload["tag"],
                        "final_payload": final_payload,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                message = f"keyword_id={keyword_id}: orchestrator failure: {exc}"
                logger.exception(message)
                errors.append(message)
                keyword_results.append(
                    {
                        "keyword_id": keyword_id,
                        "profile_used": profile,
                        "scores": {},
                        "confidence_breakdown": {},
                        "missing_data_warnings": [],
                        "final_score": 0.0,
                        "tag": "PASS",
                        "final_payload": {
                            "keyword_id": keyword_id,
                            "final_score": 0.0,
                            "tag": "PASS",
                            "profile_used": profile,
                            "weights_applied": {},
                            "component_scores": {},
                            "confidence_modifier": 0.0,
                            "missing_components": [],
                            "explanation_text": "Score failed in orchestrator.",
                        },
                    }
                )

        ranked_keywords = self._keyword_ranker.rank(keyword_results, profile=profile)
        grouped_rankings = self._keyword_ranker.grouped()
        completed_at = datetime.fromtimestamp(time.time(), tz=UTC)

        return ScoringRunResult(
            run_id=run_id,
            started_at=started_at,
            completed_at=completed_at,
            keyword_count=len(keyword_ids),
            profile_used=profile,
            keyword_results=keyword_results,
            ranked_keywords=ranked_keywords,
            grouped_rankings=grouped_rankings,
            errors=errors,
        )

    def score(self, scoring_input: ScoringInput) -> ScoringOutput:
        """Legacy compatibility wrapper for single-input scoring API."""
        if scoring_input.keyword_id is None:
            return ScoringOutput(
                run_id=scoring_input.run_id,
                keyword_id=scoring_input.keyword_id,
                gig_id=scoring_input.gig_id,
                seller_id=scoring_input.seller_id,
                profile_name=scoring_input.profile_name,
                composite_score=0.0,
                verdict="UNSCORED",
                explanation="Scoring not yet implemented — stub compatibility path.",
            )
        keyword_id = scoring_input.keyword_id if scoring_input.keyword_id is not None else -1
        db_payload = self._materialize_single_input_db(scoring_input)
        run_result = self.run(
            keyword_ids=[keyword_id],
            db=db_payload,
            profile=scoring_input.profile_name,
        )
        first_result = run_result.ranked_keywords[0] if run_result.ranked_keywords else {}
        final_payload = first_result.get("final_payload", {})
        final_score = float(final_payload.get("final_score", 0.0))
        tag = str(final_payload.get("tag", "UNSCORED"))
        return ScoringOutput(
            run_id=scoring_input.run_id,
            keyword_id=scoring_input.keyword_id,
            gig_id=scoring_input.gig_id,
            seller_id=scoring_input.seller_id,
            profile_name=scoring_input.profile_name,
            composite_score=final_score,
            verdict=tag,
            explanation=str(final_payload.get("explanation_text", "")),
            raw_json=final_payload,
        )

    def score_batch(self, inputs: list[ScoringInput]) -> list[ScoringOutput]:
        """Legacy compatibility wrapper for batch scoring API."""
        return [self.score(inp) for inp in inputs]

    def _compute_composite(self, dimensions: list[ScoreDimension]) -> float:
        """Compute normalized weighted composite for scaffold compatibility."""
        if not dimensions:
            return 0.0
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0.0:
            return 0.0
        weighted_sum = sum(d.value * d.weight for d in dimensions)
        return min(1.0, max(0.0, weighted_sum / total_weight))

    @staticmethod
    def _build_run_context(**results: Any) -> dict[str, Any]:
        score_values = [
            getattr(result, "score_value", None)
            for result in results.values()
        ]
        present_scores = sum(1 for value in score_values if value is not None)
        completeness_ratio = present_scores / max(1, len(score_values))
        warnings: list[str] = []
        source_evidence: list[str] = []
        missing_reddit_signal = False
        for result in results.values():
            warnings.extend(getattr(result, "missing_data_warnings", []))
            source_evidence.extend(getattr(result, "source_evidence", []))
            confidence_breakdown = getattr(result, "confidence_breakdown", {}) or {}
            if any("missing_reddit" in str(key) for key in confidence_breakdown):
                missing_reddit_signal = True
        reddit_signal_evidence = any("reddit" in entry.lower() for entry in source_evidence)
        reddit_warning_missing = any("reddit_not_implemented" in warning for warning in warnings)
        return {
            "data_completeness_ratio": completeness_ratio,
            "data_freshness_score": 1.0,
            "source_diversity_score": 1.0,
            "llm_analysis_completion_ratio": 1.0,
            "google_trends_available": getattr(results["trend_result"], "score_value", None) is not None,
            "gig_detail_collected": True,
            "seller_profiles_collected": True,
            "reddit_signals_available": (
                reddit_signal_evidence and not missing_reddit_signal and not reddit_warning_missing
            ),
            "llm_gig_quality_incomplete_count": sum(
                1 for warning in warnings if "llm_not_implemented" in warning
            ),
            "llm_competitor_synthesis_failed": any(
                "competitor" in warning and "llm_not_implemented" in warning
                for warning in warnings
            ),
            "data_age_hours": 0.0,
            "data_ttl_hours": 168.0,
            "mode": "standard",
        }

    @staticmethod
    def _materialize_single_input_db(scoring_input: ScoringInput) -> dict[int, dict[str, Any]]:
        keyword_id = scoring_input.keyword_id if scoring_input.keyword_id is not None else -1
        merged_signals: dict[str, Any] = {}
        merged_signals.update(scoring_input.demand_signals)
        merged_signals.update(scoring_input.competition_signals)
        merged_signals.update(scoring_input.opportunity_signals)
        merged_signals.update(scoring_input.feasibility_signals)
        merged_signals.update(scoring_input.profitability_signals)
        merged_signals.update(scoring_input.intent_signals)
        merged_signals.update(scoring_input.saturation_signals)
        merged_signals.update(scoring_input.weakness_signals)
        merged_signals.update(scoring_input.trend_signals)
        return {keyword_id: merged_signals}
