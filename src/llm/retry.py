"""Retry policy and deterministic backoff helpers for LLM calls."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from src.llm.schemas import RetryDecision
from src.llm.validation import LLMValidationError


class LLMRateLimitError(RuntimeError):
    """Raised when provider reports rate limit pressure."""


class LLMTransientError(RuntimeError):
    """Raised for retryable provider or transport failures."""


@dataclass(slots=True, frozen=True)
class LLMRetryPolicy:
    """Controls which error classes can trigger retries."""

    max_attempts: int = 3
    retry_on_validation_error: bool = True
    retry_on_rate_limit: bool = True
    retry_on_transient_error: bool = True
    base_delay_seconds: float = 0.5
    max_delay_seconds: float = 8.0

    def compute_delay(
        self,
        attempt: int,
        jitter_provider: Callable[[], float] | None = None,
    ) -> float:
        """Compute capped exponential delay without sleeping."""
        if attempt <= 0:
            return 0.0
        uncapped = self.base_delay_seconds * (2 ** (attempt - 1))
        delay = min(uncapped, self.max_delay_seconds)
        if jitter_provider is None:
            return delay
        jitter = max(0.0, min(1.0, jitter_provider()))
        return min(delay + (self.base_delay_seconds * jitter), self.max_delay_seconds)

    def should_retry(self, error: Exception) -> bool:
        """Return whether error type is retryable under this policy."""
        if isinstance(error, LLMValidationError):
            return self.retry_on_validation_error
        if isinstance(error, LLMRateLimitError):
            return self.retry_on_rate_limit
        if isinstance(error, LLMTransientError):
            return self.retry_on_transient_error
        return False

    def build_retry_decision(self, *, attempt: int, error: Exception) -> RetryDecision:
        """Return retry decision for current attempt and error."""
        retryable = self.should_retry(error)
        if not retryable:
            return RetryDecision(
                should_retry=False,
                reason="error-not-retryable",
                next_attempt=None,
                delay_seconds=0.0,
            )
        if attempt >= self.max_attempts:
            return RetryDecision(
                should_retry=False,
                reason="max-attempts-reached",
                next_attempt=None,
                delay_seconds=0.0,
            )
        next_attempt = attempt + 1
        return RetryDecision(
            should_retry=True,
            reason=error.__class__.__name__,
            next_attempt=next_attempt,
            delay_seconds=self.compute_delay(next_attempt),
        )
