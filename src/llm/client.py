"""Injectable LLM client wrapper with optional response caching."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Protocol

from src.llm.cache import LLMCache, build_cache_key

PRICING_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0050, "output": 0.0150},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
}


class LLMProvider(Protocol):
    """Provider interface used by ``LLMClient``."""

    def complete(
        self,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...

    def embed(self, texts: list[str], model: str) -> dict[str, Any]: ...


@dataclass(slots=True)
class LLMResult:
    """Response payload returned from complete requests."""

    text: str
    metadata: dict[str, Any]


class LLMClient:
    """LLM wrapper that supports injected providers and cache metadata."""

    def __init__(
        self,
        provider: LLMProvider | Any | None = None,
        cache: LLMCache | None = None,
        cache_ttl_hours: int = 72,
    ) -> None:
        self._provider = provider
        self._cache = cache
        self._cache_ttl_hours = cache_ttl_hours

    def complete(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> LLMResult:
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        cache_key = build_cache_key(model=model, temperature=temperature, prompt_text=prompt)

        if self._cache is not None:
            cached_payload = self._cache.get(cache_key)
            if cached_payload is not None:
                cached_metadata = dict(cached_payload["metadata"])
                cached_metadata["cache_hit"] = True
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
        estimated_cost_usd = self.calculate_cost_usd(model, prompt_tokens, completion_tokens)

        metadata = {
            "model": model,
            "temperature": temperature,
            "prompt_hash": prompt_hash,
            "cache_hit": False,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "estimated_cost_usd": estimated_cost_usd,
        }
        result = LLMResult(text=text, metadata=metadata)

        if self._cache is not None:
            self._cache.set(
                cache_key,
                {"text": result.text, "metadata": result.metadata},
                ttl_hours=self._cache_ttl_hours,
            )

        return result

    def embed(self, texts: list[str], model: str = "text-embedding-3-small") -> dict[str, Any]:
        payload = self._call_provider_embed(texts=texts, model=model)
        usage = payload.get("usage", {})
        prompt_tokens = int(usage.get("prompt_tokens", self._estimate_tokens(" ".join(texts))))
        estimated_cost_usd = self.calculate_cost_usd(model, prompt_tokens, 0)

        return {
            "embeddings": payload.get("embeddings", []),
            "metadata": {
                "model": model,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": 0,
                "total_tokens": prompt_tokens,
                "estimated_cost_usd": estimated_cost_usd,
            },
        }

    @staticmethod
    def calculate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int = 0) -> float:
        """Estimate request cost using per-1K token pricing."""
        pricing = PRICING_PER_1K_TOKENS.get(model)
        if pricing is None:
            return 0.0
        prompt_cost = (prompt_tokens / 1000) * pricing["input"]
        completion_cost = (completion_tokens / 1000) * pricing["output"]
        return round(prompt_cost + completion_cost, 8)

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

        if callable(self._provider):
            payload = self._provider(
                prompt=prompt,
                model=model,
                temperature=temperature,
                response_format=response_format,
            )
            return payload if isinstance(payload, dict) else {"text": str(payload)}

        if hasattr(self._provider, "complete"):
            payload = self._provider.complete(
                prompt=prompt,
                model=model,
                temperature=temperature,
                response_format=response_format,
            )
            return payload if isinstance(payload, dict) else {"text": str(payload)}

        raise TypeError("Provider must be callable or define a complete() method.")

    def _call_provider_embed(self, texts: list[str], model: str) -> dict[str, Any]:
        if self._provider is None:
            raise RuntimeError("LLM provider is not configured.")

        if hasattr(self._provider, "embed"):
            payload = self._provider.embed(texts=texts, model=model)
            return payload if isinstance(payload, dict) else {"embeddings": payload}

        raise TypeError("Provider must define an embed() method for embedding requests.")
