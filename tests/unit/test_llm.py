"""Unit tests for LLM provider, cache, validation, retry, and cost controls."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
import src.llm.cache as cache_module
from pydantic import BaseModel
from src.llm import (
    CachePolicy,
    LLMCache,
    LLMClient,
    LLMRetryPolicy,
    LLMValidationError,
    MockLLMProvider,
    OpenAIProvider,
    build_cache_key,
    build_self_correction_prompt,
    build_validation_retry_prompt,
    estimate_llm_cost,
    parse_json_response,
)
from src.llm.retry import LLMRateLimitError


class CountingMockProvider(MockLLMProvider):
    """Mock provider that tracks completion invocations."""

    def __init__(self, completion_text: str = "mock response") -> None:
        super().__init__(completion_text=completion_text, embedding_value=1.0)
        self.complete_calls = 0

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.complete_calls += 1
        return super().complete(
            prompt=prompt,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )


class DemoSchema(BaseModel):
    name: str
    score: int


class StringOnlyProvider:
    provider_name = "string-only"

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        del prompt, model, temperature, response_format
        return "plain-text-payload"


class IncompleteProvider:
    provider_name = "incomplete"


def test_mock_provider_completion_works() -> None:
    provider = CountingMockProvider(completion_text="processed")
    client = LLMClient(provider=provider, cache=LLMCache(db_path=None))

    result = client.complete("hello world", model="gpt-4o-mini", temperature=0.2)

    assert result.text == "processed"
    assert provider.complete_calls == 1
    assert result.metadata["cache_hit"] is False
    assert result.metadata["provider_name"] == "mock"


def test_llm_client_does_not_require_openai_key_with_injected_mock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    client = LLMClient(provider=MockLLMProvider(completion_text="ok"))
    result = client.complete("safe prompt")

    assert result.text == "ok"


def test_openai_provider_missing_key_fails_only_on_construction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient(provider=MockLLMProvider())
    assert client is not None

    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        OpenAIProvider()


def test_llm_client_rejects_conflicting_provider_configuration() -> None:
    with pytest.raises(ValueError, match="either 'provider' or 'use_openai_provider=True'"):
        LLMClient(provider=MockLLMProvider(), use_openai_provider=True)


class _FakeChatCompletions:
    def __init__(self, holder: dict) -> None:
        self._holder = holder

    def create(self, **kwargs):
        from types import SimpleNamespace
        self._holder["kwargs"] = kwargs
        return SimpleNamespace(
            model=kwargs["model"],
            choices=[SimpleNamespace(
                message=SimpleNamespace(content="real answer"),
                finish_reason="stop",
            )],
            usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
        )


class _FakeEmbeddings:
    def create(self, **kwargs):
        from types import SimpleNamespace
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3]) for _ in kwargs["input"]],
            usage=SimpleNamespace(prompt_tokens=5),
        )


class _FakeOpenAIClient:
    def __init__(self) -> None:
        from types import SimpleNamespace
        self._holder: dict = {}
        self.chat = SimpleNamespace(completions=_FakeChatCompletions(self._holder))
        self.embeddings = _FakeEmbeddings()


def test_openai_provider_complete_returns_normalised_payload() -> None:
    """The provider now makes real calls (via an injected client) and normalises the
    response to the {text, usage, metadata} contract — not a NotImplementedError shell."""
    fake = _FakeOpenAIClient()
    provider = OpenAIProvider(client=fake)
    out = provider.complete(
        prompt="hello", model="gpt-4o-mini", temperature=0.2,
        response_format={"type": "json_object"},
    )
    assert out["text"] == "real answer"
    assert out["usage"] == {"prompt_tokens": 11, "completion_tokens": 7}
    assert out["metadata"]["model"] == "gpt-4o-mini"
    assert out["metadata"]["finish_reason"] == "stop"
    kw = fake._holder["kwargs"]
    assert kw["messages"] == [{"role": "user", "content": "hello"}]
    assert kw["response_format"] == {"type": "json_object"}


def test_openai_provider_embed_returns_vectors() -> None:
    provider = OpenAIProvider(client=_FakeOpenAIClient())
    out = provider.embed(texts=["a", "b"], model="text-embedding-3-small")
    assert out["embeddings"] == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert out["usage"]["prompt_tokens"] == 5


def test_llm_result_exposes_token_properties_for_usage_logging() -> None:
    """Codex P2: consumers (pricing_llm_task) read token counts as top-level attributes;
    LLMResult must surface them from metadata so usage logs aren't zero."""
    client = LLMClient(provider=MockLLMProvider(completion_text="hello world"))
    res = client.complete("hi there", model="gpt-4o-mini")
    assert res.prompt_tokens == res.metadata["prompt_tokens"] > 0
    assert res.completion_tokens == res.metadata["completion_tokens"] >= 0
    assert res.total_tokens == res.prompt_tokens + res.completion_tokens


