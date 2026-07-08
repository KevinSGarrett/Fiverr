"""S4.3 Opportunity Score calculator."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from src.scoring.competition import CompetitionScoreCalculator
from src.scoring.contracts import (
    CompetitionScoreResult,
    DemandScoreResult,
    OpportunityScoreResult,
    ScoreComponent,
)
from src.scoring.demand import DemandScoreCalculator
from src.scoring.intent import compute_intent_alignment_factor
from src.scoring.result_set_relevance import get_result_set_validation


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


_RELEVANCE_QUALIFIER_THRESHOLD = 0.70


def _opportunity_relevance_qualifier(rsv_relevance: float | None) -> float:
    """R4.7 (SCORING_INTEGRITY_EXTENSIONS.md / OPPORTUNITY_SCORE.md SRDI ADDENDUM):
    only qualify when the result set is contaminated (RSV < 0.70); a clean or
    absent RSV leaves the opportunity score unchanged. Below the threshold,
    scale by 0.50 + 0.50*rsv rather than by raw RSV directly -- e.g. RSV=0.60
    scales by 0.80, not 0.60 (Codex review, PR #175)."""
    if rsv_relevance is None or rsv_relevance >= _RELEVANCE_QUALIFIER_THRESHOLD:
        return 1.0
    return 0.50 + 0.50 * _clamp01(rsv_relevance)


def _opportunity_config(config: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    scoring_cfg = config.get("scoring")
    if not isinstance(scoring_cfg, Mapping):
        return {}
    opportunity_cfg = scoring_cfg.get("opportunity")
    if not isinstance(opportunity_cfg, Mapping):
        return {}
    return dict(opportunity_cfg)


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
        opportunity_relevance_factor: float | None = None
        if bool(_opportunity_config(config).get("qualify_by_relevance", False)):
            rsv = get_result_set_validation(keyword_id, db)
            rsv_relevance = (
                float(rsv.result_set_relevance_score)
                if rsv is not None and rsv.result_set_relevance_score is not None
                else None
            )
            if rsv_relevance is None and hasattr(db, "get_opportunity_inputs"):
                loaded = db.get_opportunity_inputs(keyword_id)
                if isinstance(loaded, Mapping):
                    rsv_relevance = _as_optional_float(loaded.get("rsv_relevance"))
            if rsv_relevance is None and isinstance(db, Mapping):
                loaded = db.get(keyword_id, db)
                if isinstance(loaded, Mapping):
                    rsv_relevance = _as_optional_float(loaded.get("rsv_relevance"))
            opportunity_relevance_factor = _opportunity_relevance_qualifier(rsv_relevance)

            intent_inputs: Mapping[str, Any] | None = None
            if hasattr(db, "get_intent_inputs"):
                loaded_intent = db.get_intent_inputs(keyword_id)
                if isinstance(loaded_intent, Mapping):
                    intent_inputs = loaded_intent
            elif isinstance(db, Mapping):
                loaded_intent = db.get(keyword_id, db)
                if isinstance(loaded_intent, Mapping):
                    intent_inputs = loaded_intent
            intent_alignment_factor = compute_intent_alignment_factor(
                query_intent=(
                    str(intent_inputs.get("query_intent_class"))
                    if isinstance(intent_inputs, Mapping) and intent_inputs.get("query_intent_class") is not None
                    else None
                ),
                service_intent=(
                    str(intent_inputs.get("service_intent_class"))
                    if isinstance(intent_inputs, Mapping) and intent_inputs.get("service_intent_class") is not None
                    else None
                ),
            )
            qualification_factor = opportunity_relevance_factor * intent_alignment_factor
            if raw_opportunity > 0:
                raw_opportunity = raw_opportunity * qualification_factor
            else:
                raw_opportunity = raw_opportunity * (2.0 - qualification_factor)
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
            opportunity_relevance_factor=opportunity_relevance_factor,
        )

    @staticmethod
    def _normalize_0_100(raw_score: float) -> float:
        normalized = ((raw_score + 80.0) / 200.0) * 100.0
        return round(min(100.0, max(0.0, normalized)), 2)
