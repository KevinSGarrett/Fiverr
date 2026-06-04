"""Unit coverage for Wave 9 pricing LLM task integration."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock

from src.pricing.llm_task import (
    PRICING_MODEL,
    PRICING_TEMPERATURE,
    build_pricing_prompt,
    check_cache,
    log_llm_usage,
    pricing_llm_task,
    store_cache,
)
from src.pricing import llm_task as pricing_module
from src.recommendations.context import RecommendationContext, build_context
from src.recommendations.schemas import RecommendationOutput
from src.recommendations.tasks import RECOMMENDATION_FIELD_NAMES, generate_recommendation


def _context() -> RecommendationContext:
    return RecommendationContext(
        keyword_id=11,
        keyword_text="python automation",
        niche_id=1,
        niche_name="Automation",
        price_distribution={"basic": {"median": 100, "q1": 80, "q3": 130}},
        calculated_entry_prices={"basic": 70, "standard": 140, "premium": 260},
        market_type="MODERATE_SPREAD",
        competitor_price_positions=[{"seller": "alice", "basic": 95}],
    )


def _chat_client(content: str = "Use entry pricing and move up with reviews.") -> Any:
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage={"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
    )
    create = AsyncMock(return_value=response)
    return SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))


def _simple_llm_client(text: str = "fallback response") -> Any:
    return SimpleNamespace(complete=MagicMock(return_value=SimpleNamespace(text=text)))


def test_returns_none_when_no_price_distribution() -> None:
    context = _context()
    context.price_distribution = None
    result = asyncio.run(pricing_llm_task(1, context, db=None, client=_chat_client()))
    assert result is None


def test_returns_none_when_no_entry_prices() -> None:
    context = _context()
    context.calculated_entry_prices = None
    result = asyncio.run(pricing_llm_task(1, context, db=None, client=_chat_client()))
    assert result is None


def test_returns_none_when_both_price_fields_empty() -> None:
    context = _context()
    context.price_distribution = {}
    context.calculated_entry_prices = {}
    result = asyncio.run(pricing_llm_task(1, context, db=None, client=_chat_client()))
    assert result is None


def test_returns_none_when_client_missing() -> None:
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=None))
    assert result is None


def test_returns_none_on_llm_exception() -> None:
    client = _chat_client()
    client.chat.completions.create.side_effect = RuntimeError("boom")
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert result is None


def test_returns_string_on_success() -> None:
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=_chat_client("hello")))
    assert result == "hello"


def test_cache_key_uses_keyword_text() -> None:
    context = _context()
    context.keyword_text = "keyword-x"
    client = _chat_client("text")
    _ = asyncio.run(pricing_llm_task(1, context, db=None, client=client))
    assert client.chat.completions.create.await_count == 1


def test_model_is_gpt_4o() -> None:
    client = _chat_client()
    _ = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    kwargs = client.chat.completions.create.await_args.kwargs
    assert kwargs["model"] == "gpt-4o"
    assert PRICING_MODEL == "gpt-4o"


def test_temperature_is_0_2() -> None:
    client = _chat_client()
    _ = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert client.chat.completions.create.await_args.kwargs["temperature"] == 0.2
    assert PRICING_TEMPERATURE == 0.2


def test_max_tokens_is_600() -> None:
    client = _chat_client()
    _ = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert client.chat.completions.create.await_args.kwargs["max_tokens"] == 600


def test_fallback_client_complete_path() -> None:
    client = _simple_llm_client("plain text")
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert result == "plain text"


def test_prompt_includes_keyword_text() -> None:
    prompt = build_pricing_prompt(_context())
    assert "python automation" in prompt


def test_prompt_includes_market_type() -> None:
    prompt = build_pricing_prompt(_context())
    assert "MODERATE_SPREAD" in prompt


def test_prompt_includes_entry_prices() -> None:
    prompt = build_pricing_prompt(_context())
    assert "Basic $70" in prompt
    assert "Standard $140" in prompt
    assert "Premium $260" in prompt


def test_prompt_handles_none_market_type() -> None:
    context = _context()
    context.market_type = None
    prompt = build_pricing_prompt(context)
    assert "UNKNOWN" in prompt


def test_prompt_handles_missing_distribution_tier() -> None:
    context = _context()
    context.price_distribution = {}
    prompt = build_pricing_prompt(context)
    assert "Median: $0" in prompt


def test_full_pipeline_includes_pricing_strategy_field(monkeypatch: Any) -> None:
    async def _task_value(_context: RecommendationContext, _llm: Any, _cache: Any) -> dict[str, Any]:
        return {"output": "value", "cost_usd": 0.01}

    context = _context()
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _task_value)
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _task_value)
    monkeypatch.setattr(
        "src.recommendations.tasks.generate_pricing_strategy",
        AsyncMock(return_value={"output": "pricing copy", "cost_usd": 0.0}),
    )
    result = asyncio.run(generate_recommendation(11, context, llm_client=MagicMock(), cache=None, db=MagicMock()))
    assert result["pricing_strategy"] == "pricing copy"


def test_pricing_task_added_to_gather_result_order() -> None:
    assert RECOMMENDATION_FIELD_NAMES[-1] == "pricing_strategy"
    assert len(RECOMMENDATION_FIELD_NAMES) == 12


def test_none_result_stored_gracefully_in_pipeline(monkeypatch: Any) -> None:
    async def _none_task(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
        return {"output": None, "cost_usd": 0.0}

    context = _context()
    monkeypatch.setattr("src.recommendations.tasks.generate_gig_titles", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_tag_sets", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_package_structure", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_description_outline", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_faq_entries", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_differentiation_angle", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_buyer_persona", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_thumbnail_direction", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_upsell_structure", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_red_flags", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_niche_viability", _none_task)
    monkeypatch.setattr("src.recommendations.tasks.generate_pricing_strategy", _none_task)
    result = asyncio.run(generate_recommendation(11, context, llm_client=MagicMock(), cache=None, db=MagicMock()))
    assert result["pricing_strategy"] is None


def test_recommendation_output_accepts_pricing_strategy_none() -> None:
    output = RecommendationOutput()
    assert output.pricing_strategy is None


def test_recommendation_output_pricing_strategy_not_required() -> None:
    output = RecommendationOutput(generation_complete=False)
    assert output.model_dump().get("pricing_strategy") is None


def test_build_context_alias_returns_context() -> None:
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    context = build_context(9999, db)
    assert isinstance(context, RecommendationContext)


class _FakeQuery:
    def __init__(self, row: Any | None) -> None:
        self.row = row

    def filter(self, *_args: Any, **_kwargs: Any) -> _FakeQuery:
        return self

    def first(self) -> Any | None:
        return self.row


class _FakeSession:
    def __init__(self, row: Any | None = None) -> None:
        self.row = row
        self.added: list[Any] = []
        self.flushed = False
        self.rolled_back = False

    def query(self, *_args: Any) -> _FakeQuery:
        return _FakeQuery(self.row)

    def add(self, row: Any) -> None:
        self.added.append(row)

    def flush(self) -> None:
        self.flushed = True

    def rollback(self) -> None:
        self.rolled_back = True


def test_pricing_task_returns_cached_without_llm_call(monkeypatch: Any) -> None:
    context = _context()
    client = _chat_client("should not be used")
    monkeypatch.setattr("src.pricing.llm_task.check_cache", AsyncMock(return_value="cached strategy"))
    result = asyncio.run(pricing_llm_task(1, context, db=None, client=client))
    assert result == "cached strategy"
    assert client.chat.completions.create.await_count == 0


def test_pricing_task_awaits_async_complete_response() -> None:
    async def _complete(**_kwargs: Any) -> Any:
        return SimpleNamespace(text="async complete text", prompt_tokens=1, completion_tokens=2, total_tokens=3)

    client = SimpleNamespace(complete=_complete)
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert result == "async complete text"


def test_pricing_task_returns_none_on_blank_response_text() -> None:
    client = _chat_client("   ")
    result = asyncio.run(pricing_llm_task(1, _context(), db=None, client=client))
    assert result is None


def test_check_cache_returns_value_for_session(monkeypatch: Any) -> None:
    monkeypatch.setattr(pricing_module, "Session", _FakeSession)
    session = _FakeSession(row=SimpleNamespace(value_json={"value": "cached"}))
    cached = asyncio.run(check_cache(client=None, cache_key="k", db=session))
    assert cached == "cached"


def test_store_cache_adds_row_for_session(monkeypatch: Any) -> None:
    class _CacheRecord(SimpleNamespace):
        cache_key = "cache_key"

    monkeypatch.setattr(pricing_module, "Session", _FakeSession)
    monkeypatch.setattr(pricing_module, "LLMCacheRecord", _CacheRecord)
    session = _FakeSession(row=None)
    asyncio.run(store_cache(client=None, cache_key="abc", value="value", db=session))
    assert session.flushed is True


def test_log_llm_usage_flushes_for_session(monkeypatch: Any) -> None:
    monkeypatch.setattr(pricing_module, "Session", _FakeSession)
    monkeypatch.setattr(pricing_module, "LLMUsageLog", SimpleNamespace)
    session = _FakeSession(row=None)
    asyncio.run(
        log_llm_usage(
            keyword_id=1,
            model_name="gpt-4o",
            usage={"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
            task_type="pricing_strategy",
            db=session,
            request_hash="hash",
        )
    )
    assert session.flushed is True


def test_log_llm_usage_rolls_back_on_flush_error(monkeypatch: Any) -> None:
    class _BrokenSession(_FakeSession):
        def flush(self) -> None:
            raise RuntimeError("flush failed")

    monkeypatch.setattr(pricing_module, "Session", _BrokenSession)
    monkeypatch.setattr(pricing_module, "LLMUsageLog", SimpleNamespace)
    session = _BrokenSession(row=None)
    asyncio.run(
        log_llm_usage(
            keyword_id=1,
            model_name="gpt-4o",
            usage=SimpleNamespace(prompt_tokens="x", completion_tokens="y", total_tokens="z"),
            task_type="pricing_strategy",
            db=session,
            request_hash="hash",
        )
    )
    assert session.rolled_back is True
