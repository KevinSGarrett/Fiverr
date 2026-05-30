# Competition Score
# Fiverr Research System — Wave 6, Score 2

**Status:** Complete | **Range:** 0–100 | **Direction:** Lower = better opportunity (inverted in composite) | **Weight:** 20% (default) | **Depth:** All

---

## What It Measures
The strength of the existing competitive field — how strong, established, and entrenched the top competitors are. Higher score = stronger competition = harder for a new seller to enter.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| Average competitor strength (top N sellers) | seller_scores | authority_score, competitor_strength | 60% |
| Average seller level index (top N sellers) | sellers | seller_level | 25% |
| New seller ratio in top 10 | sellers + Wave 5 detection | is_new_seller | 15% (inverted) |

---

## Full Python Formula

```python
LEVEL_INDEX = {
    "No Level":   1,
    "Level 1":    3,
    "Level 2":    6,
    "Top Rated":  9,
    "Pro":       10,
}

def calculate_competition_score(keyword_id: int, db) -> float | None:
    """
    Calculates the Competition Score for a keyword (0–100).
    Higher = stronger competition. This score is INVERTED in the composite
    (100 - competition_score) so that high competition reduces the weighted composite.
    Returns None if no competitor data is available.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    # Determine top-N based on depth
    top_n_map = {"full": 20, "standard": 10, "feasibility": 5, "keyword_only": 10}
    top_n = top_n_map.get(depth, 10)

    # For keyword_only depth, use search_results gig_cards directly (no detailed seller data)
    if depth == "keyword_only":
        return _calculate_competition_from_search_only(keyword_id, db, top_n)

    # For standard/full/feasibility — use full seller and gig data
    top_sellers = get_top_n_sellers_for_keyword(keyword_id, top_n, db)
    if not top_sellers:
        return None

    components = {}

    # Component 1: Average Competitor Strength (60%)
    strength_scores = []
    for seller_data in top_sellers:
        if seller_data.get("authority_score") is not None:
            strength_scores.append(seller_data["authority_score"])
    if strength_scores:
        avg_strength = sum(strength_scores) / len(strength_scores)
        # authority_score is 0–10, scale to 0–100
        strength_component = avg_strength * 10.0
        components["avg_strength"] = {"value": strength_component, "weight": 0.60,
                                       "n_sellers": len(strength_scores)}
    else:
        strength_component = None

    # Component 2: Average Seller Level Index (25%)
    level_values = []
    for seller_data in top_sellers:
        level = seller_data.get("seller_level") or "No Level"
        level_values.append(LEVEL_INDEX.get(level, 1))
    if level_values:
        avg_level = sum(level_values) / len(level_values)
        # avg_level is 1–10, scale to 0–100 (level 1 → 10, level 10 → 100)
        level_component = avg_level * 10.0
        components["avg_level"] = {"value": level_component, "weight": 0.25,
                                    "avg_level_index": avg_level}
    else:
        level_component = None

    # Component 3: New Seller Ratio (15%) — INVERTED
    # More new sellers = weaker competition = lower competition score
    new_seller_count = sum(1 for s in top_sellers if s.get("is_new_seller") is True)
    new_ratio = new_seller_count / max(1, len(top_sellers))
    # 0% new sellers → score 100 (no openings); 50% new → score 50; 100% new → score 0
    new_seller_component = (1.0 - new_ratio) * 100.0
    components["new_seller_ratio"] = {"value": new_seller_component, "weight": 0.15,
                                       "new_ratio": new_ratio}

    # Composite (only including components that exist)
    weighted_sum = 0.0
    weight_used = 0.0
    if strength_component is not None:
        weighted_sum += strength_component * 0.60
        weight_used += 0.60
    if level_component is not None:
        weighted_sum += level_component * 0.25
        weight_used += 0.25
    if new_seller_component is not None:
        weighted_sum += new_seller_component * 0.15
        weight_used += 0.15

    if weight_used < 0.30:
        return None

    competition_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, competition_score)), 2)


def _calculate_competition_from_search_only(keyword_id: int, db, top_n: int) -> float | None:
    """
    Fallback Competition Score calculation when no gig detail or seller data
    is available (keyword_only depth).
    Uses seller_level and review_count visible in search result cards.
    """
    search_result = get_latest_search_result(keyword_id, db)
    if not search_result or not search_result.gig_cards:
        return None

    cards = search_result.gig_cards[:top_n]

    # Use seller_level from cards
    level_values = []
    review_values = []
    for card in cards:
        level = card.get("seller_level") or "No Level"
        level_values.append(LEVEL_INDEX.get(level, 1))
        if card.get("review_count_visible") is not None:
            review_values.append(card["review_count_visible"])

    if not level_values:
        return None

    # Component A: Avg seller level (60%)
    avg_level = sum(level_values) / len(level_values)
    level_score = avg_level * 10.0

    # Component B: Avg review count (40%) — log scale
    if review_values:
        import math
        avg_reviews = sum(review_values) / len(review_values)
        review_score = min(100.0, 25.0 * math.log10(max(1, avg_reviews) + 1) / math.log10(2))
        weighted_sum = level_score * 0.60 + review_score * 0.40
        weight_used = 1.0
    else:
        weighted_sum = level_score
        weight_used = 0.60

    competition_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, competition_score)), 2)
```

