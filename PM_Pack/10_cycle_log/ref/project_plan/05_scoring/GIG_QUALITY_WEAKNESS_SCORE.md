# Gig Quality Weakness Score
# Fiverr Research System — Wave 6, Score 8

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better (more weakness to exploit) | **Weight:** 10% (default), 20% (aggressive_new_seller) | **Depth:** standard, full

---

## What It Measures
How beatable the existing top competitor gigs are. This score aggregates the per-gig `overall_weakness_score` from Wave 5 (GIG_QUALITY_RUBRIC) across the top N gigs for the keyword.

**Higher score = competitors have more exploitable weaknesses = stronger opportunity for a well-crafted new gig.**

This is the inverted complement to Competition Score. Where Competition measures *strength*, this measures *vulnerability*.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| Average overall_weakness_score across top N gigs | gig_quality_scores | overall_weakness_score | 70% |
| Red flag review boost | gig_quality_scores via review analysis | weakness_list red flag count | 20% |
| Distribution skew (how many gigs are highly exploitable) | gig_quality_scores | overall_weakness_score distribution | 10% |

---

## Full Python Formula

```python
import statistics

def calculate_gig_quality_weakness_score(keyword_id: int, db) -> float | None:
    """
    Calculates the Gig Quality Weakness Score (0–100).
    Higher = competitors are weaker = more opportunity.
    Returns None at keyword_only and feasibility depths.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    if depth in ("keyword_only", "feasibility"):
        return None

    top_n_map = {"full": 10, "standard": 5}
    top_n = top_n_map.get(depth, 10)

    # Get gig_quality_scores for top N gigs of this keyword
    gig_quality_records = get_gig_quality_scores_for_keyword(keyword_id, top_n, db)
    if not gig_quality_records:
        return None

    weakness_scores = [
        gq.overall_weakness_score for gq in gig_quality_records
        if gq.overall_weakness_score is not None
    ]
    if not weakness_scores:
        return None

    components = {}
    weighted_sum = 0.0
    weight_used = 0.0

    # Component 1: Average Overall Weakness Score (70%)
    # overall_weakness_score is 0–10 from Wave 5, scale to 0–100
    avg_weakness = statistics.mean(weakness_scores)
    avg_score = avg_weakness * 10.0
    components["avg_weakness"] = {
        "value": avg_score,
        "weight": 0.70,
        "raw_avg": round(avg_weakness, 2),
        "n_gigs": len(weakness_scores),
    }
    weighted_sum += avg_score * 0.70
    weight_used += 0.70

    # Component 2: Red Flag Review Boost (20%)
    # Total red flags across the analyzed gigs
    total_red_flags = 0
    for gq in gig_quality_records:
        if gq.weakness_list:
            try:
                import json
                weakness_data = (
                    json.loads(gq.weakness_list)
                    if isinstance(gq.weakness_list, str)
                    else gq.weakness_list
                )
                if isinstance(weakness_data, list):
                    total_red_flags += sum(
                        1 for w in weakness_data
                        if w.get("severity") == "HIGH"
                    )
            except (json.JSONDecodeError, AttributeError):
                pass

    # 0 red flags → 30 (baseline); 5+ red flags → 100
    if total_red_flags == 0:
        red_flag_score = 30.0
    elif total_red_flags <= 2:
        red_flag_score = 50.0
    elif total_red_flags <= 4:
        red_flag_score = 75.0
    else:
        red_flag_score = 100.0
    components["red_flag_boost"] = {
        "value": red_flag_score,
        "weight": 0.20,
        "total_red_flags": total_red_flags,
    }
    weighted_sum += red_flag_score * 0.20
    weight_used += 0.20

    # Component 3: Distribution Skew (10%)
    # If 3+ gigs in top N are highly exploitable (overall_weakness_score >= 7.0),
    # the opportunity is concentrated in beatable competitors
    highly_exploitable = sum(1 for w in weakness_scores if w >= 7.0)
    exploitable_ratio = highly_exploitable / len(weakness_scores)
    # 0% highly exploitable → 30; 50%+ → 100
    if exploitable_ratio == 0:
        distribution_score = 30.0
    elif exploitable_ratio < 0.20:
        distribution_score = 50.0
    elif exploitable_ratio < 0.40:
        distribution_score = 75.0
    else:
        distribution_score = 100.0
    components["distribution"] = {
        "value": distribution_score,
        "weight": 0.10,
        "highly_exploitable_count": highly_exploitable,
        "ratio": round(exploitable_ratio, 2),
    }
    weighted_sum += distribution_score * 0.10
    weight_used += 0.10

    weakness_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, weakness_score)), 2)
```

