# Pricing Recommendations LLM Task
# Fiverr Research System — Wave 9

**Document Status:** Complete
**Wave:** 9 — Pricing Strategy Engine
**Purpose:** LLM task #12 for pricing recommendation generation — prompt template, output schema, integration into RecommendationOutput, model selection, and cache strategy.

---

## Task Overview

| Property | Value |
|---|---|
| Task Number | 12 (added to existing 11 recommendation tasks) |
| Model | gpt-4o |
| Estimated Cost | ~$0.015 per keyword |
| Cache Key | keyword_text + price_distribution_hash + competitor_data_hash |
| Temperature | 0.2 |
| Runs Concurrently | Yes — added to asyncio.gather() with other 11 tasks |
| Depends On | Stage 10.5 (Price Distribution Analysis) must complete first |
| Skip Condition | Skipped if no price_analysis data exists for this keyword |

---

## Task Input

The pricing LLM task receives the standard `RecommendationContext` plus new pricing-specific fields:

```python
# Extended RecommendationContext (added fields for Wave 9)

class RecommendationContext(BaseModel):
    # ... all existing fields from Wave 7 ...

    # NEW — Wave 9 pricing fields
    price_distribution: dict | None = None
    # {
    #   "basic": {"median": 100, "mean": 127, "q1": 75, "q3": 175, "clusters": [...], "gaps": [...]},
    #   "standard": {"median": 200, ...},
    #   "premium": {"median": 375, ...}
    # }

    price_review_correlation: dict | None = None
    # {"pearson": 0.312, "moat_strength": "MEDIUM", "review_premium_usd": 45.0, ...}

    market_type: str | None = None
    # "COMMODITY" | "MODERATE_SPREAD" | "WIDE_SPREAD" | "FRAGMENTED"

    calculated_entry_prices: dict | None = None
    # {"basic": 65, "standard": 145, "premium": 280} — from NEW_SELLER_PRICING_MODEL

    calculated_price_ladder: list[dict] | None = None
    # [{"milestone_reviews": 5, "basic": 75, "standard": 160, "premium": 305}, ...]

    new_seller_discount_pct: float | None = None
    # How much less new sellers charge vs. market average (e.g., 43.1%)

    competitor_price_positions: list[dict] | None = None
    # [{"seller": "username", "level": "Level 2", "reviews": 234, "basic": 150, "standard": 300}, ...]
```

---

## Prompt Template — pricing_strategy.j2

