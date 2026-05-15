# Final Recommendation Score
# Fiverr Research System — Wave 6, Score 10

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Type:** Composite | **Depth:** All

---

## What It Measures
The single overall opportunity score for a keyword — the weighted composite of all available individual scores, multiplied by the Confidence Modifier. This is the score the dashboard sorts by and the score that determines GO/PASS tags.

---

## Calculation Flow

```
[Individual Scores 1–9]
    │
    ▼
[Profile Weights from config.yaml]
    │
    ▼
[Weighted Composite] (handles missing scores via weight redistribution)
    │
    ▼
[× Confidence Modifier] (floored at 0.20)
    │
    ▼
[Final Score 0–100]
    │
    ▼
[GO/PASS Tag Assignment] (with confidence-based demotion)
    │
    ▼
[Final ranked output]
```

---

## Full Python Formula

```python
# Already detailed in SCORING_SYSTEM.md — repeated here as the canonical reference

def calculate_final_score_complete(
    keyword_id: int,
    profile_name: str,
    db,
    llm_client,
    cache,
) -> dict:
    """
    Complete Final Score calculation pipeline.
    Returns a full result dict with all intermediate values, ready to write
    to keyword_scores table.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth
    available = DEPTH_SCORE_AVAILABILITY[depth]["available_scores"]

    # Step 1: Calculate individual scores
    scores = {
        "demand_score":        calculate_demand_score(keyword_id, db)        if 1 in available else None,
        "competition_score":   calculate_competition_score(keyword_id, db)   if 2 in available else None,
        "opportunity_score":   None,  # Computed after demand + competition
        "feasibility_score":   calculate_feasibility_score(keyword_id, db)   if 4 in available else None,
        "profitability_score": calculate_profitability_score(keyword_id, db) if 5 in available else None,
        "intent_score":        calculate_conversion_intent_score(keyword_id, db) if 6 in available else None,
        "saturation_score":    calculate_saturation_score(keyword_id, db)    if 7 in available else None,
        "weakness_score":      calculate_gig_quality_weakness_score(keyword_id, db) if 8 in available else None,
        "trend_score":         calculate_trend_score(keyword_id, db)         if 9 in available else None,
    }

    # Step 2: Compute Opportunity Score from Demand + Competition
    if scores["demand_score"] is not None and scores["competition_score"] is not None:
        scores["opportunity_score"] = calculate_opportunity_score(
            scores["demand_score"], scores["competition_score"]
        )

    # Step 3: Get profile weights
    profile_weights = SCORING_PROFILES[profile_name]
    validate_scoring_profile(profile_name, profile_weights)

    # Step 4: Calculate weighted composite
    weighted_composite, score_components = calculate_weighted_composite(scores, profile_weights)

    # Step 5: Calculate Confidence Modifier
    confidence_modifier, confidence_breakdown = calculate_confidence_modifier(
        keyword_id, scores, db
    )

    # Step 6: Calculate Final Score (with confidence floor)
    final_score = calculate_final_score(weighted_composite, confidence_modifier, confidence_floor=0.20)

    # Step 7: Assign GO/PASS tag (with confidence-based demotion)
    tag = assign_tag(final_score, confidence_modifier)

    # Step 8: Calculate rank within niche
    rank_within_niche = calculate_rank_within_niche(keyword_id, final_score, db)

    return {
        "keyword_id": keyword_id,
        "niche_id": keyword.niche_id,
        "scoring_profile": profile_name,
        "score_depth": DEPTH_SCORE_AVAILABILITY[depth]["label"],
        "scores": scores,
        "weighted_composite": weighted_composite,
        "confidence_modifier": confidence_modifier,
        "final_score": final_score,
        "tag": tag,
        "rank_within_niche": rank_within_niche,
        "score_components": score_components,
        "confidence_breakdown": confidence_breakdown,
    }
```

---

## GO/PASS Tag Thresholds

```python
OPPORTUNITY_TAGS = [
    ("STRONG GO",      80, 100),
    ("CONDITIONAL GO", 60,  80),
    ("MONITOR",        40,  60),
    ("CAUTION",        20,  40),
    ("PASS",            0,  20),
]
```

These thresholds are configurable in `config.yaml`:
```yaml
opportunity_thresholds:
  strong_go: 80
  conditional_go: 60
  monitor: 40
  caution: 20
```

Changing thresholds triggers tag reassignment on the next score-only run.

---

## Confidence-Based Tag Demotion

When `confidence_modifier < 0.5`:
- STRONG GO → CONDITIONAL GO
- CONDITIONAL GO → MONITOR
- MONITOR → CAUTION
- CAUTION → PASS

This protects the user from acting on high scores built on thin or unreliable data.

---

## Example: Full Calculation for "AI SaaS PRD"

Continuing all previous score examples for the same keyword:

