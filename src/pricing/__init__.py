"""Pricing engine — E06 implementation module.

Provides price distribution analysis, new-seller entry pricing,
LLM pricing tasks, price ladder tracking, and revenue gate tracking.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-187 through SCRUM-194.
"""

from __future__ import annotations

from src.pricing.contracts import (
    EntryPricingRecommendation,
    PriceDistribution,
    PricingInput,
    PricingOutput,
)
from src.pricing.new_seller_pricing import (
    PricingRecommendation,
    calculate_new_seller_pricing,
    project_revenue_at_entry_pricing,
)
from src.pricing.orchestrator import PricingOrchestrator

__all__ = [
    "EntryPricingRecommendation",
    "PriceDistribution",
    "PricingRecommendation",
    "PricingInput",
    "PricingOutput",
    "PricingOrchestrator",
    "calculate_new_seller_pricing",
    "project_revenue_at_entry_pricing",
]
