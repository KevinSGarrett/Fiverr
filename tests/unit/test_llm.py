"""Unit tests for LLM client, cache, and prompt rendering."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import src.llm.cache as cache_module
from src.llm import (
    PRICING_PER_1K_TOKENS,
    LLMCache,
    LLMClient,
    TemplateRenderer,
    build_cache_key,
    build_validation_retry_prompt,
)


class StubProvider:
    """Test double for complete/embed provider methods."""

    def __init__(self) -> None:
        self.complete_calls = 0

    def complete(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del model, temperature, response_format
        self.complete_calls += 1
        return {
            "text": f"processed: {prompt}",
            "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
        }

    def embed(self, texts: list[str], model: str) -> dict[str, Any]:
        del model
        return {
            "embeddings": [[float(len(text))] for text in texts],
            "usage": {"prompt_tokens": 10},
        }


def test_mocked_complete_returns_text_and_metadata() -> None:
    provider = StubProvider()
    client = LLMClient(provider=provider, cache=LLMCache(db_path=None), cache_ttl_hours=24)

    result = client.complete("hello world", model="gpt-4o-mini", temperature=0.2)

    assert result.text == "processed: hello world"
    assert result.metadata["model"] == "gpt-4o-mini"
    assert result.metadata["temperature"] == 0.2
    assert result.metadata["cache_hit"] is False
    assert len(result.metadata["prompt_hash"]) == 64
    assert result.metadata["prompt_tokens"] == 1000
    assert result.metadata["completion_tokens"] == 500
    assert result.metadata["total_tokens"] == 1500
    assert result.metadata["estimated_cost_usd"] > 0.0


def test_cost_calculation_matches_known_formula() -> None:
    prompt_tokens = 1000
    completion_tokens = 500
    pricing = PRICING_PER_1K_TOKENS["gpt-4o-mini"]
    expected = round(
        (prompt_tokens / 1000) * pricing["input"]
        + (completion_tokens / 1000) * pricing["output"],
        8,
    )

    cost = LLMClient.calculate_cost_usd("gpt-4o-mini", prompt_tokens, completion_tokens)
    assert cost == expected


def test_build_cache_key_is_deterministic_and_sha256_hex() -> None:
    key_a = build_cache_key("gpt-4o-mini", 0.2, "my prompt")
    key_b = build_cache_key("gpt-4o-mini", 0.2, "my prompt")

    assert key_a == key_b
    assert len(key_a) == 64
    assert all(char in "0123456789abcdef" for char in key_a)


def test_identical_requests_hit_cache_on_second_lookup() -> None:
    provider = StubProvider()
    cache = LLMCache(db_path=None)
    client = LLMClient(provider=provider, cache=cache, cache_ttl_hours=24)

    first = client.complete("cache me", model="gpt-4o-mini")
    second = client.complete("cache me", model="gpt-4o-mini")

    assert provider.complete_calls == 1
    assert first.text == second.text
    assert second.metadata["cache_hit"] is True


def test_ttl_expiration_returns_cache_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = LLMCache(db_path=None)
    key = build_cache_key("gpt-4o-mini", 0.2, "expiring prompt")
    cache.set(key, {"text": "stale", "metadata": {}}, ttl_hours=1)
    assert cache.get(key) is not None

    future_time = datetime.now(UTC) + timedelta(hours=2)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            del cls
            return future_time if tz is not None else future_time.replace(tzinfo=None)

    monkeypatch.setattr(cache_module, "datetime", FrozenDateTime)

    assert cache.get(key) is None


def test_template_renderer_renders_temp_template(tmp_path: Path) -> None:
    template_file = tmp_path / "hello.j2"
    template_file.write_text("Hello {{ name }}!", encoding="utf-8")

    renderer = TemplateRenderer(template_dir=tmp_path)
    rendered = renderer.render_template("hello.j2", {"name": "Kevin"})

    assert rendered == "Hello Kevin!"


def test_template_renderer_raises_for_missing_template(tmp_path: Path) -> None:
    renderer = TemplateRenderer(template_dir=tmp_path)

    with pytest.raises(FileNotFoundError, match="Template 'missing.j2' not found"):
        renderer.render_template("missing.j2", {})


def test_validation_retry_prompt_includes_guidance_without_leaking_keys() -> None:
    prompt = "Use API key sk-test1234567890abcdef to proceed."
    retry = build_validation_retry_prompt(prompt, ValueError("field 'score' missing"))

    assert "Validation failed" in retry
    assert "schema and constraints" in retry
    assert "sk-test1234567890abcdef" not in retry
