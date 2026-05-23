"""Recommendation engine contracts for Stage 13."""

from __future__ import annotations

from dataclasses import dataclass, field
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


@dataclass(slots=True)
class RecommendationContext:
    """Shared context payload for recommendation generation and gating."""

    # Required Stage-13 identity + score fields.
    keyword_id: int = 0
    keyword_text: str = ""
    niche_id: int | str = ""
    tag: str = "MONITOR"
    final_score: float = 0.0
    confidence_modifier: float = 0.5
    demand_score: float | None = None
    competition_score: float | None = None
    opportunity_score: float | None = None
    top_competitor_weaknesses: list[dict[str, Any]] = field(default_factory=list)
    cluster_label: str | None = None
    cluster_size: int | None = None
    saturation_score: float | None = None
    feasibility_score: float | None = None
    niche_name: str = ""
    run_id: str | int | None = None

    # Optional enrichment fields used by downstream tasks.
    reviewer_pain_points: list[str] = field(default_factory=list)
    market_price_range: dict[str, Any] | None = None
    top_buyer_complaints: list[str] = field(default_factory=list)
    top_buyer_praise: list[str] = field(default_factory=list)
    red_flag_patterns: list[str] = field(default_factory=list)

    # Compatibility aliases/containers used by earlier cycles.
    keyword: str = ""
    score_data: dict[str, Any] = field(default_factory=dict)
    competitor_data: dict[str, Any] = field(default_factory=dict)
    pricing_data: dict[str, Any] = field(default_factory=dict)
    visual_data: dict[str, Any] = field(default_factory=dict)
    review_insights: dict[str, Any] = field(default_factory=dict)
    external_signals: dict[str, Any] = field(default_factory=dict)

    # Existing Stage-13 task context fields.
    score_components: dict[str, Any] = field(default_factory=dict)
    positioning_gaps: list[dict[str, Any]] | None = None
    dominant_sellers: list[dict[str, Any]] | None = None

    # Stage-12 pricing enrichment fields.
    price_distribution: dict[str, Any] | None = None
    price_review_correlation: dict[str, Any] | None = None
    market_type: str | None = None
    calculated_entry_prices: dict[str, Any] | None = None
    calculated_price_ladder: list[dict[str, Any]] | None = None
    new_seller_discount_pct: float | None = None
    competitor_price_positions: list[dict[str, Any]] | None = None

    def __post_init__(self) -> None:
        if not self.keyword_text and self.keyword:
            self.keyword_text = self.keyword
        if not self.keyword and self.keyword_text:
            self.keyword = self.keyword_text
        if not self.niche_name and self.niche_id not in ("", None):
            self.niche_name = str(self.niche_id)

    def completeness_ratio(self) -> float:
        optional_fields = [
            self.score_data,
            self.competitor_data,
            self.pricing_data,
            self.visual_data,
            self.review_insights,
            self.external_signals,
        ]
        populated = sum(1 for value in optional_fields if value)
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
            self.gig_titles,
            self.tag_sets,
            self.package_structure,
            self.description_outline,
            self.faq_entries,
            self.differentiation_angle,
            self.buyer_persona,
            self.thumbnail_direction,
            self.upsell_structure,
            self.red_flags,
            self.niche_viability,
            self.pricing_strategy,
            self.profile_optimization,
            self.visual_recommendations,
        ]
        populated = sum(1 for field_value in task_fields if field_value is not None)
        return populated / len(task_fields)
