# Recommendation Engine
# Fiverr Research System — Wave 7

**Document Status:** Complete
**Wave:** 7 — Recommendation Engine
**Purpose:** Stage 13 orchestration — which keywords trigger recommendations, gating logic, parallel LLM task execution, cost estimation, skip logic for unchanged scores, and storage design.

---

## Design Goals

1. Generate a complete, actionable gig recommendation package for every keyword tagged STRONG GO or CONDITIONAL GO
2. Each recommendation contains 11 LLM-generated components — enough to draft a real Fiverr gig immediately
3. Recommendations are only regenerated when underlying scores change significantly (>5 points)
4. LLM tasks can run concurrently per keyword (11 independent tasks)
5. Total LLM cost per recommendation is estimated at $0.05–0.15 per keyword
6. Results stored in `recommendations` table with `generation_complete` flag

---

## Stage 13 Orchestration Flow

```
[Stage 12 Complete — Opportunity Rankings Written]
        │
        ▼
[Query keywords with tag = STRONG GO or CONDITIONAL GO]
        │
        ▼
[Apply gating checks per keyword]
        │
    ┌───┴───────────────┐
   PASS                SKIP
    │                    │
    ▼                    ▼
[Check skip logic]   [Log: "Keyword X skipped — gate not passed"]
    │
    ├── Score unchanged (< 5 points) → Skip (reuse existing recommendation)
    │
    ├── Score changed or no recommendation exists →
    │       │
    │       ▼
    │   [Build recommendation context: scores, competitor data, clusters]
    │       │
    │       ▼
    │   [Execute 11 LLM tasks (async gather)]
    │       │
    │       ▼
    │   [Parse + validate all outputs]
    │       │
    │       ▼
    │   [Write recommendations table row]
    │       │
    │       ▼
    │   [Set generation_complete = True if all 11 tasks succeeded]
    │       │
    │       ▼
    │   [Log LLM cost for this recommendation]
    │
    └── [Next keyword]
```

---

## Recommendation Eligibility

```python
# src/scoring/recommendation_engine.py

def get_eligible_keywords(run_id: str, db, config) -> list[dict]:
    """
    Returns keywords eligible for recommendation generation in this run.
    """
    min_tag = config.get("recommendations", {}).get("min_tag", "CONDITIONAL GO")
    eligible_tags = _tags_at_or_above(min_tag)
    # Default: ["STRONG GO", "CONDITIONAL GO"]

    rankings = db.query(OpportunityRanking).filter(
        OpportunityRanking.run_id == run_id,
        OpportunityRanking.tag.in_(eligible_tags),
    ).all()

    eligible = []
    for ranking in rankings:
        keyword = db.query(Keyword).filter(Keyword.id == ranking.keyword_id).first()
        niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()

        # Skip niches with recommendation_generation = false in config
        niche_config = get_niche_yaml_config(keyword.niche_id)
        if not getattr(niche_config.llm, "recommendation_generation", True):
            continue

        eligible.append({
            "keyword_id": keyword.id,
            "keyword_text": keyword.keyword_text,
            "niche_id": keyword.niche_id,
            "tag": ranking.tag,
            "final_score": ranking.final_score,
            "confidence_modifier": get_confidence_modifier(keyword.id, db),
        })

    return eligible

def _tags_at_or_above(min_tag: str) -> list[str]:
    TAG_ORDER = ["STRONG GO", "CONDITIONAL GO", "MONITOR", "CAUTION", "PASS"]
    idx = TAG_ORDER.index(min_tag)
    return TAG_ORDER[:idx + 1]
```

---

## Gating Checks

Before generating a recommendation, these gates must pass:

```python
def passes_recommendation_gates(keyword_data: dict, db) -> tuple[bool, str]:
    """
    Returns (passes: bool, reason: str).
    """
    keyword_id = keyword_data["keyword_id"]

    # Gate 1: Confidence Modifier minimum
    if keyword_data["confidence_modifier"] < 0.40:
        return False, "Confidence modifier below 0.40 — data too unreliable for recommendations"

    # Gate 2: Demand Score must exist and be > 20
    score = db.query(KeywordScore).filter(KeywordScore.keyword_id == keyword_id).first()
    if score is None or score.demand_score is None or score.demand_score < 20:
        return False, "Demand score missing or below 20 — insufficient buyer interest"

    # Gate 3: At least one competitor gig must have been analyzed
    gig_quality_count = db.query(GigQualityScore).filter(
        GigQualityScore.keyword_id == keyword_id,
        GigQualityScore.analysis_complete == True,
    ).count()
    if gig_quality_count == 0:
        return False, "No gig quality analysis available — cannot generate differentiation angle"

    # Gate 4: User override — if keyword is manually marked for recommendation, skip other gates
    if is_keyword_force_recommended(keyword_id, db):
        return True, "User override — forced recommendation"

    return True, "All gates passed"
```