def test_llm_client_retries_transient_then_succeeds() -> None:
    """LLMClient now applies LLMRetryPolicy: a transient provider error is retried."""
    from src.llm.retry import LLMTransientError
    calls = {"n": 0}

    class _Flaky:
        provider_name = "flaky"

        def complete(self, *, prompt, model, temperature, response_format=None):
            calls["n"] += 1
            if calls["n"] < 3:
                raise LLMTransientError("temporary blip")
            return {"text": "ok", "usage": {"prompt_tokens": 1, "completion_tokens": 1}}

    client = LLMClient(
        provider=_Flaky(),
        retry_policy=LLMRetryPolicy(max_attempts=3),
        sleep_fn=lambda _s: None,
    )
    res = client.complete("hi")
    assert res.text == "ok"
    assert calls["n"] == 3


def test_llm_client_gives_up_after_max_attempts() -> None:
    from src.llm.retry import LLMTransientError

    class _AlwaysFails:
        provider_name = "bad"

        def complete(self, *, prompt, model, temperature, response_format=None):
            raise LLMTransientError("always")

    client = LLMClient(
        provider=_AlwaysFails(),
        retry_policy=LLMRetryPolicy(max_attempts=2),
        sleep_fn=lambda _s: None,
    )
    with pytest.raises(LLMTransientError):
        client.complete("hi")


@pytest.mark.skipif(
    not os.getenv("OPENAI_LIVE"),
    reason="live OpenAI test — set OPENAI_LIVE=1 with a real OPENAI_API_KEY to run",
)
def test_openai_provider_live_smoke() -> None:  # pragma: no cover - network/live
    """Real OpenAI call (opt-in). Proves the live path end-to-end with a real key."""
    provider = OpenAIProvider()
    out = provider.complete(
        prompt="Reply with the single word: pong", model="gpt-4o-mini", temperature=0.0,
    )
    assert isinstance(out["text"], str) and out["text"].strip()
    assert out["usage"]["completion_tokens"] >= 1
    emb = provider.embed(texts=["hello world"], model="text-embedding-3-small")
    assert len(emb["embeddings"]) == 1 and len(emb["embeddings"][0]) > 100


def test_prompt_text_not_in_result_repr_or_metadata_dump() -> None:
    prompt = "sensitive prompt with context"
    client = LLMClient(provider=MockLLMProvider(completion_text="ok"))
    result = client.complete(prompt)

    assert prompt not in repr(result)
    assert prompt not in str(result.metadata)


def test_cache_write_read_round_trip(tmp_path: Path) -> None:
    db_path = tmp_path / "llm_cache.sqlite"
    cache = LLMCache(db_path=db_path)
    policy = CachePolicy(ttl_hours=4, enabled=True, cache_namespace="unit")
    key = build_cache_key(
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="cache me",
        cache_namespace=policy.cache_namespace,
    )
    payload = {"text": "cached", "metadata": {"cache_hit": False}}

    cache.set(
        key,
        payload,
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="cache me",
        policy=policy,
    )
    recovered = cache.get(key, policy=policy)

    assert recovered == payload


def test_expired_record_misses(monkeypatch: pytest.MonkeyPatch) -> None:
    cache = LLMCache(db_path=None)
    policy = CachePolicy(ttl_hours=1, enabled=True)
    key = build_cache_key(model="gpt-4o-mini", temperature=0.2, prompt_text="expiring prompt")
    cache.set(
        key,
        {"text": "stale", "metadata": {}},
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="expiring prompt",
        policy=policy,
    )
    assert cache.get(key, policy=policy) is not None

    future_time = datetime.now(UTC) + timedelta(hours=2)

    class FrozenDateTime(datetime):
        @classmethod
        def now(cls, tz: Any = None) -> datetime:
            del cls
            return future_time if tz is not None else future_time.replace(tzinfo=None)

    monkeypatch.setattr(cache_module, "datetime", FrozenDateTime)
    assert cache.get(key, policy=policy) is None


def test_disabled_cache_policy_bypasses_get_and_set(tmp_path: Path) -> None:
    cache = LLMCache(db_path=tmp_path / "cache.sqlite")
    policy = CachePolicy(enabled=False)
    key = build_cache_key(model="gpt-4o-mini", temperature=0.2, prompt_text="ignore me")

    cache.set(
        key,
        {"text": "value", "metadata": {}},
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="ignore me",
        policy=policy,
    )

    assert cache.get(key, policy=policy) is None


