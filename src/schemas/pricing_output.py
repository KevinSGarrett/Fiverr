"""Pydantic output schema for LLM pricing strategy recommendations."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EntryPrices(BaseModel):
    basic: int = Field(..., ge=5, le=2000)
    standard: int = Field(..., ge=10, le=5000)
    premium: int = Field(..., ge=20, le=10000)
    lead_tier: Literal["basic", "standard"]
    lead_tier_reasoning: str = Field(..., min_length=20, max_length=200)

    @model_validator(mode="after")
    def validate_price_order(self) -> EntryPrices:
        if self.standard <= self.basic:
            raise ValueError("Standard must be above Basic")
        if self.premium <= self.standard:
            raise ValueError("Premium must be above Standard")
        return self


class AcquisitionPrices(BaseModel):
    basic: int = Field(..., ge=5, le=2000)
    standard: int = Field(..., ge=10, le=5000)
    premium: int = Field(..., ge=20, le=10000)
    acquisition_period: str = Field(..., min_length=5, max_length=50)


class PriceLadderStep(BaseModel):
    milestone_reviews: int = Field(..., ge=0, le=500)
    basic: int = Field(..., ge=5)
    standard: int = Field(..., ge=10)
    premium: int = Field(..., ge=20)
    adjustment_rationale: str = Field(..., min_length=10, max_length=200)


class PricingRisk(BaseModel):
    risk: str = Field(..., min_length=10, max_length=200)
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    mitigation: str = Field(..., min_length=10, max_length=200)


class RecommendedExtra(BaseModel):
    name: str = Field(..., min_length=5, max_length=60)
    price: int = Field(..., ge=5, le=500)
    rationale: str = Field(..., min_length=10, max_length=200)


class ProjectedAOV(BaseModel):
    at_entry: float = Field(..., ge=5)
    at_50_reviews: float = Field(..., ge=5)
    aov_growth_pct: float = Field(..., ge=0)


class PricingStrategy(BaseModel):
    """Complete LLM-generated pricing strategy for a keyword."""

    entry_prices: EntryPrices
    acquisition_prices: AcquisitionPrices
    price_ladder: list[PriceLadderStep] = Field(..., min_length=4, max_length=8)
    strategy_narrative: str = Field(..., min_length=100, max_length=500)
    pricing_risks: list[PricingRisk] = Field(default_factory=list, max_length=5)
    recommended_extras: list[RecommendedExtra] = Field(..., min_length=2, max_length=4)
    projected_aov: ProjectedAOV

    @field_validator("price_ladder")
    @classmethod
    def ladder_prices_ascending(cls, value: list[PriceLadderStep]) -> list[PriceLadderStep]:
        for index in range(1, len(value)):
            if value[index].basic < value[index - 1].basic:
                raise ValueError(f"Price ladder step {index} basic price must be >= step {index - 1}")
        return value
