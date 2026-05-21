"""S4.3 Opportunity Score calculator."""

from __future__ import annotations

from typing import Any

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.contracts import (
    CompetitionScoreResult,
    DemandScoreResult,
    OpportunityScoreResult,
    ScoreComponent,
)
from src.scoring.demand import DemandScoreCalculator


class OpportunityScoreCalculator:
    """Calculate derived opportunity from demand and competition."""

    DEFAULT_WEIGHT = 0.25

    def __init__(
        self,
        demand_calculator: DemandScoreCalculator | None = None,
        competition_calculator: CompetitionScoreCalculator | None = None,
    ) -> None:
        self._demand_calculator = demand_calculator or DemandScoreCalculator()
        self._competition_calculator = competition_calculator or CompetitionScoreCalculator()

    def calculate(
        self,
        keyword_id: int,
        db: Any,
        demand_result: DemandScoreResult | None = None,
        competition_result: CompetitionScoreResult | None = None,
        config: dict[str, Any] | None = None,
    ) -> OpportunityScoreResult:
        """Calculate opportunity score using weighted demand minus weighted competition."""
        demand_payload = demand_result or self._demand_calculator.calculate(keyword_id, db)
        competition_payload = competition_result or self._competition_calculator.calculate(
            keyword_id,
            db,
            config=config,
        )

        demand_score = demand_payload.score_value
        competition_score = competition_payload.score_value
        if demand_score is None or competition_score is None:
            missing_data_warnings: list[str] = []
            if demand_score is None:
                missing_data_warnings.append("Demand score missing; cannot derive opportunity.")
            if competition_score is None:
                missing_data_warnings.append("Competition score missing; cannot derive opportunity.")
            return OpportunityScoreResult(
                keyword_id=keyword_id,
                score_value=None,
                score_components={},
                confidence_modifier=1.0,
                confidence_breakdown={},
                confidence_reason="Opportunity requires both demand and competition scores.",
                missing_data_warnings=missing_data_warnings,
                source_evidence=[],
                explanation_text=(
                    "Higher demand minus weighted competition = opportunity, but one or more"
                    " prerequisite scores are missing."
                ),
                demand_score=demand_score,
                competition_score=competition_score,
                default_weight=self.DEFAULT_WEIGHT,
            )

        raw_opportunity = (demand_score * 1.2) - (competition_score * 0.8)
        normalized_opportunity = self._normalize_0_100(raw_opportunity)
        score_components = {
            "weighted_demand": ScoreComponent(
                value=min(100.0, max(0.0, demand_score * 1.2)),
                weight=0.60,
                raw=demand_score,
                note="Demand weighted by 1.2 in derived opportunity formula.",
            ),
            "weighted_competition": ScoreComponent(
                value=min(100.0, max(0.0, competition_score * 0.8)),
                weight=0.40,
                raw=competition_score,
                note="Competition weighted by 0.8 and subtracted from demand.",
            ),
        }
        return OpportunityScoreResult(
            keyword_id=keyword_id,
            score_value=normalized_opportunity,
            score_components=score_components,
            confidence_modifier=min(
                demand_payload.confidence_modifier,
                competition_payload.confidence_modifier,
            ),
            confidence_breakdown={
                "demand_confidence_modifier": demand_payload.confidence_modifier,
                "competition_confidence_modifier": competition_payload.confidence_modifier,
            },
            confidence_reason=(
                "Derived from demand and competition scores; confidence follows the weaker"
                " upstream confidence modifier."
            ),
            missing_data_warnings=[],
            source_evidence=[
                "keyword_scores.demand_score",
                "keyword_scores.competition_score",
            ],
            explanation_text="Higher demand minus weighted competition = opportunity.",
            demand_score=demand_score,
            competition_score=competition_score,
            default_weight=self.DEFAULT_WEIGHT,
        )

    @staticmethod
    def _normalize_0_100(raw_score: float) -> float:
        normalized = ((raw_score + 80.0) / 200.0) * 100.0
        return round(min(100.0, max(0.0, normalized)), 2)