**Individual scores:**
- demand_score: 75.29
- competition_score: 65.55
- opportunity_score: 25.94 (derived from demand and competition)
- feasibility_score: 63.80
- profitability_score: 80.03
- intent_score: 77.60
- saturation_score: 35.95
- weakness_score: 68.91
- trend_score: 70.20

**Using `aggressive_new_seller` profile weights:**
```
feasibility:     0.25
weakness:        0.20
opportunity:     0.20
demand:          0.15
competition_inv: 0.10
profitability:   0.05
intent:          0.05
saturation_inv:  0.00
trend:           0.00
```

**Weighted composite calculation:**
```
feasibility:     63.80 × 0.25 = 15.95
weakness:        68.91 × 0.20 = 13.78
opportunity:     25.94 × 0.20 =  5.19
demand:          75.29 × 0.15 = 11.29
competition_inv: (100 - 65.55) × 0.10 = 3.45
profitability:   80.03 × 0.05 =  4.00
intent:          77.60 × 0.05 =  3.88
saturation_inv:  excluded (weight 0)
trend:           excluded (weight 0)

weighted_sum = 15.95 + 13.78 + 5.19 + 11.29 + 3.45 + 4.00 + 3.88 = 57.54
total_weight_used = 0.25 + 0.20 + 0.20 + 0.15 + 0.10 + 0.05 + 0.05 = 1.00
weighted_composite = 57.54 / 1.00 = 57.54
```

**Confidence Modifier:** 0.913 (from CONFIDENCE_SCORE.md example)

**Final Score:**
```
effective_modifier = max(0.913, 0.20) = 0.913
final_score = 57.54 × 0.913 = 52.53
```

**Tag assignment:**
- 52.53 falls in 40–60 range → base_tag = "MONITOR"
- confidence_modifier 0.913 > 0.5 → no demotion
- final tag = **"MONITOR"**

Result for "AI SaaS PRD" with aggressive_new_seller profile:
- **Final Recommendation Score: 52.53**
- **Tag: MONITOR**
- **Insight:** Despite high demand (75) and exploitable weaknesses (69), the strong competition (65) and weak Opportunity Score (26) keep this in MONITOR range. This is a niche to watch and prepare for, not necessarily to immediately enter without exceptional proof.

---

## Profile Comparison for Same Keyword

Same keyword "AI SaaS PRD" scored with different profiles:

| Profile | Weighted Composite | Final Score | Tag |
|---|---|---|---|
| default | 60.18 | 54.94 | MONITOR |
| aggressive_new_seller | 57.54 | 52.53 | MONITOR |
| profitability_focus | 56.93 | 51.98 | MONITOR |
| trend_chaser | 58.81 | 53.69 | MONITOR |

All profiles agree this keyword is in MONITOR range — different profiles weight the underlying signals differently but reach similar conclusions for this keyword. The variance helps identify which keywords are robustly STRONG GO across profiles (real opportunities) vs. profile-sensitive (depends on strategic lens).

---

## How Scores Map to Decisions

The Final Score + Tag combination drives downstream actions:

| Tag | Score Range | What the System Does |
|---|---|---|
| STRONG GO | 80–100 | Generates full recommendation package in Stage 13 (titles, packages, FAQ, etc.) |
| CONDITIONAL GO | 60–80 | Generates recommendation package, flags conditions to address |
| MONITOR | 40–60 | No recommendation generated; surfaces in dashboard for ongoing observation |
| CAUTION | 20–40 | No recommendation; appears in dashboard with low-priority badge |
| PASS | 0–20 | No recommendation; deprioritized in dashboard display |

---

## Score Storage in keyword_scores Table

After calculation, the Final Score record is written to `keyword_scores` with:
- All 9 individual scores (null where unavailable)
- weighted_composite
- confidence_modifier
- final_score
- tag
- score_components (full JSON breakdown)
- confidence_breakdown (full JSON)
- explanation_text (gpt-4o LLM-generated, see Stage 14)
- red_flags (JSON array)
- missing_data_warnings (JSON array)
- scoring_profile (which profile was active)
- score_depth (all_11 / scores_1_to_5 / scores_1_to_3)
- scored_at (timestamp)
- data_as_of (timestamp of oldest contributing record)

---

## Rank Within Niche

After all keyword scores are calculated for a niche, ranks are assigned:

```python
def calculate_rank_within_niche(niche_id: str, db) -> None:
    """
    Updates rank field in opportunity_rankings table for all keywords
    in this niche. Rank 1 = highest final_score in niche.
    """
    keywords_in_niche = db.query(OpportunityRanking).filter(
        OpportunityRanking.niche_id == niche_id,
        OpportunityRanking.run_id == get_current_run_id(),
    ).order_by(OpportunityRanking.final_score.desc()).all()

    for rank, ranking in enumerate(keywords_in_niche, start=1):
        ranking.rank = rank
    db.commit()
```

A global rank (across all niches) is also calculated for the dashboard's cross-niche opportunity view.
