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
    """OpenAI provider shell with runtime-only API key validation."""

    provider_name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        resolved_key = api_key or os.getenv("OPENAI_API_KEY")
        if not resolved_key:
            raise ValueError(
                "OPENAI_API_KEY is required to construct OpenAIProvider. "
                "Inject MockLLMProvider for unit tests."
            )
        self._api_key = resolved_key

    def complete(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        del prompt, model, temperature, response_format
        raise NotImplementedError(
            "OpenAIProvider shell is configured, but live API calls are not "
            "enabled in this unit-test-safe foundation cycle."
        )

    def embed(self, *, texts: list[str], model: str) -> dict[str, Any]:
        del texts, model
        raise NotImplementedError(
            "OpenAIProvider shell is configured, but live API calls are not "
            "enabled in this unit-test-safe foundation cycle."
        )
