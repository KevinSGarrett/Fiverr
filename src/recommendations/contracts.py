"""Recommendation engine contracts (Pydantic models) — E05 scaffold."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GigTitle(BaseModel):
    title: str
    rationale: str | None = None


class TagSet(BaseModel):
    tags: list[str] = Field(default_factory=list)


class PackageTier(BaseModel):
    name: str
    price: float
    deliverables: list[str] = Field(default_factory=list)
    delivery_days: int
    revisions: int | None = None


class PackageStructure(BaseModel):
    basic: PackageTier
    standard: PackageTier
    premium: PackageTier


class DescriptionSection(BaseModel):
    title: str
    body: str


class DescriptionOutline(BaseModel):
    sections: list[DescriptionSection] = Field(default_factory=list)


class FAQEntry(BaseModel):
    question: str
    answer: str


class DifferentiationAngle(BaseModel):
    positioning_statement: str
    differentiators: list[str] = Field(default_factory=list)


class BuyerPersona(BaseModel):
    name: str
    pain_points: list[str] = Field(default_factory=list)
    decision_factors: list[str] = Field(default_factory=list)


class ThumbnailDirection(BaseModel):
    visual_concept: str
    color_palette: list[str] = Field(default_factory=list)
    text_overlay: str | None = None


class UpsellExtra(BaseModel):
    name: str
    price: float
    description: str


class UpsellStructure(BaseModel):
    extras: list[UpsellExtra] = Field(default_factory=list)


class RedFlagsAssessment(BaseModel):
    risk_level: str = "MEDIUM"
    risks: list[str] = Field(default_factory=list)


class NicheViability(BaseModel):
    viability_rating: float
    reasoning: str


class PricingStrategy(BaseModel):
    entry_price: float
    target_price: float
    milestone_prices: list[float] = Field(default_factory=list)
    rationale: str | None = None


class ProfileOptimization(BaseModel):
    bio_template: str
    headline: str
    specialization_tags: list[str] = Field(default_factory=list)


class VisualRecommendations(BaseModel):
    thumbnail_style: str
    gallery_recommendations: list[str] = Field(default_factory=list)


class RecommendationContext(BaseModel):
    niche_id: str
    keyword: str
    run_id: int | None = None
    score_data: dict[str, Any] = Field(default_factory=dict)
    competitor_data: dict[str, Any] = Field(default_factory=dict)
    pricing_data: dict[str, Any] = Field(default_factory=dict)
    visual_data: dict[str, Any] = Field(default_factory=dict)
    review_insights: dict[str, Any] = Field(default_factory=dict)
    external_signals: dict[str, Any] = Field(default_factory=dict)

    def completeness_ratio(self) -> float:
        optional_fields = [
            self.score_data, self.competitor_data, self.pricing_data,
            self.visual_data, self.review_insights, self.external_signals,
        ]
        populated = sum(1 for f in optional_fields if f)
        return populated / len(optional_fields)


class RecommendationOutput(BaseModel):
    niche_id: str
    keyword: str
    run_id: int | None = None
    gig_titles: list[GigTitle] | None = None
    tag_sets: list[TagSet] | None = None
    package_structure: PackageStructure | None = None
    description_outline: DescriptionOutline | None = None
    faq_entries: list[FAQEntry] | None = None
    differentiation_angle: DifferentiationAngle | None = None
    buyer_persona: BuyerPersona | None = None
    thumbnail_direction: ThumbnailDirection | None = None
    upsell_structure: UpsellStructure | None = None
    red_flags: RedFlagsAssessment | None = None
    niche_viability: NicheViability | None = None
    pricing_strategy: PricingStrategy | None = None
    profile_optimization: ProfileOptimization | None = None
    visual_recommendations: VisualRecommendations | None = None
    generation_complete: bool = False
    llm_cost_usd: float = 0.0

    def completeness_ratio(self) -> float:
        task_fields = [
            self.gig_titles, self.tag_sets, self.package_structure,
            self.description_outline, self.faq_entries, self.differentiation_angle,
            self.buyer_persona, self.thumbnail_direction, self.upsell_structure,
            self.red_flags, self.niche_viability, self.pricing_strategy,
            self.profile_optimization, self.visual_recommendations,
        ]
        populated = sum(1 for f in task_fields if f is not None)
        return populated / len(task_fields)
