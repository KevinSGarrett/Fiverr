"""Unit tests for recommendation orchestrator helper branches."""

from __future__ import annotations

from src.recommendations.contracts import RecommendationContext
from src.recommendations.orchestrator import RecommendationOrchestrator, _to_optional_int


def _context(run_id: str | int | None) -> RecommendationContext:
    return RecommendationContext(
        keyword_id=901,
        keyword_text="python automation",
        niche_id="1",
        niche_name="Automation",
        run_id=run_id,
        tag="STRONG GO",
        final_score=80.0,
        confidence_modifier=0.8,
        top_competitor_weaknesses=[],
    )


def test_orchestrator_generate_handles_non_numeric_run_id() -> None:
    output = RecommendationOrchestrator().generate(_context("run-xyz"))

    assert output.run_id is None
    assert output.generation_complete is False


def test_orchestrator_generate_coerces_numeric_run_id() -> None:
    output = RecommendationOrchestrator().generate(_context("42"))

    assert output.run_id == 42
    assert output.niche_id == "1"
    assert output.keyword == "python automation"


def test_to_optional_int_returns_none_for_invalid_values() -> None:
    assert _to_optional_int("invalid-int") is None


def test_to_optional_int_handles_none_and_numeric_values() -> None:
    assert _to_optional_int(None) is None
    assert _to_optional_int("7") == 7
