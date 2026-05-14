"""Injectable LLM client with safe metadata and cost accounting."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from src.llm.cache import CachePolicy, LLMCache, build_cache_key
from src.llm.costs import estimate_llm_cost
from src.llm.provider import LLMProviderProtocol, OpenAIProvider


@dataclass(slots=True)
class LLMResult:
    """Response payload returned from complete requests."""

    text: str
    metadata: dict[str, Any]

    def __repr__(self) -> str:
        keys = ", ".join(sorted(self.metadata.keys()))
        return f"LLMResult(text_len={len(self.text)}, metadata_keys=[{keys}])"


class LLMClient:
    """LLM wrapper that supports injected providers and cache metadata."""

    def __init__(
        self,
        provider: LLMProviderProtocol | Any | None = None,
        cache: LLMCache | None = None,
        cache_policy: CachePolicy | None = None,
        use_openai_provider: bool = False,
        openai_api_key: str | None = None,
    ) -> None:
        if provider is not None and use_openai_provider:
            raise ValueError("Provide either 'provider' or 'use_openai_provider=True', not both.")
        if provider is None and use_openai_provider:
            provider = OpenAIProvider(api_key=openai_api_key)
        self._provider = provider
        self._cache = cache
        self._cache_policy = cache_policy or CachePolicy()

    def complete(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        cache_key = build_cache_key(
            model=model,
            temperature=temperature,
            prompt_text=prompt,
            cache_namespace=self._cache_policy.cache_namespace,
            max_prompt_chars_for_keying=self._cache_policy.max_prompt_chars_for_keying,
        )

        if self._cache is not None and self._cache_policy.enabled:
            cached_payload = self._cache.get(cache_key, policy=self._cache_policy)
            if cached_payload is not None:
                cached_metadata = dict(cached_payload["metadata"])
                cached_metadata["cache_hit"] = True
                cached_metadata["estimated_cost_usd"] = 0.0
                return LLMResult(text=str(cached_payload["text"]), metadata=cached_metadata)

        payload = self._call_provider_complete(
            prompt=prompt,
            model=model,
            temperature=temperature,
            response_format=response_format,
        )
        text = str(payload.get("text", ""))
        usage = payload.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", self._estimate_tokens(prompt)))
        completion_tokens = int(usage.get("completion_tokens", self._estimate_tokens(text)))
        cost_estimate = estimate_llm_cost(model, prompt_tokens, completion_tokens)
        prompt_hash = build_cache_key(
            model=model,
            temperature=temperature,
            prompt_text=prompt,
            cache_namespace="prompt-hash-only",
            max_prompt_chars_for_keying=self._cache_policy.max_prompt_chars_for_keying,
            cache_version="prompt-v1",
        )

        metadata = {
            "model": model,
            "temperature": temperature,
            "prompt_hash": prompt_hash,
            "cache_hit": False,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": cost_estimate.estimated_cost_usd,
            "provider_name": getattr(self._provider, "provider_name", "unknown"),
            "created_at": datetime.now(UTC).isoformat(),
            "usage_event": {
                "model": model,
                "task_name": None,
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
                "estimated_cost_usd": cost_estimate.estimated_cost_usd,
                "cache_hit": False,
                "provider_name": getattr(self._provider, "provider_name", "unknown"),
                "created_at": datetime.now(UTC).isoformat(),
            },
        }
        result = LLMResult(text=text, metadata=metadata)

        if self._cache is not None and self._cache_policy.enabled:
            self._cache.set(
                cache_key,
                {"text": result.text, "metadata": result.metadata},
                model=model,
                temperature=temperature,
                prompt_text=prompt,
                policy=self._cache_policy,
            )

        return result

    def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> dict[str, Any]:
        payload = self._call_provider_embed(texts=texts, model=model)
        usage = payload.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", self._estimate_tokens(" ".join(texts))))
        cost_estimate = estimate_llm_cost(model, prompt_tokens, 0)

        return {
            "embeddings": payload.get("embeddings", []),
            "metadata": {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 0,
                "total_tokens": prompt_tokens,
                "estimated_cost_usd": cost_estimate.estimated_cost_usd,
            },
        }

    @staticmethod
    def calculate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int = 0) -> float:
        """Estimate request cost using per-1K token pricing."""
        return estimate_llm_cost(model, prompt_tokens, completion_tokens).estimated_cost_usd

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def _call_provider_complete(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if self._provider is None:
            raise RuntimeError("LLM provider is not configured.")

        if hasattr(self._provider, "complete"):
            payload = self._provider.complete(
                prompt=prompt,
                model=model,
                temperature=temperature,
                response_format=response_format,
            )
            return payload if isinstance(payload, dict) else {"text": str(payload)}

        raise TypeError("Provider must define a complete() method.")

    def _call_provider_embed(self, texts: list[str], model: str) -> dict[str, Any]:
        if self._provider is None:
            raise RuntimeError("LLM provider is not configured.")

        if hasattr(self._provider, "embed"):
            payload = self._provider.embed(texts=texts, model=model)
            return payload if isinstance(payload, dict) else {"embeddings": payload}

        raise TypeError("Provider must define an embed() method for embedding requests.")
