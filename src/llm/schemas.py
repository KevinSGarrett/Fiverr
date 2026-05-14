"""Reusable structured schemas for LLM outputs and accounting."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Schema validation issue suitable for retries or logging."""

    field: str
    message: str
    severity: Literal["error", "warning"] = "error"


class RetryDecision(BaseModel):
    """Decision object for deterministic retry behavior."""

    should_retry: bool
    reason: str
    next_attempt: int | None = None
    delay_seconds: float = 0.0


class TokenUsage(BaseModel):
    """Token accounting for a provider interaction."""

    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0, default=0)
    total_tokens: int = Field(ge=0)


class CostEstimate(BaseModel):
    """Estimated request cost in USD."""

    model: str
    input_tokens: int = Field(ge=0)
    output_tokens: int = Field(ge=0, default=0)
    total_tokens: int = Field(ge=0)
    estimated_cost_usd: float = Field(ge=0.0)
    confidence: Literal["known", "unknown"] = "known"
    pricing_source: str | None = None
    currency: Literal["USD"] = "USD"


class LLMTaskResult(BaseModel):
    """Generic structured task envelope returned by LLM layers."""

    task_name: str
    status: Literal["success", "failed"]
    output: dict[str, Any] = Field(default_factory=dict)
    usage: TokenUsage | None = None
    cost: CostEstimate | None = None
    issues: list[ValidationIssue] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
