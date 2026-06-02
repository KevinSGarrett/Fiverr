"""Unit tests for Stage 7.5 LLM relevance classification."""

from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

from src.analysis.llm_relevance_classifier import (
    NICHE_EXPECTED_SERVICE_DESCRIPTIONS,
    LLMRelevanceClassifier,
    LLMRelevanceConfig,
    _should_run_llm,
    classify_gig_relevance,
)


def test_llm_relevance_only_triggers_in_ambiguous_band() -> None:
    """REG-23: _should_run_llm fires exactly in [0.40, 0.70)."""
    assert _should_run_llm(0.40) is True
    assert _should_run_llm(0.55) is True
    assert _should_run_llm(0.699) is True
    assert _should_run_llm(0.39) is False
    assert _should_run_llm(0.70) is False
    assert _should_run_llm(0.75) is False


@dataclass
class _FakeRSV:
    result_set_relevance_score: float
    ghost_market_flag: bool = False
    relevance_deduction: float = 0.0


@dataclass
class _FakeKeyword:
    id: int
    niche_id: str
    keyword: str
    ghost_market_flag: bool = False


class _FakeQuery:
    def __init__(self, keyword: _FakeKeyword) -> None:
        self._keyword = keyword

    def filter(self, *_args, **_kwargs) -> _FakeQuery:
        return self

    def first(self) -> _FakeKeyword:
        return self._keyword


class _FakeSession:
    def __init__(self, keyword: _FakeKeyword) -> None:
        self._keyword = keyword

    def query(self, *_args, **_kwargs) -> _FakeQuery:
        return _FakeQuery(self._keyword)

    def flush(self) -> None:
        return None


def test_llm_ghost_verdict_blocks_recommendation() -> None:
    """REG-24: NOT_RELEVANT verdict forces ghost-block path semantics."""
    keyword = _FakeKeyword(id=42, niche_id="python_automation", keyword="python automation script")
    session = _FakeSession(keyword=keyword)
    rsv = _FakeRSV(result_set_relevance_score=0.55)
    config = LLMRelevanceConfig(enabled=True, call_budget_per_run=50)
    classifier = LLMRelevanceClassifier(config=config, client=object())

    with (
        patch("src.scoring.result_set_relevance.get_result_set_validation", return_value=rsv),
        patch("src.analysis.llm_relevance_classifier._extract_top_gig_titles", return_value=["Gig A", "Gig B"]),
        patch("src.analysis.llm_relevance_classifier.classify_gig_relevance", return_value="NOT_RELEVANT"),
    ):
        verdict = classifier.classify_keyword(session=session, keyword_id=42)

    assert verdict == "NOT_RELEVANT"
    assert rsv.ghost_market_flag is True
    assert rsv.relevance_deduction == -0.50
    assert keyword.ghost_market_flag is True


def test_classify_gig_relevance_returns_relevant_on_api_error() -> None:
    """Graceful degrade: API error returns RELEVANT."""
    failing_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(create=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("API down")))
        )
    )
    result = classify_gig_relevance(
        gig_titles=["test gig"],
        niche_id="python_automation",
        keyword_text="python automation",
        client=failing_client,
    )
    assert result == "RELEVANT"


def test_classify_gig_relevance_invalid_response_falls_back_to_relevant() -> None:
    """Unexpected response text is treated as RELEVANT."""
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="maybe"))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: fake_response)))
    result = classify_gig_relevance(
        gig_titles=["test gig"],
        niche_id="python_automation",
        keyword_text="python automation",
        client=client,
    )
    assert result == "RELEVANT"


def test_niche_service_descriptions_covers_all_9_niches() -> None:
    expected = {
        "prd_ai_saas",
        "support_kb_readiness",
        "gumloop_lindy_workflow",
        "mcp_ai_agent",
        "python_automation",
        "ai_tool_llm_integration",
        "ai_agent_development",
        "workflow_automation",
        "python_web_scraping",
    }
    assert set(NICHE_EXPECTED_SERVICE_DESCRIPTIONS.keys()) == expected


def test_llm_call_budget_stops_at_limit() -> None:
    config = LLMRelevanceConfig(enabled=True, call_budget_per_run=3)
    classifier = LLMRelevanceClassifier(config=config, client=object())

    with patch("src.analysis.llm_relevance_classifier.classify_gig_relevance", return_value="RELEVANT") as mocked:
        verdicts = [
            classifier.classify_with_budget(
                gig_titles=["gig"],
                niche_id="python_automation",
                keyword_text=f"kw-{index}",
            )
            for index in range(5)
        ]

    assert mocked.call_count == 3
    assert classifier.calls_used == 3
    assert verdicts == ["RELEVANT", "RELEVANT", "RELEVANT", "RELEVANT", "RELEVANT"]