---

## Inversion in Composite

In the Final Score weighted composite, the Competition Score is **inverted**:
```python
effective_competition_contribution = 100.0 - competition_score
```

So:
- Competition Score 90 (strong competition) → contributes 10 to composite
- Competition Score 50 (moderate competition) → contributes 50 to composite
- Competition Score 20 (weak competition) → contributes 80 to composite

This inversion is handled in `calculate_weighted_composite()` in SCORING_SYSTEM.md — the score itself is stored as raw "competition strength."

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| Competitor strength | DEGRADED | Score may still compute; confidence −0.10 |
| Seller level | DEGRADED | Score may still compute; confidence −0.05 |
| New seller flags | OPTIONAL | Treated as 0% new (assumed established competition) |

If no competitor data at all is available, returns None — the keyword has no Competition Score and Confidence Modifier penalty applies.

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Uses top 20 sellers' authority_score + level + new seller detection |
| standard | Uses top 10 sellers' authority_score + level + new seller detection |
| feasibility | Uses top 5 sellers' authority_score + level + new seller detection |
| keyword_only | Falls back to search card data only (no detailed seller analysis) — uses seller_level and review_count_visible from gig_cards JSON |

---

## Score Interpretation

| Competition Score | Meaning |
|---|---|
| 0–20 | Very weak competition — open field |
| 21–40 | Weak competition — many new or low-level sellers in top results |
| 41–60 | Moderate competition — established sellers but no dominant force |
| 61–80 | Strong competition — Level 2+ sellers, high review counts |
| 81–100 | Dominant competition — Top Rated / Pro sellers with thousands of reviews |

---

## Example Calculation

**Keyword:** "AI SaaS PRD" — full depth, 20 sellers analyzed.
- Average authority_score: 6.8 → strength_component = 68.0
- Seller levels: mix of Level 2 (8), Top Rated (5), Level 1 (4), No Level (3)
  - Avg level index: (8×6 + 5×9 + 4×3 + 3×1) / 20 = (48+45+12+3)/20 = 5.4
  - level_component = 54.0
- New sellers in top 20: 5 → new_ratio = 0.25 → new_seller_component = 75.0

Calculation:
```
weighted_sum = (68.0 × 0.60) + (54.0 × 0.25) + (75.0 × 0.15)
             = 40.80 + 13.50 + 11.25
             = 65.55
competition_score = 65.55
```

Result: **Competition Score = 65.55** → "Strong competition" tier.

In composite: `effective_value = 100 - 65.55 = 34.45`


---

## SRDI ADDENDUM -- Competition Score Integrity Extensions
**Source:** WAVE_E section 2 (R4); Epic R4 (SCRUM-613-619, SCRUM-813)

### Clean Gig Set for All Competition Metrics

All competition calculations now use a clean gig set excluding sponsored, zombie,
and irrelevant gigs. TOP_N_FOR_SCORING = 10.

clean_gigs = [g for g in top_gigs[:20]
              if g.is_sponsored is not True   (NULL = organic = include)
              and g.is_zombie is not True      (NULL = non-zombie = include)
              and g.relevance_flag is not False (NULL = include)][:10]

Fallback: if len(clean_gigs) < 3, use full top_gigs[:10] + WARNING log.
"insufficient_clean_gigs: fewer than 3 gigs pass organic/non-zombie/relevant filters"

### Per-Keyword vs. Per-Niche Profile Selection (R4.3)

Profile type selected based on RSV relevance:
  RSV >= 0.80: use niche-level aggregate profile (high quality result set)
  RSV 0.60-0.80: use per-keyword profile
  RSV < 0.60: use per-keyword profile with contamination outlier exclusion (R4.4)

### Niche Profile Contamination Outlier Exclusion (R4.4)

When building niche aggregate profile, keywords with RSV < 0.40 are excluded:
  for each keyword in niche: if rsv.result_set_relevance_score < 0.40: skip
  If ALL keywords excluded: fallback to full set + WARNING "all_keywords_contaminated_fallback"

This prevents ghost-market and contaminated keywords from distorting the niche picture.
Exclusion count logged: "Niche profile [niche]: N kws included / M excluded"

### Price Outlier Exclusion (R4.5, IQR Method)

Applied in competition.py price signal AND profitability.py before any price calculation.

_filter_price_outliers(prices):
  Requires >= 4 prices to apply filter (else returns unchanged)
  Q1, Q3 = 25th and 75th percentile
  IQR = Q3 - Q1
  upper = Q3 + 2.5 * IQR
  filtered = [p for p in prices if p <= upper]
  Returns filtered if non-empty, else original list (never returns empty)

Effect: cross-category contaminated gigs with inflated premium prices (e.g. a $5000
logo design in an automation niche) are excluded from competition price signal.