def test_cache_key_changes_with_model_or_temperature() -> None:
    key_one = build_cache_key(model="gpt-4o-mini", temperature=0.2, prompt_text="same prompt")
    key_two = build_cache_key(model="gpt-4o-mini", temperature=0.2, prompt_text="same prompt")
    key_diff_model = build_cache_key(model="gpt-4o", temperature=0.2, prompt_text="same prompt")
    key_diff_temp = build_cache_key(model="gpt-4o-mini", temperature=0.5, prompt_text="same prompt")

    assert key_one == key_two
    assert key_one != key_diff_model
    assert key_one != key_diff_temp


def test_cache_key_namespace_is_trimmed_for_determinism() -> None:
    one = build_cache_key(
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="same prompt",
        cache_namespace="  unit-cache  ",
    )
    two = build_cache_key(
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text="same prompt",
        cache_namespace="unit-cache",
    )
    assert one == two


def test_cache_record_and_db_do_not_store_raw_fake_api_key(tmp_path: Path) -> None:
    fake_key = "sk-fake1234"
    cache_path = tmp_path / "cache.sqlite"
    cache = LLMCache(db_path=cache_path)
    policy = CachePolicy(store_prompt_text=False)
    key = build_cache_key(model="gpt-4o-mini", temperature=0.2, prompt_text=fake_key)

    cache.set(
        key,
        {"text": "safe", "metadata": {}},
        model="gpt-4o-mini",
        temperature=0.2,
        prompt_text=fake_key,
        policy=policy,
    )
    record = cache.get_record(key, policy=policy)
    db_raw = cache_path.read_bytes().decode("utf-8", errors="ignore")

    assert record is not None
    assert fake_key not in str(record)
    assert fake_key not in db_raw


