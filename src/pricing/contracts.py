"""Pricing engine contracts.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-187 through SCRUM-194.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PriceDistribution:
    """Market price distribution statistics."""

    niche_id: str
    keyword: str
    sample_count: int = 0
    price_min: float | None = None
    price_max: float | None = None
    price_median: float | None = None
    price_p25: float | None = None
    price_p75: float | None = None
    price_mean: float | None = None
    currency: str = "USD"
    raw_prices: list[float] = field(default_factory=list)


@dataclass
class EntryPricingRecommendation:
    """Recommended entry pricing for a new seller."""

    niche_id: str
    keyword: str
    basic_price: float = 0.0
    standard_price: float = 0.0
    premium_price: float = 0.0
    market_position: str = "budget"  # budget | mid-range | premium
    undercutting_pct: float = 0.0
    price_increase_triggers: list[str] = field(default_factory=list)
    confidence: float = 0.0
    rationale: str = ""
    raw_json: dict[str, Any] = field(default_factory=dict)


@dataclass
class PricingInput:
    """Input contract for the pricing orchestrator."""

    run_id: int | None = None
    niche_id: str | None = None
    keyword_id: int | None = None
    distribution: PriceDistribution | None = None
    scoring_output_raw: dict[str, Any] = field(default_factory=dict)
    llm_context: dict[str, Any] = field(default_factory=dict)


@dataclass
class PricingOutput:
    """Output from a pricing analysis run."""

    run_id: int | None = None
    niche_id: str | None = None
    keyword_id: int | None = None
    distribution: PriceDistribution | None = None
    entry_recommendation: EntryPricingRecommendation | None = None
    llm_pricing_guidance: dict[str, Any] = field(default_factory=dict)
    raw_json: dict[str, Any] = field(default_factory=dict)
