# Recommendation Output Format
# Fiverr Research System — Wave 7

**Document Status:** Complete
**Wave:** 7 — Recommendation Engine
**Purpose:** Full Pydantic RecommendationOutput schema, validation rules per field, storage format in recommendations table, dashboard display format, and export format.

---

## RecommendationOutput Pydantic Schema

This is the complete output schema for a single keyword's recommendation package. It matches the `recommendations` table columns from Wave 3 SCHEMA.md.

```python
# src/schemas/recommendation_output.py

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class GigTitle(BaseModel):
    title: str = Field(..., min_length=30, max_length=120)
    positioning_angle: str  # outcome | specialist | speed | proof | scope
    character_count: int = Field(..., ge=30, le=120)
    primary_keyword_present: bool

    @validator("title")
    def must_start_with_i_will(cls, v):
        if not v.lower().startswith("i will"):
            raise ValueError("Gig title must start with 'I will'")
        return v


class PackageTier(BaseModel):
    name: str = Field(..., min_length=3, max_length=60)
    price: int = Field(..., ge=5, le=5000)
    deliverables: list[str] = Field(..., min_items=2, max_items=10)
    delivery_days: int = Field(..., ge=1, le=60)
    revisions: int = Field(..., ge=0, le=10)


class PackageStructure(BaseModel):
    basic: PackageTier
    standard: PackageTier
    premium: PackageTier

    @validator("standard")
    def standard_higher_than_basic(cls, v, values):
        if "basic" in values and v.price <= values["basic"].price:
            raise ValueError("Standard price must exceed Basic price")
        return v

    @validator("premium")
    def premium_higher_than_standard(cls, v, values):
        if "standard" in values and v.price <= values["standard"].price:
            raise ValueError("Premium price must exceed Standard price")
        return v


class DescriptionSection(BaseModel):
    heading: str = Field(..., min_length=5, max_length=80)
    copy_direction: str = Field(..., min_length=20, max_length=500)
    proof_elements: list[str] = Field(default_factory=list)
    estimated_words: int = Field(..., ge=20, le=300)


class DescriptionOutline(BaseModel):
    sections: list[DescriptionSection] = Field(..., min_items=4, max_items=8)

    @validator("sections")
    def total_word_estimate_reasonable(cls, v):
        total = sum(s.estimated_words for s in v)
        if total < 200 or total > 1000:
            raise ValueError(f"Total estimated words {total} outside 200–1000 range")
        return v


class FAQEntry(BaseModel):
    question: str = Field(..., min_length=10, max_length=200)
    answer: str = Field(..., min_length=30, max_length=500)
    addresses_complaint: Optional[str] = None


class Differentiator(BaseModel):
    action: str = Field(..., min_length=10, max_length=200)
    competitor_weakness_exploited: str
    buyer_pain_addressed: str


class DifferentiationAngle(BaseModel):
    positioning_statement: str = Field(..., min_length=100, max_length=500)
    differentiators: list[Differentiator] = Field(..., min_items=2, max_items=6)
    one_sentence_pitch: str = Field(..., min_length=20, max_length=200)


class BuyerPersona(BaseModel):
    name: str = Field(..., min_length=2, max_length=30)
    role: str = Field(..., min_length=5, max_length=100)
    company_stage: str
    pain_points: list[str] = Field(..., min_items=2, max_items=5)
    budget_range: str
    decision_trigger: str
    where_they_search: str
    what_makes_them_buy: str


class ThumbnailDirection(BaseModel):
    concept: str = Field(..., min_length=20, max_length=200)
    style: str
    elements_to_include: list[str] = Field(..., min_items=2, max_items=5)
    elements_to_avoid: list[str] = Field(..., min_items=1, max_items=4)
    differentiation_note: str


class UpsellExtra(BaseModel):
    name: str = Field(..., min_length=5, max_length=60)
    price: int = Field(..., ge=5, le=500)
    description: str = Field(..., min_length=10, max_length=200)


class RedFlag(BaseModel):
    flag_type: str
    description: str = Field(..., min_length=20, max_length=300)
    severity: str  # HIGH | MEDIUM | LOW | INFO
    mitigation: str = Field(..., min_length=10, max_length=300)


class RedFlagsAssessment(BaseModel):
    red_flags: list[RedFlag] = Field(default_factory=list, max_items=10)
    overall_risk_level: str  # LOW | MEDIUM | HIGH
    proceed_recommendation: str


class NicheViability(BaseModel):
    viability_assessment: str = Field(..., min_length=100, max_length=600)
    timing_assessment: str = Field(..., min_length=20, max_length=200)
    risk_summary: str = Field(..., min_length=20, max_length=200)
    blunt_recommendation: str = Field(..., min_length=10, max_length=150)


class RecommendationOutput(BaseModel):
    """
    Complete recommendation package for a single keyword.
    This is the full output of all 11 LLM tasks in Stage 13.
    """
    # Identity
    keyword_id: int
    keyword_text: str
    niche_id: str
    niche_name: str
    tag: str
    final_score: float

    # LLM outputs (any field can be None if the corresponding task failed)
    gig_titles: Optional[list[GigTitle]] = None
    tag_sets: Optional[list[list[str]]] = None
    package_structure: Optional[PackageStructure] = None
    description_outline: Optional[DescriptionOutline] = None
    faq_entries: Optional[list[FAQEntry]] = None
    differentiation_angle: Optional[DifferentiationAngle] = None
    buyer_persona: Optional[BuyerPersona] = None
    thumbnail_direction: Optional[ThumbnailDirection] = None
    upsell_structure: Optional[list[UpsellExtra]] = None
    red_flags: Optional[RedFlagsAssessment] = None
    niche_viability_assessment: Optional[NicheViability] = None

    # Metadata
    generation_complete: bool = False
    llm_cost_usd: float = 0.0
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("gig_titles")
    def must_have_five_titles(cls, v):
        if v is not None and len(v) != 5:
            raise ValueError(f"Expected 5 gig titles, got {len(v)}")
        return v

    @validator("tag_sets")
    def must_have_five_tag_sets(cls, v):
        if v is not None:
            if len(v) != 5:
                raise ValueError(f"Expected 5 tag sets, got {len(v)}")
            for i, tag_set in enumerate(v):
                if len(tag_set) != 5:
                    raise ValueError(f"Tag set {i} must have exactly 5 tags, got {len(tag_set)}")
        return v

    @validator("faq_entries")
    def faq_count_range(cls, v):
        if v is not None and not (5 <= len(v) <= 7):
            raise ValueError(f"Expected 5–7 FAQ entries, got {len(v)}")
        return v

    def completeness_ratio(self) -> float:
        """Returns 0.0–1.0 indicating what proportion of LLM outputs are present."""
        fields = [
            self.gig_titles, self.tag_sets, self.package_structure,
            self.description_outline, self.faq_entries, self.differentiation_angle,
            self.buyer_persona, self.thumbnail_direction, self.upsell_structure,
            self.red_flags, self.niche_viability_assessment,
        ]
        present = sum(1 for f in fields if f is not None)
        return present / len(fields)
```

