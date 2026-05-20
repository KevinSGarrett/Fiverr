# New Seller Feasibility Score
# Fiverr Research System — Wave 6, Score 4

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Weight:** 15% (default), 25% (aggressive_new_seller) | **Depth:** standard, feasibility, full

---

## What It Measures
How feasible it is for a NEW Fiverr seller (zero reviews, no track record) to break into this keyword. Higher score = more achievable entry for someone with no existing platform presence.

This score is critical for the user — they are entering as a new seller in PRD (Slot 1) and other niches, and the aggressive_new_seller profile weights this score at 25%.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| Feasibility contribution (entry difficulty quadrant) | Wave 5 SELLER_STRENGTH_MODEL | feasibility_contribution per top competitor | 40% |
| Cluster entry feasibility rating (LLM synthesis) | competitor_analysis | entry_feasibility_rating | 40% |
| New seller ratio in top 10 | sellers + is_new_seller detection | new_ratio | 20% |

---

## Full Python Formula

```python
def calculate_feasibility_score(keyword_id: int, db) -> float | None:
    """
    Calculates the New Seller Feasibility Score (0–100).
    Returns None if all inputs are missing.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    if depth == "keyword_only":
        return None  # Not available at keyword_only depth

    top_n_map = {"full": 20, "standard": 10, "feasibility": 5}
    top_n = top_n_map.get(depth, 10)

    top_sellers = get_top_n_sellers_for_keyword(keyword_id, top_n, db)
    if not top_sellers:
        return None

    components = {}
    weighted_sum = 0.0
    weight_used = 0.0

    # Component 1: Average Feasibility Contribution from Quadrant Analysis (40%)
    # Each seller has a 0–10 feasibility_contribution from the 4-quadrant entry difficulty
    # (calculated in Wave 5 SELLER_STRENGTH_MODEL)
    feasibility_contributions = [
        s.get("feasibility_contribution")
        for s in top_sellers
        if s.get("feasibility_contribution") is not None
    ]
    if feasibility_contributions:
        avg_feasibility = sum(feasibility_contributions) / len(feasibility_contributions)
        # 0–10 → 0–100
        feasibility_quadrant_score = avg_feasibility * 10.0
        components["quadrant_feasibility"] = {
            "value": feasibility_quadrant_score,
            "weight": 0.40,
            "avg_raw": avg_feasibility,
            "n_competitors": len(feasibility_contributions),
        }
        weighted_sum += feasibility_quadrant_score * 0.40
        weight_used += 0.40

    # Component 2: Cluster Entry Feasibility Rating from LLM Synthesis (40%)
    # gpt-4o produces this in Wave 5 cluster synthesis
    cluster_rating = get_cluster_entry_feasibility_rating(keyword_id, db)
    if cluster_rating is not None:
        # cluster_rating is 0–10, scale to 0–100
        cluster_score = cluster_rating * 10.0
        components["cluster_synthesis"] = {
            "value": cluster_score,
            "weight": 0.40,
            "llm_rating": cluster_rating,
        }
        weighted_sum += cluster_score * 0.40
        weight_used += 0.40

    # Component 3: New Seller Ratio in Top 10 (20%)
    # If new sellers are already winning top spots, the niche is more accessible
    new_count = sum(1 for s in top_sellers if s.get("is_new_seller") is True)
    new_ratio = new_count / max(1, len(top_sellers))
    # 0% new → score 20 (mature niche, no fresh entrants); 30%+ new → score 100
    if new_ratio == 0:
        new_seller_score = 20.0
    elif new_ratio < 0.10:
        new_seller_score = 35.0
    elif new_ratio < 0.20:
        new_seller_score = 55.0
    elif new_ratio < 0.30:
        new_seller_score = 75.0
    else:
        new_seller_score = 100.0
    components["new_seller_ratio"] = {
        "value": new_seller_score,
        "weight": 0.20,
        "new_count": new_count,
        "total_sellers": len(top_sellers),
        "new_ratio": new_ratio,
    }
    weighted_sum += new_seller_score * 0.20
    weight_used += 0.20

    if weight_used < 0.40:
        return None

    feasibility_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, feasibility_score)), 2)
```