---

## LLM Input Handling

The `overall_weakness_score` from Wave 5 is **fully LLM-driven** (gpt-4o on description quality and weakness detection, gpt-4o-mini on title/thumbnail/FAQ). If LLM analysis failed for some gigs:
- The score uses whatever gigs have valid `overall_weakness_score`
- If fewer than 3 gigs have valid scores, returns None
- Confidence Modifier reduces by 0.10 per missing gig analysis

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| Average weakness score | REQUIRED | Returns None if no LLM analysis available |
| Red flag count | OPTIONAL | Defaults to 30 (baseline) |
| Distribution | OPTIONAL | Defaults to 30 (baseline) |

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Uses top 10 gigs with full gpt-4o description quality + weakness analysis |
| standard | Uses top 5 gigs with full gpt-4o analysis |
| feasibility | **NOT AVAILABLE** — returns None (only gpt-4o-mini analysis runs at feasibility, not the weakness detection) |
| keyword_only | **NOT AVAILABLE** — returns None |

---

## Score Interpretation

| Weakness Score | Meaning |
|---|---|
| 0–20 | Strong competitor gigs — minimal exploitable weaknesses |
| 21–40 | Decent gigs with some weaknesses — moderate opportunity |
| 41–60 | Mixed quality — some weak gigs, some strong |
| 61–80 | Many exploitable weaknesses — strong opportunity for differentiation |
| 81–100 | Highly exploitable field — top gigs have significant gaps a new seller can attack |

---

## Example Calculation

**Keyword:** "AI SaaS PRD" (full depth, top 10 gigs analyzed)

From Wave 5 analysis:
- overall_weakness_scores across 10 gigs: [7.2, 6.8, 8.1, 5.4, 6.9, 4.3, 7.5, 8.8, 5.2, 6.1]
- Average: 6.63 → avg_score = 66.3
- Total red flags across these gigs: 4 → red_flag_score = 75.0
- Highly exploitable (≥7.0): 4 of 10 → exploitable_ratio = 0.40 → distribution_score = 75.0

Calculation:
```
weighted_sum = (66.3 × 0.70) + (75.0 × 0.20) + (75.0 × 0.10)
             = 46.41 + 15.00 + 7.50
             = 68.91
weakness_score = 68.91
```

Result: **Gig Quality Weakness Score = 68.91** → "Many exploitable weaknesses" tier.

For the aggressive_new_seller profile (20% weight), this score significantly boosts the keyword's Final Recommendation Score — indicating that despite strong competition (Competition Score 65.55), the existing gigs have enough weaknesses for a well-crafted new gig to win buyers.

---

## How This Score Feeds the Recommendation Engine

The Gig Quality Weakness Score is one of the most actionable scores because it directly informs the **differentiation_angle** generated in Stage 13 (Recommendations):

When this score is high (>60), the recommendation engine receives the specific weakness_list from Wave 5 as input to gpt-4o, which generates a differentiation angle like:

> "Top 10 gigs in this niche have generic descriptions with no proof elements and weak FAQ sections. Position as the specialist with a verifiable process: include a 3-bullet proof block (X clients delivered, Y industry experience, Z deliverables shipped), a 7-question FAQ addressing common buyer concerns, and a video walkthrough demonstrating the actual deliverable."

This is the bridge from analysis → actionable gig assets.