```jinja2
You are a Fiverr pricing strategist for NEW SELLERS with zero reviews.

KEYWORD: "{{ keyword_text }}"
NICHE: {{ niche_name }}
TAG: {{ tag }} (Final Score: {{ final_score | round(1) }})

MARKET PRICING DATA:
{% if price_distribution %}
Basic tier:
  - Median: ${{ price_distribution.basic.median | round(0) }}
  - Mean: ${{ price_distribution.basic.mean | round(0) }}
  - Range: ${{ price_distribution.basic.min | round(0) }} – ${{ price_distribution.basic.max | round(0) }}
  - 25th percentile: ${{ price_distribution.basic.q1 | round(0) }}
  - 75th percentile: ${{ price_distribution.basic.q3 | round(0) }}
  {% if price_distribution.basic.clusters %}
  - Price clusters: {% for c in price_distribution.basic.clusters[:3] %}${{ c.center | round(0) }} ({{ c.pct }}%){% if not loop.last %}, {% endif %}{% endfor %}
  {% endif %}
  {% if price_distribution.basic.gaps %}
  - Price gaps: {% for g in price_distribution.basic.gaps[:2] %}${{ g.gap_start | round(0) }}–${{ g.gap_end | round(0) }}{% if not loop.last %}, {% endif %}{% endfor %}
  {% endif %}

Standard tier:
  - Median: ${{ price_distribution.standard.median | round(0) }}
  - Range: ${{ price_distribution.standard.min | round(0) }} – ${{ price_distribution.standard.max | round(0) }}

Premium tier:
  - Median: ${{ price_distribution.premium.median | round(0) }}
  - Range: ${{ price_distribution.premium.min | round(0) }} – ${{ price_distribution.premium.max | round(0) }}
{% endif %}

MARKET STRUCTURE: {{ market_type or "Unknown" }}
{% if price_review_correlation %}
REVIEW MOAT: {{ price_review_correlation.moat_strength }}
  - Price-review correlation: {{ price_review_correlation.pearson | round(3) }}
  - Established sellers charge ${{ price_review_correlation.review_premium_usd | round(0) }} more than new sellers
  - New sellers currently average: ${{ price_review_correlation.new_seller_avg_price | round(0) }}
  - New sellers discount vs market: {{ price_review_correlation.new_seller_discount_pct | round(0) }}%
{% endif %}

ALGORITHM-CALCULATED ENTRY PRICES:
{% if calculated_entry_prices %}
  Basic: ${{ calculated_entry_prices.basic | round(0) }}
  Standard: ${{ calculated_entry_prices.standard | round(0) }}
  Premium: ${{ calculated_entry_prices.premium | round(0) }}
{% endif %}

TOP COMPETITOR PRICING:
{% for comp in competitor_price_positions[:5] %}
  {{ comp.seller }} ({{ comp.level }}, {{ comp.reviews }} reviews): Basic ${{ comp.basic }}, Standard ${{ comp.standard | default("N/A") }}, Premium ${{ comp.premium | default("N/A") }}
{% endfor %}

COMPETITOR WEAKNESSES:
{% for comp in top_competitor_weaknesses[:3] %}
  - {{ comp.gig_title }}: {% for w in comp.weaknesses[:2] %}{{ w.weakness }}{% if not loop.last %}, {% endif %}{% endfor %}
{% endfor %}

YOUR TASK:
Create a complete pricing strategy for a NEW SELLER with 0 reviews entering this keyword.

Requirements:
1. Recommend specific Basic / Standard / Premium prices — use the algorithm-calculated prices as a starting point but adjust based on the market data and your strategic analysis
2. Explain WHY these prices work — reference the specific market data (clusters, gaps, moat strength)
3. Provide a price ladder: specific prices to set at 5, 10, 25, 50, and 100 review milestones
4. Identify the "first 5 orders" acquisition pricing — even more aggressive than entry pricing
5. Flag any pricing risks (race-to-bottom danger, undercutting too aggressively, pricing above market without proof)
6. Recommend which tier to LEAD with (which package to make most attractive for first orders)
7. Suggest 2-3 gig extras (upsells) with specific prices that increase AOV from day one

Return JSON only. No preamble.

{
  "pricing_strategy": {
    "entry_prices": {
      "basic": integer,
      "standard": integer,
      "premium": integer,
      "lead_tier": "basic|standard",
      "lead_tier_reasoning": "string"
    },
    "acquisition_prices": {
      "basic": integer,
      "standard": integer,
      "premium": integer,
      "acquisition_period": "string (e.g., 'first 5 orders' or 'first 2 weeks')"
    },
    "price_ladder": [
      {
        "milestone_reviews": integer,
        "basic": integer,
        "standard": integer,
        "premium": integer,
        "adjustment_rationale": "string"
      }
    ],
    "strategy_narrative": "string (100-200 words explaining the pricing logic, referencing market data)",
    "pricing_risks": [
      {"risk": "string", "severity": "HIGH|MEDIUM|LOW", "mitigation": "string"}
    ],
    "recommended_extras": [
      {"name": "string", "price": integer, "rationale": "string"}
    ],
    "projected_aov": {
      "at_entry": number,
      "at_50_reviews": number,
      "aov_growth_pct": number
    }
  }
}
```

---

## Output Schema (Pydantic)

```python
# src/schemas/pricing_output.py

from pydantic import BaseModel, Field, validator
from typing import Optional

class EntryPrices(BaseModel):
    basic: int = Field(..., ge=5, le=2000)
    standard: int = Field(..., ge=10, le=5000)
    premium: int = Field(..., ge=20, le=10000)
    lead_tier: str  # "basic" or "standard"
    lead_tier_reasoning: str = Field(..., min_length=20, max_length=200)

    @validator("standard")
    def standard_above_basic(cls, v, values):
        if "basic" in values and v <= values["basic"]:
            raise ValueError("Standard must be above Basic")
        return v

    @validator("premium")
    def premium_above_standard(cls, v, values):
        if "standard" in values and v <= values["standard"]:
            raise ValueError("Premium must be above Standard")
        return v


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
    severity: str  # HIGH, MEDIUM, LOW
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
    price_ladder: list[PriceLadderStep] = Field(..., min_items=4, max_items=8)
    strategy_narrative: str = Field(..., min_length=100, max_length=500)
    pricing_risks: list[PricingRisk] = Field(default_factory=list, max_items=5)
    recommended_extras: list[RecommendedExtra] = Field(..., min_items=2, max_items=4)
    projected_aov: ProjectedAOV

    @validator("price_ladder")
    def ladder_prices_ascending(cls, v):
        for i in range(1, len(v)):
            if v[i].basic < v[i-1].basic:
                raise ValueError(f"Price ladder step {i} basic price must be >= step {i-1}")
        return v
```