---

## Helper: Cluster Feasibility Rating Lookup

```python
def get_cluster_entry_feasibility_rating(keyword_id: int, db) -> float | None:
    """
    Returns the entry_feasibility_rating from the cluster this keyword belongs to.
    Set by gpt-4o in Wave 5 cluster synthesis.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    if not keyword.cluster_id:
        return None

    competitor_analysis = db.query(CompetitorAnalysis).filter(
        CompetitorAnalysis.cluster_id == keyword.cluster_id,
        CompetitorAnalysis.niche_id == keyword.niche_id,
    ).order_by(CompetitorAnalysis.analyzed_at.desc()).first()

    return competitor_analysis.entry_feasibility_rating if competitor_analysis else None
```

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| feasibility_contribution | DEGRADED | Score may still compute; confidence −0.10 |
| Cluster LLM rating | DEGRADED | Score may still compute; confidence −0.10 |
| New seller ratio | OPTIONAL | Defaults to 0% new (assumed mature) |

If both LLM-driven components are missing (Wave 5 didn't produce the data), Feasibility Score may still calculate from new_seller_ratio alone but Confidence Modifier reduces by 0.20.

---

## LLM Input Handling

This score depends on TWO Wave 5 LLM outputs:
1. **Seller authority_score** → used to compute feasibility_contribution (40% of this score)
2. **Cluster entry_feasibility_rating** → directly used (40% of this score)

If either LLM call failed:
- The score uses whatever components are available
- Confidence Modifier deduction applies (per missing data handling above)
- The explanation_text field notes which LLM analysis is missing

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Uses top 20 sellers + cluster synthesis (most accurate) |
| standard | Uses top 10 sellers + cluster synthesis |
| feasibility | Uses top 5 sellers (less reliable due to small sample) |
| keyword_only | **NOT AVAILABLE** — returns None |

---

## Score Interpretation

| Feasibility Score | Meaning |
|---|---|
| 0–20 | Very hard entry — top sellers are entrenched Pro/Top Rated with no weak gigs |
| 21–40 | Hard entry — established sellers dominate; new entry requires exceptional positioning |
| 41–60 | Moderate entry — possible with strong gig assets and clear differentiation |
| 61–80 | Achievable entry — clear gaps exist; new sellers can win with focused execution |
| 81–100 | Very accessible — new sellers are already winning spots in this keyword |

---

## Example Calculation

**Keyword:** "AI SaaS PRD" (continuing from previous examples)

Top 10 sellers analyzed:
- Avg feasibility_contribution: 6.2 → quadrant_score = 62.0
- Cluster entry_feasibility_rating from LLM: 7 → cluster_score = 70.0
- New seller count: 2 of 10 → new_ratio = 0.20 → new_seller_score = 55.0

Calculation:
```
weighted_sum = (62.0 × 0.40) + (70.0 × 0.40) + (55.0 × 0.20)
             = 24.80 + 28.00 + 11.00
             = 63.80
weight_used = 1.0
feasibility_score = 63.80
```

Result: **New Seller Feasibility Score = 63.80** → "Achievable entry" tier.

For the user (Marcus, the aggressive_new_seller persona), this score combined with the high weight in his profile (25%) means this keyword contributes significantly to his Final Recommendation Score — confirming that PRD is appropriate for his entry strategy.

---

## Cross-Score Interaction

Feasibility Score is **highly correlated** with the inverted Competition Score, but they measure different things:
- **Competition Score** measures *how strong* the existing field is
- **Feasibility Score** measures *whether a new seller can win* — accounting for gig weaknesses, fresh sellers already winning, and cluster-level qualitative judgment

A keyword can have:
- High Competition Score (strong field) + High Feasibility Score = strong field but exploitable weaknesses (good for skilled new entrants)
- Low Competition Score (weak field) + Low Feasibility Score = unusual — possibly indicates low demand or niche oddities making entry hard
- High Competition Score + Low Feasibility Score = avoid (strong field with no gaps)
- Low Competition Score + High Feasibility Score = ideal (weak field that's also welcoming to new sellers)
