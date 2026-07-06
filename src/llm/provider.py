"""Provider abstractions and safe test adapters for LLM access."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Protocol


class LLMProviderProtocol(Protocol):
    """Protocol for chat completion and embedding providers."""

    provider_name: str

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a completion request and return provider payload."""

    def embed(self, *, texts: list[str], model: str) -> dict[str, Any]:
        """Run an embedding request and return provider payload."""


@dataclass(slots=True)
class MockLLMProvider:
    """Deterministic provider used by unit tests and local development."""

    completion_text: str = "mock completion"
    embedding_value: float = 0.0
    provider_name: str = "mock"

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del response_format
        return {
            "text": self.completion_text,
            "usage": {
                "prompt_tokens": max(1, len(prompt) // 4),
                "completion_tokens": max(1, len(self.completion_text) // 4),
            },
            "metadata": {
                "model": model,
                "temperature": temperature,
            },
        }

    def embed(self, *, texts: list[str], model: str) -> dict[str, Any]:
        del model
        return {
            "embeddings": [[self.embedding_value] for _ in texts],
            "usage": {"prompt_tokens": max(1, len(" ".join(texts)) // 4)},
        }


class OpenAIProvider:
    """Live OpenAI provider (chat completions + embeddings).

    Wraps the official ``openai`` SDK (v1) and normalises responses to the payload
    contract the rest of the stack expects (see ``MockLLMProvider``):
      complete -> {"text", "usage": {prompt_tokens, completion_tokens}, "metadata"}
      embed    -> {"embeddings": [[float, ...], ...], "usage": {prompt_tokens}}

    Retryable provider failures (rate limit, timeout, connection, 5xx) are re-raised as
    ``LLMRateLimitError`` / ``LLMTransientError`` so ``LLMClient``'s ``LLMRetryPolicy`` can
    back off and retry. The SDK's own retries are disabled (``max_retries=0``) so retry
    lives in one place. A pre-built ``client`` may be injected for tests.
    """

    provider_name = "openai"

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: Any | None = None,
        timeout: float = 60.0,
    ) -> None:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if client is None and not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY is required to construct OpenAIProvider. "
                "Inject MockLLMProvider (or client=) for unit tests."
            )
        self._api_key = resolved_key
        self._client = client
        self._timeout = timeout

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import OpenAI  # lazy: MockLLMProvider paths need no SDK

            # max_retries=0 → LLMClient's LLMRetryPolicy is the single retry authority.
            self._client = OpenAI(api_key=self._api_key, timeout=self._timeout, max_retries=0)
        return self._client

    @staticmethod
    def _mapped_errors() -> Any:
        from openai import (
            APIConnectionError,
            APIStatusError,
            APITimeoutError,
            RateLimitError,
        )
        from src.llm.retry import LLMRateLimitError, LLMTransientError

        return (
            RateLimitError,
            (APITimeoutError, APIConnectionError),
            APIStatusError,
            LLMRateLimitError,
            LLMTransientError,
        )

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = self._get_client()
        rate_limit, transient_net, status_err, RateLimit, Transient = self._mapped_errors()
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format
        try:
            resp = client.chat.completions.create(**kwargs)
        except rate_limit as exc:
            raise RateLimit(str(exc)) from exc
        except transient_net as exc:
            raise Transient(str(exc)) from exc
        except status_err as exc:
            if 500 <= int(getattr(exc, "status_code", 0) or 0) < 600:
                raise Transient(str(exc)) from exc
            raise

        choice = resp.choices[0]
        usage = resp.usage
        return {
            "text": (choice.message.content or ""),
            "usage": {
                "prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
                "completion_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
            },
            "metadata": {
                "model": getattr(resp, "model", model),
                "temperature": temperature,
                "finish_reason": getattr(choice, "finish_reason", None),
            },
        }

    def embed(self, *, texts: list[str], model: str) -> dict[str, Any]:
        client = self._get_client()
        rate_limit, transient_net, status_err, RateLimit, Transient = self._mapped_errors()
        try:
            resp = client.embeddings.create(model=model, input=texts)
        except rate_limit as exc:
            raise RateLimit(str(exc)) from exc
        except transient_net as exc:
            raise Transient(str(exc)) from exc
        except status_err as exc:
            if 500 <= int(getattr(exc, "status_code", 0) or 0) < 600:
                raise Transient(str(exc)) from exc
            raise

        usage = resp.usage
        return {
            "embeddings": [list(d.embedding) for d in resp.data],
            "usage": {"prompt_tokens": int(getattr(usage, "prompt_tokens", 0) or 0)},
        }
