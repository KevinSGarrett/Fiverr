"""Discovery pre-validation that reuses R2 result-set relevance logic."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.analysis.result_set_validator import (
    NICHE_VALIDATION_CONFIG,
    compute_gig_relevance,
    get_validation_config,
    validate_result_set,
)

R2_RELEVANT_THRESHOLD = 0.60


class DiscoveryVerdict(str, Enum):
    VALID = "VALID"
    GHOST = "GHOST"
    CONTAMINATED = "CONTAMINATED"


@dataclass(slots=True)
class PreValidationResult:
    candidate: str
    niche_id: str
    verdict: DiscoveryVerdict
    rsv: float
    reason: str


class DiscoveryPreValidator:
    """Dry-run validator for discovery candidates using existing result sets."""

    def __init__(self, relevant_threshold: float = R2_RELEVANT_THRESHOLD) -> None:
        self._relevant_threshold = relevant_threshold

    def evaluate(
        self,
        *,
        candidate: str,
        niche_id: str,
        provisional_result_set: list[dict[str, Any]],
    ) -> PreValidationResult:
        validation_config = NICHE_VALIDATION_CONFIG.get(niche_id) or get_validation_config(niche_id)
        validation = validate_result_set(
            provisional_result_set,
            keyword_text=candidate,
            niche_id=niche_id,
            validation_config=validation_config,
        )
        rsv = float(validation.result_set_relevance_score)

        if provisional_result_set:
            first_title = str(provisional_result_set[0].get("gig_title", ""))
            compute_gig_relevance(
                gig_title=first_title,
                keyword_text=candidate,
                niche_id=niche_id,
                validation_config=validation_config,
            )

        if validation.ghost_market_flag:
            return PreValidationResult(
                candidate=candidate,
                niche_id=niche_id,
                verdict=DiscoveryVerdict.GHOST,
                rsv=rsv,
                reason="ghost_market_result_set",
            )
        if validation.category_contamination_flag:
            return PreValidationResult(
                candidate=candidate,
                niche_id=niche_id,
                verdict=DiscoveryVerdict.CONTAMINATED,
                rsv=rsv,
                reason="contaminated_result_set",
            )
        if rsv >= self._relevant_threshold:
            return PreValidationResult(
                candidate=candidate,
                niche_id=niche_id,
                verdict=DiscoveryVerdict.VALID,
                rsv=rsv,
                reason="relevant_result_set",
            )
        return PreValidationResult(
            candidate=candidate,
            niche_id=niche_id,
            verdict=DiscoveryVerdict.CONTAMINATED,
            rsv=rsv,
            reason=f"rsv_below_threshold:{rsv:.2f}",
        )
