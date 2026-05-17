"""Scoring orchestrator stub.

Coordinates multi-dimension scoring and persists results.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-177.
"""

from __future__ import annotations

import logging

from src.scoring.contracts import ScoreDimension, ScoringInput, ScoringOutput

logger = logging.getLogger(__name__)

# Default scoring profile weights (mirrors config.yaml defaults)
_DEFAULT_WEIGHTS: dict[str, float] = {
    "demand": 0.20,
    "competition_inv": 0.20,
    "opportunity": 0.25,
    "feasibility": 0.10,
    "profitability": 0.10,
    "intent": 0.05,
    "saturation_inv": 0.05,
    "weakness": 0.03,
    "trend": 0.02,
}

_VERDICT_THRESHOLDS = {
    "GO": 0.80,
    "CONDITIONAL_GO": 0.60,
    "MONITOR": 0.40,
    "CAUTION": 0.20,
}


def _classify_verdict(composite: float) -> str:
    """Return GO/NO-GO verdict string based on composite score."""
    for verdict, threshold in _VERDICT_THRESHOLDS.items():
        if composite >= threshold:
            return verdict
    return "NO_GO"


class ScoringOrchestrator:
    """Orchestrate multi-dimension scoring for a keyword/gig/seller combination.

    This is a stub that will be fully implemented in SCRUM-177.
    Currently provides the interface contract and basic weighted composite logic.
    """

    def __init__(self, weights: dict[str, float] | None = None) -> None:
        self._weights = weights or _DEFAULT_WEIGHTS

    def score(self, scoring_input: ScoringInput) -> ScoringOutput:
        """Score a single input record.

        Stub implementation: returns UNSCORED output with zero composite.
        Full dimension scoring will be wired in SCRUM-165 through SCRUM-177.
        """
        logger.debug(
            "ScoringOrchestrator.score called for run_id=%s niche=%s — stub",
            scoring_input.run_id,
            scoring_input.niche_id,
        )
        output = ScoringOutput(
            run_id=scoring_input.run_id,
            keyword_id=scoring_input.keyword_id,
            gig_id=scoring_input.gig_id,
            seller_id=scoring_input.seller_id,
            profile_name=scoring_input.profile_name,
            composite_score=0.0,
            verdict="UNSCORED",
            explanation="Scoring not yet implemented — stub (SCRUM-177)",
        )
        return output

    def score_batch(self, inputs: list[ScoringInput]) -> list[ScoringOutput]:
        """Score a batch of inputs. Stub delegates to score()."""
        return [self.score(inp) for inp in inputs]

    def _compute_composite(self, dimensions: list[ScoreDimension]) -> float:
        """Compute weighted composite score from dimension list."""
        if not dimensions:
            return 0.0
        total_weight = sum(d.weight for d in dimensions)
        if total_weight == 0.0:
            return 0.0
        weighted_sum = sum(d.value * d.weight for d in dimensions)
        return min(1.0, max(0.0, weighted_sum / total_weight))
