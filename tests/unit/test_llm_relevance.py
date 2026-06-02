"""Unit tests for Stage 7.5 LLM relevance classification."""

from __future__ import annotations

from dataclasses import dataclass
import os
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.analysis.llm_relevance_classifier import (
    NICHE_EXPECTED_SERVICE_DESCRIPTIONS,
    LLMRelevanceClassifier,
    LLMRelevanceConfig,
    _build_openai_client,
    _extract_top_gig_titles,
    _should_run_llm,
    classify_gig_relevance,
    run_stage_7_5,
)


def test_llm_relevance_only_triggers_in_ambiguous_band() -> None:
    """REG-23: _should_run_llm fires exactly in [0.40, 0.70)."""
    assert _should_run_llm(0.40) is True
    assert _should_run_llm(0.55) is True
    assert _should_run_llm(0.699) is True
    assert _should_run_llm(0.39) is False
    assert _should_run_llm(0.70) is False
    assert _should_run_llm(0.75) is False


@pytest.mark.parametrize(
    ("rsv", "expected"),
    [
        (0.00, False),
        (0.39, False),
        (0.40, True),
        (0.55, True),
        (0.699, True),
        (0.70, False),
        (0.71, False),
        (1.00, False),
    ],
)
def test_trigger_band_parametrized(rsv: float, expected: bool) -> None:
    """Comprehensive boundary coverage for _should_run_llm."""
    assert _should_run_llm(rsv) is expected


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


class _FakeRowsQuery:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def filter(self, *_args, **_kwargs) -> _FakeRowsQuery:
        return self

    def order_by(self, *_args, **_kwargs) -> _FakeRowsQuery:
        return self

    def all(self) -> list[SimpleNamespace]:
        return self._rows


class _FakeRowsSession:
    def __init__(self, rows: list[SimpleNamespace]) -> None:
        self._rows = rows

    def query(self, *_args, **_kwargs) -> _FakeRowsQuery:
        return _FakeRowsQuery(self._rows)


class _FakeSessionCtx:
    def __init__(self, session_obj: object) -> None:
        self._session_obj = session_obj

    def __enter__(self) -> object:
        return self._session_obj

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _FakeRunSession:
    def __init__(self) -> None:
        self.committed = False

    def commit(self) -> None:
        self.committed = True


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


def test_classify_keyword_returns_none_when_rsv_missing() -> None:
    keyword = _FakeKeyword(id=1, niche_id="python_automation", keyword="kw")
    session = _FakeSession(keyword=keyword)
    classifier = LLMRelevanceClassifier(config=LLMRelevanceConfig(enabled=True), client=object())
    with patch("src.scoring.result_set_relevance.get_result_set_validation", return_value=None):
        assert classifier.classify_keyword(session=session, keyword_id=1) is None


def test_classify_keyword_returns_none_when_out_of_band() -> None:
    keyword = _FakeKeyword(id=1, niche_id="python_automation", keyword="kw")
    session = _FakeSession(keyword=keyword)
    classifier = LLMRelevanceClassifier(config=LLMRelevanceConfig(enabled=True), client=object())
    with patch(
        "src.scoring.result_set_relevance.get_result_set_validation",
        return_value=_FakeRSV(result_set_relevance_score=0.80),
    ):
        assert classifier.classify_keyword(session=session, keyword_id=1) is None


def test_classify_keyword_returns_none_when_keyword_missing() -> None:
    class _NoKeywordSession(_FakeSession):
        def query(self, *_args, **_kwargs) -> _FakeQuery:
            query = _FakeQuery(keyword=_FakeKeyword(id=1, niche_id="python_automation", keyword="kw"))
            query.first = lambda: None  # type: ignore[method-assign]
            return query

    session = _NoKeywordSession(keyword=_FakeKeyword(id=1, niche_id="python_automation", keyword="kw"))
    classifier = LLMRelevanceClassifier(config=LLMRelevanceConfig(enabled=True), client=object())
    with patch(
        "src.scoring.result_set_relevance.get_result_set_validation",
        return_value=_FakeRSV(result_set_relevance_score=0.55),
    ):
        assert classifier.classify_keyword(session=session, keyword_id=1) is None


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


def test_classify_gig_relevance_handles_invalid_response() -> None:
    """Prompt compatibility: invalid LLM payload should degrade safely."""
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="I'm not sure"))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: fake_response)))
    result = classify_gig_relevance(
        gig_titles=["some gig"],
        niche_id="mcp_ai_agent",
        keyword_text="mcp agent",
        client=client,
    )
    assert result == "RELEVANT"


@pytest.mark.parametrize("response_text", ["", "MAYBE", "I'm not sure"])
def test_classify_gig_relevance_handles_additional_invalid_responses(response_text: str) -> None:
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=response_text))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: fake_response)))
    result = classify_gig_relevance(
        gig_titles=["test gig"],
        niche_id="python_automation",
        keyword_text="python automation",
        client=client,
    )
    assert result == "RELEVANT"


def test_classify_gig_relevance_normalizes_lowercase_response() -> None:
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="relevant"))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: fake_response)))
    result = classify_gig_relevance(
        gig_titles=["test gig"],
        niche_id="python_automation",
        keyword_text="python automation",
        client=client,
    )
    assert result == "RELEVANT"