---

## Storage Format in recommendations Table

The Pydantic schema maps directly to the `recommendations` table columns:

| Pydantic Field | DB Column | DB Type | Notes |
|---|---|---|---|
| gig_titles | gig_titles | JSON | Serialized as list of dicts |
| tag_sets | tag_sets | JSON | 2D array |
| package_structure | package_structure | JSON | Nested dict |
| description_outline | description_outline | JSON | Nested dict with sections array |
| faq_entries | faq_entries | JSON | Array of Q&A dicts |
| differentiation_angle | differentiation_angle | Text | Stored as the positioning_statement string. Full DifferentiationAngle JSON stored in description_outline for full access. |
| buyer_persona | buyer_persona | JSON | Full persona dict |
| thumbnail_direction | thumbnail_direction | Text | Stored as the concept string |
| upsell_structure | upsell_structure | JSON | Array of extra dicts |
| red_flags | red_flags | JSON | Full RedFlagsAssessment dict |
| niche_viability_assessment | niche_viability_assessment | Text | Stored as viability_assessment string |
| generation_complete | generation_complete | Boolean | True if all 11 tasks succeeded |
| llm_cost_usd | llm_cost_usd | Float | Total cost for all 11 tasks |

---

## Dashboard Display Format

### Recommendation Card Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ⭐ STRONG GO — "AI SaaS PRD"                    Score: 82.3    │
│ Niche: PRD / AI SaaS MVP Roadmap                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ VIABILITY: This keyword scores 82 driven by strong demand (75)  │
│ and exploitable competitor weaknesses (69)...                   │
│                                                                 │
│ ─── GIG TITLES ─────────────────────────────────────────────── │
│ 1. I will write a developer-ready AI SaaS MVP PRD...    [Copy] │
│ 2. I will create your complete AI product requirements... [Copy]│
│ 3. ...                                                          │
│                                                                 │
│ ─── PACKAGES ───────────────────────────────────────────────── │
│ Basic ($95)     Standard ($225)     Premium ($395)              │
│ Scope Audit     Complete PRD        PRD + Roadmap Bundle       │
│ 3 days, 1 rev   5 days, 2 rev      7 days, 3 rev              │
│                                                                 │
│ ─── DIFFERENTIATION ANGLE ──────────────────────────────────── │
│ "Top 10 gigs have generic descriptions with no proof..."       │
│ → Include proof block: X clients, Y years, Z deliverables      │
│ → Add architecture diagrams (competitors don't include these)   │
│                                                                 │
│ ─── FAQ ────────────────────────────────────────────────────── │
│ Q: What do I need to provide?                                   │
│ A: A structured intake questionnaire covering...                │
│ ...                                                             │
│                                                                 │
│ ─── BUYER PERSONA ──────────────────────────────────────────── │
│ Alex — Non-technical SaaS founder, pre-seed stage              │
│ Pain: Needs to communicate vision to developers                 │
│ Budget: $100–$400 | Trigger: Just hired first developer         │
│                                                                 │
│ ─── RED FLAGS ──────────────────────────────────────────────── │
│ ⚠ MEDIUM: Top 3 sellers have 500+ reviews...                   │
│   → Build 3+ portfolio samples before publishing               │
│                                                                 │
│ [Export to Markdown]  [Export to JSON]  [Copy All]              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Export Formats

### Markdown Export

Generated per recommendation for easy copy-paste into note-taking apps:

```markdown
# Recommendation: AI SaaS PRD

**Tag:** STRONG GO | **Score:** 82.3 | **Niche:** PRD / AI SaaS MVP Roadmap

## Viability Assessment
This keyword scores 82 driven by strong demand (75)...

## Gig Title Options
1. I will write a developer-ready AI SaaS MVP PRD and technical roadmap
2. I will create a complete AI product requirements document...
...

## Packages
| Tier | Price | Deliverables | Delivery | Revisions |
|---|---|---|---|---|
| Basic | $95 | Scope audit, feature matrix | 3 days | 1 |
| Standard | $225 | Complete PRD, user stories | 5 days | 2 |
| Premium | $395 | PRD + roadmap + diagrams | 7 days | 3 |

## Differentiation Angle
Top 10 gigs have generic descriptions with no proof elements...

## FAQ
**Q: What do I need to provide?**
A: A structured intake questionnaire...
...

## Red Flags
- ⚠ MEDIUM: Top 3 sellers have 500+ reviews...
```

### JSON Export

Full `RecommendationOutput` serialized as JSON for programmatic use:

```python
# Export function
def export_recommendation_json(recommendation: Recommendation) -> str:
    output = RecommendationOutput(
        keyword_id=recommendation.keyword_id,
        keyword_text=get_keyword_text(recommendation.keyword_id),
        niche_id=recommendation.niche_id,
        niche_name=get_niche_name(recommendation.niche_id),
        tag=recommendation.tag,
        final_score=recommendation.final_score,
        gig_titles=recommendation.gig_titles,
        tag_sets=recommendation.tag_sets,
        package_structure=recommendation.package_structure,
        description_outline=recommendation.description_outline,
        faq_entries=recommendation.faq_entries,
        differentiation_angle=recommendation.differentiation_angle,
        buyer_persona=recommendation.buyer_persona,
        thumbnail_direction=recommendation.thumbnail_direction,
        upsell_structure=recommendation.upsell_structure,
        red_flags=recommendation.red_flags,
        niche_viability_assessment=recommendation.niche_viability_assessment,
        generation_complete=recommendation.generation_complete,
        llm_cost_usd=recommendation.llm_cost_usd,
        generated_at=recommendation.generated_at,
    )
    return output.model_dump_json(indent=2)
```

---

## Validation Summary

| Field | Validation Rules |
|---|---|
| gig_titles | Exactly 5 titles, each 30–120 chars, starts with "I will", keyword present |
| tag_sets | Exactly 5 sets, each with exactly 5 tags, each tag 2–25 chars |
| package_structure | 3 tiers (basic/standard/premium), prices ascending, 2–10 deliverables each |
| description_outline | 4–8 sections, total est. words 200–1000, each section has heading + direction |
| faq_entries | 5–7 entries, each with question (10–200 chars) and answer (30–500 chars) |
| differentiation_angle | Positioning statement 100–500 chars, 2–6 differentiators with action + weakness + pain |
| buyer_persona | All 8 fields required, name 2–30 chars, 2–5 pain points |
| thumbnail_direction | Concept 20–200 chars, 2–5 include elements, 1–4 avoid elements |
| upsell_structure | 2–4 extras, each $5–500, name 5–60 chars |
| red_flags | 0–10 flags, each with type + description + severity + mitigation |
| niche_viability_assessment | Assessment 100–600 chars, timing 20–200, risk 20–200, blunt rec 10–150 |
