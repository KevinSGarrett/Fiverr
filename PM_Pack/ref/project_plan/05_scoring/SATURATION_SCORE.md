# Saturation Score
# Fiverr Research System — Wave 6, Score 7

**Status:** Complete | **Range:** 0–100 | **Direction:** Lower = better opportunity (inverted in composite) | **Weight:** 5% (default) | **Depth:** standard, full

---

## What It Measures
How commoditized and undifferentiated the existing gigs are. Higher score = more saturated market with similar offerings competing on price.

This score is calculated by the Wave 5 SATURATION_MODEL and directly stored in `keyword_scores.saturation_score`. This Wave 6 document covers how the Wave 5 output integrates with the broader scoring system.

---

## Data Inputs

This score is **already calculated** in Wave 5 (SATURATION_MODEL.md). The Wave 6 scoring system simply:
1. Reads the calculated saturation_score
2. Validates it is in the 0–100 range
3. Stores it in `keyword_scores.saturation_score`
4. Inverts it in the weighted composite (100 - saturation_score)

The full input chain (from SATURATION_MODEL):

| Component | Source | Weight |
|---|---|---|
| Total gig count vs. niche median | search_results.total_result_count | 25% |
| Title duplication rate (Jaccard) | search_results.gig_cards (top 30 titles) | 25% |
| Price compression | search_results.gig_cards (top 30 prices) | 20% |
| Seller portfolio overlap | search_results across niche keywords | 15% |
| LLM saturation classification | gpt-4o-mini | 15% |

---

## Score Calculation Integration

```python
# src/scoring/saturation_score.py

def calculate_saturation_score(keyword_id: int, db) -> float | None:
    """
    Reads the saturation_score calculated by the Wave 5 saturation model.
    Returns None at keyword_only and feasibility depths (saturation requires
    title duplication and price analysis from gig_cards).
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    if depth in ("keyword_only", "feasibility"):
        return None

    # Direct call to Wave 5 saturation model
    from src.analysis.saturation_model import calculate_saturation_score as wave5_calc
    niche_context = get_niche_context(keyword.niche_id, db)
    return wave5_calc(keyword_id, keyword.niche_id, db, niche_context)
```

The score is stored in `keyword_scores.saturation_score`.

---

## Inversion in Composite

In the Final Score weighted composite:
```python
effective_saturation_contribution = 100.0 - saturation_score
```

- Saturation Score 90 (heavily commoditized) → contributes 10 to composite
- Saturation Score 50 (moderate saturation) → contributes 50 to composite
- Saturation Score 10 (highly differentiated) → contributes 90 to composite

The inversion is handled by `calculate_weighted_composite()` in SCORING_SYSTEM.md.

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| Total result count | DEGRADED | Saturation may still calculate; confidence −0.05 |
| Title duplication | DEGRADED | Required for accurate calculation; confidence −0.10 |
| Price compression | DEGRADED | Required for accurate calculation; confidence −0.05 |
| Seller overlap | OPTIONAL | Can use other components if missing |
| LLM classification | DEGRADED | Falls back to rule-based components only; confidence −0.05 |

If fewer than 2 components are available, returns None.

---

## LLM Input Handling

The saturation model includes one LLM call (gpt-4o-mini) for qualitative classification. If the LLM call failed:
- The 15% weight is redistributed across the rule-based components
- Confidence Modifier reduces by 0.05
- The saturation_narrative field is null in keyword_scores

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Full saturation calculation with all 5 components |
| standard | Full saturation calculation with all 5 components |
| feasibility | **NOT AVAILABLE** — returns None |
| keyword_only | **NOT AVAILABLE** — returns None |

---

## Score Interpretation

| Saturation Score | Label | Strategic Meaning |
|---|---|---|
| 0–25 | HIGHLY_DIFFERENTIATED | Open market with varied offerings — strong opportunity for differentiation |
| 26–50 | MODERATELY_DIFFERENTIATED | Some patterns emerging but room for unique positioning |
| 51–75 | SATURATED | Crowded with similar gigs — need exceptional differentiation |
| 76–100 | COMMODITIZED | Race to the bottom — only compete with strong proof or sub-niche pivot |

---

## Example

**Keyword:** "AI SaaS PRD"

From Wave 5 saturation model:
- Total result count: 1,250 → component score 50 (around niche median)
- Title duplication rate: 0.42 → component score 42
- Price compression: 0.25 → component score 25
- Seller portfolio overlap: 0.18 → component score 18
- LLM classification: "MODERATELY_DIFFERENTIATED" → component score 35

Calculation (from SATURATION_MODEL.md):
```
saturation_score = (50 × 0.25) + (42 × 0.25) + (25 × 0.20) + (18 × 0.15) + (35 × 0.15)
                 = 12.50 + 10.50 + 5.00 + 2.70 + 5.25
                 = 35.95
```

Result: **Saturation Score = 35.95** → "MODERATELY_DIFFERENTIATED" — some patterns emerging but room for differentiation.

In composite: `effective_value = 100 - 35.95 = 64.05`