---

## Skip Logic — Avoid Regenerating Unchanged Recommendations

```python
def should_regenerate_recommendation(keyword_id: int, current_final_score: float, db) -> bool:
    """
    Returns True if the recommendation should be regenerated.
    Skip regeneration if scores haven't changed significantly.
    """
    existing = db.query(Recommendation).filter(
        Recommendation.keyword_id == keyword_id,
        Recommendation.generation_complete == True,
    ).first()

    if existing is None:
        return True  # No existing recommendation — generate

    # Check if final_score changed by more than 5 points
    score_delta = abs(current_final_score - existing.final_score)
    if score_delta > 5.0:
        return True  # Significant score change — regenerate

    # Check if competitor data refreshed since recommendation was generated
    latest_competitor = get_latest_competitor_analysis_timestamp(keyword_id, db)
    if latest_competitor and latest_competitor > existing.generated_at:
        return True  # New competitor data — regenerate

    return False  # No significant changes — skip
```

---

## LLM Task Execution (Async Concurrent)

All 11 LLM tasks for a single keyword run concurrently via `asyncio.gather()`:

```python
import asyncio

async def generate_recommendation(
    keyword_id: int,
    context: RecommendationContext,
    llm_client,
    cache,
    db,
) -> Recommendation:
    """
    Runs all 11 LLM tasks concurrently for a single keyword.
    Returns a Recommendation object (may be partial if some tasks failed).
    """
    tasks = [
        generate_gig_titles(context, llm_client, cache),          # gpt-4o
        generate_tag_sets(context, llm_client, cache),             # gpt-4o-mini
        generate_package_structure(context, llm_client, cache),    # gpt-4o
        generate_description_outline(context, llm_client, cache),  # gpt-4o
        generate_faq_entries(context, llm_client, cache),          # gpt-4o-mini
        generate_differentiation_angle(context, llm_client, cache),# gpt-4o
        generate_buyer_persona(context, llm_client, cache),        # gpt-4o-mini
        generate_thumbnail_direction(context, llm_client, cache),  # gpt-4o-mini
        generate_upsell_structure(context, llm_client, cache),     # gpt-4o-mini
        generate_red_flags(context, llm_client, cache),            # gpt-4o
        generate_niche_viability(context, llm_client, cache),      # gpt-4o
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Map results to fields
    field_names = [
        "gig_titles", "tag_sets", "package_structure", "description_outline",
        "faq_entries", "differentiation_angle", "buyer_persona",
        "thumbnail_direction", "upsell_structure", "red_flags",
        "niche_viability_assessment",
    ]

    recommendation_data = {}
    all_succeeded = True
    total_cost = 0.0

    for field, result in zip(field_names, results):
        if isinstance(result, Exception):
            recommendation_data[field] = None
            all_succeeded = False
            log.warning(f"LLM task {field} failed for keyword {keyword_id}: {result}")
        else:
            recommendation_data[field] = result.get("output")
            total_cost += result.get("cost_usd", 0.0)

    recommendation_data["generation_complete"] = all_succeeded
    recommendation_data["llm_cost_usd"] = total_cost

    return recommendation_data
```

---

## Recommendation Context Builder

All 11 LLM tasks receive the same context object — assembled once per keyword:

```python
from pydantic import BaseModel

class RecommendationContext(BaseModel):
    """All data needed by the 11 recommendation LLM tasks."""

    # Keyword identity
    keyword_id: int
    keyword_text: str
    niche_id: str
    niche_name: str
    tag: str
    final_score: float

    # Scoring context
    demand_score: float | None
    competition_score: float | None
    opportunity_score: float | None
    feasibility_score: float | None
    profitability_score: float | None
    score_components: dict

    # Competitor intelligence (from Wave 5)
    top_competitor_weaknesses: list[dict]
    # [{"gig_title": "...", "weaknesses": [{"weakness": "...", "severity": "HIGH"}]}]
    cluster_synthesis_narrative: str | None
    entry_feasibility_rating: float | None
    dominant_sellers: list[dict] | None
    positioning_gaps: list[dict] | None

    # Review intelligence
    top_buyer_complaints: list[str]
    top_buyer_praise: list[str]
    red_flag_patterns: list[str]

    # Niche metadata (from config.yaml)
    starter_price_basic: int
    starter_price_standard: int
    starter_price_premium: int
    hard_exclusions: list[str]

    # Demand signals
    total_result_count: int | None
    trends_slope: str | None
    reddit_intent_score: float | None

    # Cluster context
    cluster_label: str | None
    opportunity_narrative: str | None


def build_recommendation_context(keyword_id: int, db, config) -> RecommendationContext:
    """Assembles the complete context for all 11 LLM tasks."""
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    scores = db.query(KeywordScore).filter(KeywordScore.keyword_id == keyword_id).first()
    niche_config = get_niche_yaml_config(keyword.niche_id)

    # Competitor data
    top_weaknesses = get_top_competitor_weaknesses(keyword_id, db, limit=5)
    cluster_analysis = get_cluster_analysis_for_keyword(keyword_id, db)
    competitor_analysis = get_competitor_analysis_for_keyword(keyword_id, db)

    # Review intelligence
    review_insights = get_review_insights_for_recommendation(keyword.niche_id, keyword_id, db)

    # External signals
    search_result = get_latest_search_result(keyword_id, db)
    trends = get_external_signal(keyword_id, "google_trends", db)
    reddit = get_external_signal_for_niche(keyword.niche_id, "reddit_demand", db)

    return RecommendationContext(
        keyword_id=keyword_id,
        keyword_text=keyword.keyword_text,
        niche_id=keyword.niche_id,
        niche_name=niche_config.name,
        tag=scores.tag if scores else "MONITOR",
        final_score=scores.final_score if scores else 0,
        demand_score=scores.demand_score if scores else None,
        competition_score=scores.competition_score if scores else None,
        opportunity_score=scores.opportunity_score if scores else None,
        feasibility_score=scores.feasibility_score if scores else None,
        profitability_score=scores.profitability_score if scores else None,
        score_components=scores.score_components if scores else {},
        top_competitor_weaknesses=top_weaknesses,
        cluster_synthesis_narrative=(
            competitor_analysis.synthesis_narrative if competitor_analysis else None
        ),
        entry_feasibility_rating=(
            competitor_analysis.entry_feasibility_rating if competitor_analysis else None
        ),
        dominant_sellers=(
            competitor_analysis.dominant_sellers if competitor_analysis else None
        ),
        positioning_gaps=(
            competitor_analysis.positioning_gaps if competitor_analysis else None
        ),
        top_buyer_complaints=review_insights.get("top_buyer_complaints", []),
        top_buyer_praise=review_insights.get("top_buyer_praise", []),
        red_flag_patterns=review_insights.get("competitor_failure_modes", []),
        starter_price_basic=niche_config.metadata.starter_price_basic,
        starter_price_standard=niche_config.metadata.starter_price_standard,
        starter_price_premium=niche_config.metadata.starter_price_premium,
        hard_exclusions=niche_config.metadata.hard_exclusions or [],
        total_result_count=(
            search_result.total_result_count if search_result else None
        ),
        trends_slope=trends.trends_slope if trends else None,
        reddit_intent_score=(
            reddit.reddit_demand_intent_score if reddit else None
        ),
        cluster_label=(
            cluster_analysis.cluster_label if cluster_analysis else None
        ),
        opportunity_narrative=(
            cluster_analysis.opportunity_narrative if cluster_analysis else None
        ),
    )
```

---

## LLM Cost Estimation

Estimated cost per recommendation (11 LLM tasks):

