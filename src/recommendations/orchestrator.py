"""Recommendation engine orchestrator stub — E05 scaffold."""

from __future__ import annotations

from src.recommendations.contracts import RecommendationContext, RecommendationOutput


class RecommendationOrchestrator:
    """Stub orchestrator for the recommendation engine (E05).

    Full implementation is deferred to E05 stories (SCRUM-178 through SCRUM-186).
    This stub satisfies import-time requirements and provides the public interface
    that dependent modules can code against.
    """

    def generate(self, context: RecommendationContext) -> RecommendationOutput:
        """Generate a full recommendation for a keyword.

        Args:
            context: Assembled recommendation context.

        Returns:
            :class:`RecommendationOutput` with ``generation_complete=False``
            until full E05 implementation is wired.
        """
        return RecommendationOutput(
            niche_id=context.niche_id,
            keyword=context.keyword,
            run_id=context.run_id,
            generation_complete=False,
        )
