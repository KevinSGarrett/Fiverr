"""Pricing engine — E06 implementation module.

Provides price distribution analysis, new-seller entry pricing,
LLM pricing tasks, price ladder tracking, and revenue gate tracking.

Status: Scaffolded (SCRUM-273). Full implementation in SCRUM-187 through SCRUM-194.
"""

from __future__ import annotations

from src.pricing.analysis import (
    RawPriceData,
    extract_raw_price_data_from_db,
    run_price_distribution_analysis,
)
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
    "RawPriceData",
    "PricingOrchestrator",
    "calculate_new_seller_pricing",
    "extract_raw_price_data_from_db",
    "project_revenue_at_entry_pricing",
    "run_price_distribution_analysis",
]