| Task | Model | Est. Tokens | Est. Cost |
|---|---|---|---|
| Gig titles (5 variants) | gpt-4o | ~800 input + ~400 output | $0.012 |
| Tag sets (5 sets) | gpt-4o-mini | ~600 + ~200 | $0.001 |
| Package structure | gpt-4o | ~1000 + ~600 | $0.018 |
| Description outline | gpt-4o | ~1200 + ~800 | $0.024 |
| FAQ entries (5–7) | gpt-4o-mini | ~500 + ~400 | $0.001 |
| Differentiation angle | gpt-4o | ~1500 + ~400 | $0.020 |
| Buyer persona | gpt-4o-mini | ~400 + ~300 | $0.001 |
| Thumbnail direction | gpt-4o-mini | ~300 + ~200 | $0.001 |
| Upsell structure | gpt-4o-mini | ~400 + ~300 | $0.001 |
| Red flags | gpt-4o | ~1000 + ~400 | $0.015 |
| Niche viability | gpt-4o | ~1200 + ~400 | $0.018 |
| **Total per keyword** | | | **~$0.11** |

With LLM cache hits (estimated 40–60% on repeat runs), effective cost per recommendation: **~$0.05–0.08**.

For a run generating 20 recommendations across 9 niches: **~$1.00–2.20** total.

---

## Storage in Recommendations Table

See Wave 3 `SCHEMA.md` for the complete `Recommendation` model. Key fields:

```python
# Written at end of generate_recommendation():
recommendation = Recommendation(
    keyword_id=keyword_id,
    niche_id=context.niche_id,
    run_id=current_run_id,
    tag=context.tag,
    final_score=context.final_score,
    gig_titles=results["gig_titles"],
    tag_sets=results["tag_sets"],
    package_structure=results["package_structure"],
    description_outline=results["description_outline"],
    faq_entries=results["faq_entries"],
    differentiation_angle=results["differentiation_angle"],
    buyer_persona=results["buyer_persona"],
    thumbnail_direction=results["thumbnail_direction"],
    upsell_structure=results["upsell_structure"],
    red_flags=results["red_flags"],
    niche_viability_assessment=results["niche_viability_assessment"],
    titles_model="gpt-4o",
    packages_model="gpt-4o",
    description_model="gpt-4o",
    differentiation_model="gpt-4o",
    viability_model="gpt-4o",
    llm_cost_usd=results["llm_cost_usd"],
    generation_complete=results["generation_complete"],
    generated_at=datetime.utcnow(),
)
db.merge(recommendation)  # UPSERT — update existing or insert new
db.commit()
```

---

## Run Mode: --mode recommendations-only

```bash
python run.py --mode recommendations-only
```

This re-runs Stage 13 for all eligible keywords using existing scores (Stages 10–12 are not re-run). Useful when:
- User wants to regenerate recommendations after adjusting niche metadata (exclusions, pricing)
- User wants fresh recommendations after competitor data was updated manually
- A previous run's Stage 13 had LLM failures and recommendations were incomplete


---

## SRDI ADDENDUM -- Ghost Market Hard Block and Recommendation Eligibility
**Source:** WAVE_C section 4 (R2); Epic R2 (SCRUM-610)

### Ghost Market Absolute Block (R2.6)

Ghost markets are the most dangerous failure mode: a keyword returns real gigs with
real reviews, but none of them compete in the searched niche. Recommendations from
ghost markets can send sellers into non-existent markets.

In passes_recommendation_gates(keyword, keyword_score, run_id, db):
  FIRST gate (checked before all others):
    rsv = get_result_set_validation(keyword.id, run_id, db)
    if rsv and rsv.ghost_market_flag:
      return False, [{
        "type": "GHOST_MARKET",
        "message": "Ghost market detected: only X% of search results are relevant.
                    No recommendation until keyword is recollected or removed.",
        "resolution_options": [
          "Remove keyword from niche",
          "Update NICHE_VALIDATION_CONFIG core_terms to be more specific",
          "Reclassify niche (current category may be too broad)",
        ]
      }]
      (early exit -- no further gates evaluated)

This block is unconditional: no matter how high the final score, a ghost market
keyword cannot produce a recommendation.

### Ghost Market Resolution Surfacing

Four surfaces where ghost market is communicated to the operator:
  1. Dashboard: RED "GHOST MARKET" badge on keyword card
  2. Score explanation: "Ghost market detected -- recommendation blocked"
  3. Terminal: immediate WARNING during Stage 3.5 with top-5 returned gig titles
  4. Alert row: GHOST_MARKET_DETECTED with HIGH severity (see ALERT_SYSTEM.md)

Ghost detection does NOT delete or modify keyword or scores -- it gates the
recommendation while preserving full data transparency.

Regression: REG-15 test_ghost_market_blocks_recommendation_generation_absolutely
