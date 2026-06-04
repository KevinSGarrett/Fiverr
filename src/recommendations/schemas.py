"""Pydantic schemas for Stage 13 recommendation LLM outputs."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class RecommendationSchemaBase(BaseModel):
    """Shared schema defaults for forward-compatible LLM payload parsing."""

    model_config = ConfigDict(extra="ignore")


class GigTitle(RecommendationSchemaBase):
    title: str = Field(..., min_length=30, max_length=120)
    positioning_angle: str
    character_count: int = Field(..., ge=30, le=120)
    primary_keyword_present: bool

    @field_validator("title")
    @classmethod
    def _title_must_start_with_i_will(cls, value: str) -> str:
        if not value.lower().startswith("i will"):
            raise ValueError("Gig title must start with 'I will'.")
        return value


class GigTitlesOutput(RecommendationSchemaBase):
    titles: list[GigTitle] = Field(..., min_length=5, max_length=5)


class TagSetsOutput(RecommendationSchemaBase):
    tag_sets: list[list[str]] = Field(..., min_length=5, max_length=5)

    @field_validator("tag_sets")
    @classmethod
    def _must_have_five_tags_per_set(cls, value: list[list[str]]) -> list[list[str]]:
        for index, tag_set in enumerate(value):
            if len(tag_set) != 5:
                raise ValueError(f"Tag set {index} must contain exactly 5 tags.")
            for tag in tag_set:
                if not 2 <= len(tag.strip()) <= 25:
                    raise ValueError("Each tag must be 2-25 characters.")
        return value


class PackageTier(RecommendationSchemaBase):
    name: str = Field(..., min_length=3, max_length=80)
    price: int = Field(..., ge=5, le=5000)
    deliverables: list[str] = Field(..., min_length=1, max_length=10)
    delivery_days: int = Field(..., ge=1, le=60)
    revisions: int = Field(..., ge=0, le=10)


class PackageStructureOutput(RecommendationSchemaBase):
    basic: PackageTier
    standard: PackageTier
    premium: PackageTier

    @model_validator(mode="after")
    def _prices_are_ascending(self) -> PackageStructureOutput:
        if self.standard.price <= self.basic.price:
            raise ValueError("Standard price must exceed Basic price.")
        if self.premium.price <= self.standard.price:
            raise ValueError("Premium price must exceed Standard price.")
        return self


# Backward-compatible alias used by some validation probes/docs.
PackageStructure = PackageStructureOutput


class DescriptionSection(RecommendationSchemaBase):
    heading: str = Field(..., min_length=3, max_length=120)
    copy_direction: str = Field(..., min_length=10, max_length=800)
    proof_elements: list[str] = Field(default_factory=list)
    estimated_words: int = Field(..., ge=20, le=300)


class DescriptionOutlineOutput(RecommendationSchemaBase):
    sections: list[DescriptionSection] = Field(..., min_length=4, max_length=8)

    @model_validator(mode="after")
    def _total_word_estimate_reasonable(self) -> DescriptionOutlineOutput:
        total_estimated_words = sum(section.estimated_words for section in self.sections)
        if total_estimated_words < 200 or total_estimated_words > 1000:
            raise ValueError(f"Total estimated words {total_estimated_words} outside 200-1000 range.")
        return self


class FAQEntry(RecommendationSchemaBase):
    question: str = Field(..., min_length=8, max_length=220)
    answer: str = Field(..., min_length=20, max_length=700)
    addresses_complaint: str | None = None


class FaqEntriesOutput(RecommendationSchemaBase):
    faq_entries: list[FAQEntry] = Field(..., min_length=5, max_length=7)


class Differentiator(RecommendationSchemaBase):
    action: str = Field(..., min_length=8, max_length=240)
    competitor_weakness_exploited: str = Field(..., min_length=3, max_length=300)
    buyer_pain_addressed: str = Field(..., min_length=3, max_length=300)


class DifferentiationAngleOutput(RecommendationSchemaBase):
    positioning_statement: str = Field(..., min_length=60, max_length=800)
    differentiators: list[Differentiator] = Field(..., min_length=1, max_length=8)
    one_sentence_pitch: str = Field(..., min_length=10, max_length=250)


class BuyerPersonaOutput(RecommendationSchemaBase):
    name: str = Field(..., min_length=2, max_length=40)
    role: str = Field(..., min_length=3, max_length=120)
    company_stage: str = Field(..., min_length=2, max_length=120)
    pain_points: list[str] = Field(..., min_length=2, max_length=6)
    budget_range: str = Field(..., min_length=3, max_length=120)
    decision_trigger: str = Field(..., min_length=5, max_length=300)
    where_they_search: str = Field(..., min_length=3, max_length=200)
    what_makes_them_buy: str = Field(..., min_length=5, max_length=300)


class ThumbnailDirectionOutput(RecommendationSchemaBase):
    concept: str = Field(..., min_length=10, max_length=300)
    style: str = Field(..., min_length=3, max_length=200)
    elements_to_include: list[str] = Field(..., min_length=2, max_length=6)
    elements_to_avoid: list[str] = Field(..., min_length=1, max_length=6)
    differentiation_note: str = Field(..., min_length=5, max_length=300)


class UpsellExtra(RecommendationSchemaBase):
    name: str = Field(..., min_length=2, max_length=80)
    price: int = Field(..., ge=5, le=1000)
    description: str = Field(..., min_length=8, max_length=300)


class UpsellStructureOutput(RecommendationSchemaBase):
    extras: list[UpsellExtra] = Field(..., min_length=2, max_length=4)


class RedFlag(RecommendationSchemaBase):
    flag_type: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10, max_length=400)
    severity: str = Field(..., pattern="^(HIGH|MEDIUM|LOW)$")
    mitigation: str = Field(..., min_length=10, max_length=400)


class RedFlagsOutput(RecommendationSchemaBase):
    red_flags: list[RedFlag] = Field(default_factory=list, max_length=10)
    overall_risk_level: str = Field(..., pattern="^(LOW|MEDIUM|HIGH)$")
    proceed_recommendation: str = Field(..., min_length=5, max_length=300)


class NicheViabilityOutput(RecommendationSchemaBase):
    viability_assessment: str = Field(..., min_length=40, max_length=1200)
    timing_assessment: str = Field(..., min_length=10, max_length=300)
    risk_summary: str = Field(..., min_length=10, max_length=300)
    blunt_recommendation: str = Field(..., min_length=5, max_length=180)


class RecommendationOutput(RecommendationSchemaBase):
    gig_titles: GigTitlesOutput | None = None
    tag_sets: TagSetsOutput | None = None
    package_structure: PackageStructureOutput | None = None
    description_outline: DescriptionOutlineOutput | None = None
    faq_entries: FaqEntriesOutput | None = None
    differentiation_angle: DifferentiationAngleOutput | None = None
    buyer_persona: BuyerPersonaOutput | None = None
    thumbnail_direction: ThumbnailDirectionOutput | None = None
    upsell_structure: UpsellStructureOutput | None = None
    red_flags: RedFlagsOutput | None = None
    niche_viability: NicheViabilityOutput | None = None
    pricing_strategy: str | None = None

    generation_complete: bool = False
    failed_tasks: list[str] = Field(default_factory=list)
    total_llm_cost_usd: float = 0.0

    @field_validator("total_llm_cost_usd")
    @classmethod
    def _cost_must_be_non_negative(cls, value: float) -> float:
        if value < 0:
            raise ValueError("total_llm_cost_usd must be non-negative.")
        return value

    @model_validator(mode="after")
    def _auto_set_generation_complete(self) -> RecommendationOutput:
        if "generation_complete" not in self.model_fields_set:
            self.generation_complete = self._all_llm_outputs_present()
        return self

    def _all_llm_outputs_present(self) -> bool:
        return self.completeness_ratio() >= 1.0

    def completeness_ratio(self) -> float:
        """Returns 0.0-1.0 indicating what proportion of LLM outputs are present."""
        fields = [
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
        ]
        present = sum(1 for field_value in fields if field_value is not None)
        return present / len(fields)

