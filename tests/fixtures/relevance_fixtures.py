"""
Fixture factories for relevance and discovery outcome test data (R9.6, SCRUM-631).

All factories return in-memory ORM objects. No DB session is required for basic use.
"""
from __future__ import annotations

from src.models.discovery_outcome import DiscoveryOutcome
from src.models.result_set_validation import ResultSetValidation


def make_mock_result_set_validation(
    keyword_id: int = 1,
    relevance_score: float = 0.85,
    ghost_market_flag: bool = False,
    category_contamination_flag: bool = False,
    run_id: int | None = None,
) -> ResultSetValidation:
    """Build an in-memory RSV object for unit tests without DB."""
    rsv = ResultSetValidation()
    rsv.keyword_id = keyword_id
    rsv.result_set_relevance_score = relevance_score
    rsv.ghost_market_flag = ghost_market_flag
    rsv.category_contamination_flag = category_contamination_flag
    rsv.used_fallback_strictness = False
    rsv.relevance_deduction = 0.0 if relevance_score >= 0.80 else round(1.0 - relevance_score, 3)
    rsv.result_count = 10
    rsv.relevant_count = max(1, int(relevance_score * 10))
    rsv.sponsored_count = 0
    rsv.validation_method = "fixture_factory"
    rsv.search_strictness_used = "SUBCATEGORY"
    rsv.per_gig_relevance = {"source": "fixture", "score": relevance_score}
    rsv.ghost_evidence = {"reason": "ghost_detected"} if ghost_market_flag else None
    if run_id is not None:
        rsv.run_id = str(run_id)
    return rsv


def make_mock_discovery_outcome(
    run_id: str = "test_run",
    niche_id: str = "python_automation",
    keyword_text: str = "python script",
    is_invalid: bool = False,
    is_contaminated: bool = False,
    relevance_score: float | None = None,
    contamination_reason: str | None = None,
) -> DiscoveryOutcome:
    """Build an in-memory DiscoveryOutcome object for unit tests."""
    outcome = DiscoveryOutcome()
    outcome.run_id = run_id
    outcome.niche_id = niche_id
    outcome.keyword_text = keyword_text
    outcome.is_invalid = is_invalid
    outcome.is_contaminated = is_contaminated
    outcome.relevance_score = relevance_score
    outcome.contamination_reason = contamination_reason
    return outcome


def make_ghost_market_rsv(keyword_id: int = 1) -> ResultSetValidation:
    """Build an RSV with ghost_market_flag=True and relevance_score=0.10."""
    return make_mock_result_set_validation(
        keyword_id=keyword_id,
        relevance_score=0.10,
        ghost_market_flag=True,
        category_contamination_flag=False,
    )


def make_contaminated_rsv(keyword_id: int = 1) -> ResultSetValidation:
    """Build an RSV with category_contamination_flag=True and relevance_score=0.45."""
    return make_mock_result_set_validation(
        keyword_id=keyword_id,
        relevance_score=0.45,
        ghost_market_flag=False,
        category_contamination_flag=True,
    )


def make_clean_rsv(keyword_id: int = 1) -> ResultSetValidation:
    """Build an RSV with relevance_score=0.90 and both flags False."""
    return make_mock_result_set_validation(
        keyword_id=keyword_id,
        relevance_score=0.90,
        ghost_market_flag=False,
        category_contamination_flag=False,
    )
