"""Dashboard display schema for pricing strategy surfaces."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from src.pricing.new_seller_pricing import PricingRecommendation


class PriceLadderDisplayStep(BaseModel):
    """Single visual step in the pricing ladder display."""

    milestone_reviews: int
    label: str
    basic: float
    standard: float
    premium: float
    basic_increase_pct: float = 0.0


class PricingDisplaySchema(BaseModel):
    """Display schema for pricing strategy in the dashboard."""

    keyword_id: int
    keyword_text: str
    market_type: str | None = None
    moat_strength: str | None = None
    entry_basic: float
    entry_standard: float
    entry_premium: float
    acquisition_basic: float | None = None
    target_basic: float | None = None
    target_standard: float | None = None
    target_premium: float | None = None
    undercut_pct: float | None = None
    confidence: str | None = None  # HIGH / MEDIUM / LOW
    price_ladder: list[PriceLadderDisplayStep] = Field(default_factory=list)
    strategy_narrative: str | None = None
    llm_pricing_strategy: dict[str, Any] | None = None  # Task 12 output
    revenue_projections: dict[str, Any] | None = None

    @classmethod
    def from_pricing_recommendation(
        cls,
        pr: PricingRecommendation,
        keyword_text: str,
    ) -> PricingDisplaySchema:
        """Build PricingDisplaySchema from a PricingRecommendation payload."""

        steps = [PriceLadderDisplayStep(**step) for step in pr.price_ladder]
        return cls(
            keyword_id=pr.keyword_id,
            keyword_text=keyword_text,
            market_type=pr.market_type,
            moat_strength=getattr(pr, "moat_strength", None),
            entry_basic=pr.entry_basic,
            entry_standard=pr.entry_standard,
            entry_premium=pr.entry_premium,
            acquisition_basic=pr.acquisition_basic,
            target_basic=pr.target_basic,
            target_standard=pr.target_standard,
            target_premium=pr.target_premium,
            undercut_pct=pr.undercut_pct,
            confidence=pr.confidence,
            price_ladder=steps,
        )