def test_invalid_cache_record_is_treated_as_miss(tmp_path: Path) -> None:
    cache_path = tmp_path / "cache.sqlite"
    cache = LLMCache(db_path=cache_path)
    policy = CachePolicy(enabled=True)
    key = "broken-row-key"
    conn = cache._ensure_connection()
    assert conn is not None
    conn.execute(
        """
        INSERT OR REPLACE INTO llm_cache(
            key, model, temperature, cache_namespace, prompt_hash, prompt_text,
            response_payload, created_at, expires_at, cache_version
        )
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            key,
            "gpt-4o-mini",
            0.2,
            "default",
            "hash",
            None,
            "{bad-json",
            datetime.now(UTC).isoformat(),
            (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            "v2",
        ),
    )
    conn.commit()

    assert cache.get(key, policy=policy) is None
    row = conn.execute("SELECT key FROM llm_cache WHERE key = ?", (key,)).fetchone()
    assert row is None


def test_is_expired_handles_naive_datetime_strings() -> None:
    cache = LLMCache(db_path=None)
    reference_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)
    future_naive = "2026-01-01T13:00:00"
    assert cache.is_expired({"expires_at": future_naive}, now=reference_now) is False


def test_parse_json_response_returns_typed_schema() -> None:
    parsed = parse_json_response(DemoSchema, '{"name":"alpha","score":3}')
    assert parsed.name == "alpha"
    assert parsed.score == 3


def test_malformed_json_raises_validation_error() -> None:
    with pytest.raises(LLMValidationError, match="Malformed JSON"):
        parse_json_response(DemoSchema, '{"name": ')


def test_missing_required_field_raises_sanitized_validation_error() -> None:
    with pytest.raises(LLMValidationError) as exc_info:
        parse_json_response(DemoSchema, '{"name":"x","api_key":"sk-test1234"}')

    assert "LLM response failed schema validation." in str(exc_info.value)
    assert "sk-test1234" not in str(exc_info.value.details)


def test_retry_delay_increases_and_caps() -> None:
    policy = LLMRetryPolicy(base_delay_seconds=1.0, max_delay_seconds=3.0)
    assert policy.compute_delay(1) == 1.0
    assert policy.compute_delay(2) == 2.0
    assert policy.compute_delay(3) == 3.0
    assert policy.compute_delay(4) == 3.0


def test_retry_decision_allows_validation_error_when_enabled() -> None:
    policy = LLMRetryPolicy(max_attempts=3, retry_on_validation_error=True)
    decision = policy.build_retry_decision(
        attempt=1,
        error=LLMValidationError("invalid"),
    )
    assert decision.should_retry is True
    assert decision.next_attempt == 2


def test_retry_decision_allows_rate_limit_when_enabled() -> None:
    policy = LLMRetryPolicy(max_attempts=2, retry_on_rate_limit=True)
    decision = policy.build_retry_decision(attempt=1, error=LLMRateLimitError("rate"))
    assert decision.should_retry is True
    assert decision.reason == "LLMRateLimitError"


def test_retry_policy_jitter_and_non_retryable_errors() -> None:
    policy = LLMRetryPolicy(base_delay_seconds=1.0, max_delay_seconds=3.0, max_attempts=2)
    assert policy.compute_delay(0) == 0.0
    assert policy.compute_delay(2, jitter_provider=lambda: 1.0) == 3.0
    decision = policy.build_retry_decision(attempt=1, error=RuntimeError("not retryable"))
    assert decision.should_retry is False
    assert decision.reason == "error-not-retryable"


def test_validation_retry_prompt_redacts_secrets_and_keeps_guidance() -> None:
    prompt = build_validation_retry_prompt(
        "Original prompt api_key=sk-test1234",
        ValueError("Invalid payload with sk-test1234"),
    )
    assert "Validation failed." in prompt
    assert "[REDACTED]" in prompt
    assert "sk-test1234" not in prompt


def test_self_correction_prompt_includes_schema_and_redacts_secrets() -> None:
    prompt = build_self_correction_prompt(
        "keyword_clustering",
        '{"type":"object","required":["score"]}',
        ValueError("api_key=sk-test1234 missing score"),
    )
    assert "required" in prompt
    assert "keyword_clustering" in prompt
    assert "sk-test1234" not in prompt


def test_known_model_cost_calculation_is_exact() -> None:
    estimate = estimate_llm_cost("gpt-4o-mini", input_tokens=1000, output_tokens=500)
    assert estimate.estimated_cost_usd == 0.00045
    assert estimate.confidence == "known"


def test_unknown_model_cost_is_safe_and_strict_mode_raises() -> None:
    estimate = estimate_llm_cost("unknown-model", input_tokens=1000, output_tokens=500)
    assert estimate.estimated_cost_usd == 0.0
    assert estimate.confidence == "unknown"

    with pytest.raises(ValueError, match="Unknown model"):
        estimate_llm_cost("unknown-model", input_tokens=1, output_tokens=1, strict=True)


def test_llm_client_usage_metadata_present_for_mock_completion() -> None:
    client = LLMClient(provider=MockLLMProvider(completion_text="ok"))
    result = client.complete("hello")

    usage_event = result.metadata["usage_event"]
    assert usage_event["model"] == "gpt-4o-mini"
    assert usage_event["input_tokens"] >= 1
    assert usage_event["total_tokens"] == usage_event["input_tokens"] + usage_event["output_tokens"]
    assert usage_event["provider_name"] == "mock"


def test_cache_hit_marks_zero_cost() -> None:
    provider = CountingMockProvider(completion_text="cached output")
    cache = LLMCache(db_path=None)
    client = LLMClient(provider=provider, cache=cache, cache_policy=CachePolicy(ttl_hours=24))

    first = client.complete("cache this")
    second = client.complete("cache this")

    assert first.metadata["cache_hit"] is False
    assert second.metadata["cache_hit"] is True
    assert second.metadata["estimated_cost_usd"] == 0.0
    assert second.metadata["usage_event"]["cache_hit"] is True
    assert second.metadata["usage_event"]["estimated_cost_usd"] == 0.0


def test_malformed_provider_payload_is_coerced_to_text() -> None:
    client = LLMClient(provider=StringOnlyProvider())
    result = client.complete("hello")
    assert result.text == "plain-text-payload"
    assert result.metadata["provider_name"] == "string-only"


def test_complete_raises_when_provider_is_missing_or_incomplete() -> None:
    missing = LLMClient(provider=None)
    with pytest.raises(RuntimeError, match="not configured"):
        missing.complete("hello")

    incomplete = LLMClient(provider=IncompleteProvider())
    with pytest.raises(TypeError, match="complete"):
        incomplete.complete("hello")


def test_embed_fallback_usage_and_provider_errors() -> None:
    client = LLMClient(provider=MockLLMProvider(embedding_value=2.0))
    payload = client.embed(["a", "b"])
    assert payload["embeddings"] == [[2.0], [2.0]]
    assert payload["metadata"]["prompt_tokens"] >= 1
    assert payload["metadata"]["completion_tokens"] == 0

    missing = LLMClient(provider=None)
    with pytest.raises(RuntimeError, match="not configured"):
        missing.embed(["text"])

    incomplete = LLMClient(provider=IncompleteProvider())
    with pytest.raises(TypeError, match="embed"):
        incomplete.embed(["text"])


def test_calculate_cost_and_estimate_tokens_edge_cases() -> None:
    assert LLMClient.calculate_cost_usd("gpt-4o-mini", prompt_tokens=100, completion_tokens=50) > 0
    assert LLMClient._estimate_tokens("") == 0