---

## Integration into RecommendationOutput

The `RecommendationOutput` schema from Wave 7 gets a new field:

```python
class RecommendationOutput(BaseModel):
    # ... all 11 existing fields ...

    # NEW — Wave 9
    pricing_strategy: Optional[PricingStrategy] = None

    # Updated completeness calculation
    def completeness_ratio(self) -> float:
        fields = [
            self.gig_titles, self.tag_sets, self.package_structure,
            self.description_outline, self.faq_entries, self.differentiation_angle,
            self.buyer_persona, self.thumbnail_direction, self.upsell_structure,
            self.red_flags, self.niche_viability_assessment,
            self.pricing_strategy,  # NEW — 12 fields now
        ]
        present = sum(1 for f in fields if f is not None)
        return present / len(fields)
```

---

## Async Execution — Updated gather()

```python
async def generate_recommendation(
    keyword_id: int,
    context: RecommendationContext,
    llm_client,
    cache,
    db,
) -> Recommendation:
    """Updated to include pricing_strategy as task 12."""

    tasks = [
        generate_gig_titles(context, llm_client, cache),
        generate_tag_sets(context, llm_client, cache),
        generate_package_structure(context, llm_client, cache),
        generate_description_outline(context, llm_client, cache),
        generate_faq_entries(context, llm_client, cache),
        generate_differentiation_angle(context, llm_client, cache),
        generate_buyer_persona(context, llm_client, cache),
        generate_thumbnail_direction(context, llm_client, cache),
        generate_upsell_structure(context, llm_client, cache),
        generate_red_flags(context, llm_client, cache),
        generate_niche_viability(context, llm_client, cache),
        generate_pricing_strategy(context, llm_client, cache),  # NEW — Task 12
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    field_names = [
        "gig_titles", "tag_sets", "package_structure", "description_outline",
        "faq_entries", "differentiation_angle", "buyer_persona",
        "thumbnail_direction", "upsell_structure", "red_flags",
        "niche_viability_assessment",
        "pricing_strategy",  # NEW
    ]

    # ... rest of the processing unchanged ...
```

---

## Updated Cost Estimation

| Task | Model | Est. Cost |
|---|---|---|
| Tasks 1–11 (existing) | gpt-4o / gpt-4o-mini | ~$0.11 |
| Task 12: Pricing strategy | gpt-4o | ~$0.015 |
| **Total per keyword** | | **~$0.125** |

With cache hits: **~$0.06–0.09** per keyword.

---

## Skip Condition

```python
async def generate_pricing_strategy(
    context: RecommendationContext,
    llm_client,
    cache,
) -> dict | None:
    """
    Task 12: Generate pricing strategy.
    Skipped if no price distribution data available.
    """
    if not context.price_distribution:
        log.info(f"Skipping pricing_strategy for {context.keyword_text} — "
                 "no price distribution data")
        return {"output": None, "cost_usd": 0.0}

    # Render prompt
    prompt = render_template("pricing_strategy.j2", context)

    # Check cache
    cache_key = build_cache_key("gpt-4o", 0.2, prompt)
    cached = cache.get(cache_key)
    if cached:
        return {"output": cached, "cost_usd": 0.0}

    # Call LLM
    result = await llm_client.complete(
        prompt=prompt,
        model="gpt-4o",
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    # Parse and validate
    parsed = json.loads(result.content)
    strategy = PricingStrategy(**parsed["pricing_strategy"])

    # Cache result
    cache.set(cache_key, strategy.model_dump())

    return {
        "output": strategy.model_dump(),
        "cost_usd": result.usage_cost,
    }
```

---

## Retry and Validation

Same retry policy as other gpt-4o tasks (from Wave 4 RETRY_AND_CHECKPOINT.md):
1. First attempt: structured JSON output call
2. On ValidationError: one self-correction retry with error appended to prompt
3. On second failure: store null, set `generation_complete = False`

Key validations:
- Prices must be ascending (basic < standard < premium) at every ladder step
- Price ladder must have at least 4 steps
- Strategy narrative must be 100–500 words
- All prices must be above floor minimums
