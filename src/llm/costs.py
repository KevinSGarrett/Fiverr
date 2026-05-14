"""Centralized model pricing and cost estimation helpers."""

from __future__ import annotations

from src.llm.schemas import CostEstimate

PRICE_TABLE_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"input": 0.0050, "output": 0.0150},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "text-embedding-3-small": {"input": 0.00002, "output": 0.0},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}


def estimate_llm_cost(
    model: str,
    input_tokens: int,
    output_tokens: int = 0,
    *,
    strict: bool = False,
) -> CostEstimate:
    """Estimate LLM cost from centralized price table."""
    pricing = PRICE_TABLE_PER_1K_TOKENS.get(model)
    total_tokens = input_tokens + output_tokens
    if pricing is None:
        if strict:
            raise ValueError(f"Unknown model for pricing: {model}")
        return CostEstimate(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=0.0,
            confidence="unknown",
            pricing_source="unpriced-model",
        )

    prompt_cost = (input_tokens / 1000) * pricing["input"]
    completion_cost = (output_tokens / 1000) * pricing["output"]
    return CostEstimate(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total_tokens,
        estimated_cost_usd=round(prompt_cost + completion_cost, 8),
        confidence="known",
        pricing_source="price-table-v1",
    )