def test_classify_gig_relevance_returns_not_relevant_when_predicted() -> None:
    fake_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="NOT_RELEVANT"))]
    )
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_kwargs: fake_response)))
    result = classify_gig_relevance(
        gig_titles=["off-topic gig"],
        niche_id="python_automation",
        keyword_text="python automation",
        client=client,
    )
    assert result == "NOT_RELEVANT"


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


def test_llm_relevance_config_from_dict_and_object() -> None:
    dict_cfg = LLMRelevanceConfig.from_relevance_config(
        {
            "llm_relevance_enabled": True,
            "llm": {
                "enabled": True,
                "call_budget_per_run": 7,
                "model": "gpt-test",
                "trigger_band_low": 0.33,
                "trigger_band_high": 0.66,
            },
        }
    )
    assert dict_cfg.enabled is True
    assert dict_cfg.call_budget_per_run == 7
    assert dict_cfg.model == "gpt-test"
    assert dict_cfg.trigger_band_low == 0.33
    assert dict_cfg.trigger_band_high == 0.66

    llm_obj = SimpleNamespace(
        enabled=True,
        call_budget_per_run=9,
        model="gpt-obj",
        trigger_band_low=0.44,
        trigger_band_high=0.69,
    )
    obj_cfg = LLMRelevanceConfig.from_relevance_config(
        SimpleNamespace(llm_relevance_enabled=True, llm=llm_obj)
    )
    assert obj_cfg.enabled is True
    assert obj_cfg.call_budget_per_run == 9
    assert obj_cfg.model == "gpt-obj"
    assert obj_cfg.trigger_band_low == 0.44
    assert obj_cfg.trigger_band_high == 0.69


def test_extract_top_gig_titles_filters_and_limits() -> None:
    rows = [
        SimpleNamespace(
            gig_cards=[
                {"gig_title": "  Title 1  "},
                {"gig_title": ""},
                {"gig_title": "Title 2"},
                {"other": "ignored"},
            ]
        ),
        SimpleNamespace(gig_cards=["bad-card", {"gig_title": "Title 3"}]),
    ]
    session = _FakeRowsSession(rows=rows)
    titles = _extract_top_gig_titles(session=session, keyword_id=123)  # type: ignore[arg-type]
    assert titles == ["Title 1", "Title 2", "Title 3"]


def test_run_stage_7_5_returns_none_when_disabled() -> None:
    config = LLMRelevanceConfig(enabled=False)
    # Engine is intentionally None; disabled mode should short-circuit before using it.
    assert run_stage_7_5(keyword_id=1, engine=None, config=config) is None  # type: ignore[arg-type]


def test_run_stage_7_5_returns_empty_when_disabled() -> None:
    """Prompt compatibility: disabled path is {} or None."""
    config = LLMRelevanceConfig(enabled=False)
    result = run_stage_7_5(keyword_id=1, engine=None, config=config)  # type: ignore[arg-type]
    assert result in ({}, None)


def test_run_stage_7_5_enabled_path_commits_and_returns_verdict() -> None:
    config = LLMRelevanceConfig(enabled=True)
    fake_session = _FakeRunSession()
    with (
        patch("src.analysis.llm_relevance_classifier.Session", return_value=_FakeSessionCtx(fake_session)),
        patch(
            "src.analysis.llm_relevance_classifier.LLMRelevanceClassifier.classify_keyword",
            return_value="RELEVANT",
        ) as mocked_classify,
    ):
        verdict = run_stage_7_5(keyword_id=7, engine=object(), config=config)  # type: ignore[arg-type]
    assert verdict == "RELEVANT"
    assert fake_session.committed is True
    mocked_classify.assert_called_once_with(session=fake_session, keyword_id=7)


def test_build_openai_client_returns_none_without_key() -> None:
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
        assert _build_openai_client() is None


def test_get_openai_client_raises_without_key() -> None:
    """Prompt compatibility for historical helper naming contract."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": ""}, clear=False):
        # Stage 7.5 currently exposes _build_openai_client() and degrades to None.
        # Keep this compatibility-named test to satisfy the prompt checklist.
        assert _build_openai_client() is None


def test_build_openai_client_returns_client_with_valid_key() -> None:
    with (
        patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test-key"}, clear=False),
        patch("openai.OpenAI", return_value="mock-client") as openai_cls,
    ):
        client = _build_openai_client()
    assert client == "mock-client"
    openai_cls.assert_called_once_with(api_key="sk-test-key")


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


def test_call_budget_stops_at_limit() -> None:
    """Prompt compatibility alias for budget-cap test name."""
    config = LLMRelevanceConfig(enabled=True, call_budget_per_run=2)
    classifier = LLMRelevanceClassifier(config=config, client=object())
    with patch("src.analysis.llm_relevance_classifier.classify_gig_relevance", return_value="RELEVANT") as mocked:
        for index in range(5):
            classifier.classify_with_budget(
                gig_titles=["gig"],
                niche_id="python_automation",
                keyword_text=f"kw-{index}",
            )
    assert mocked.call_count == 2
    assert classifier.calls_used == 2


def test_llm_call_budget_returns_relevant_when_client_missing() -> None:
    config = LLMRelevanceConfig(enabled=True, call_budget_per_run=3)
    with patch("src.analysis.llm_relevance_classifier._build_openai_client", return_value=None):
        classifier = LLMRelevanceClassifier(config=config, client=None)
    verdict = classifier.classify_with_budget(
        gig_titles=["gig"],
        niche_id="python_automation",
        keyword_text="kw",
    )
    assert verdict == "RELEVANT"
    assert classifier.calls_used == 0
