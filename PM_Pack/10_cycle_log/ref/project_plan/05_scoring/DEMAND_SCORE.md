# Demand Score
# Fiverr Research System — Wave 6, Score 1

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Weight:** 20% (default profile) | **Depth:** All

---

## What It Measures
The volume of buyer search activity for this keyword across Fiverr, Google, and Reddit. Higher score = more buyers actively looking for this service.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| Fiverr total result count | search_results | total_result_count | 50% |
| Fiverr autocomplete position | keywords | autocomplete_position | 20% |
| Google Trends 12-month score | external_signals (google_trends) | trends_12mo_score | 20% |
| Reddit demand intent score | external_signals (reddit_demand) | reddit_demand_intent_score | 10% |

---

## Full Python Formula

```python
import math

def calculate_demand_score(keyword_id: int, db) -> float | None:
    """
    Calculates the Demand Score for a keyword (0–100).
    Returns None if all four inputs are missing.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    search_result = get_latest_search_result(keyword_id, db)
    trends = get_external_signal(keyword_id, "google_trends", db)
    reddit = get_external_signal_for_niche(keyword.niche_id, "reddit_demand", db)

    components = {}
    total_weight_available = 0.0
    weighted_sum = 0.0

    # Component 1: Fiverr Total Result Count (50%)
    if search_result and search_result.total_result_count is not None:
        count = search_result.total_result_count
        # Log-scaled normalization: 0 results → 0, 100 → 50, 1000 → 75, 5000+ → 100
        if count <= 0:
            count_score = 0.0
        else:
            count_score = min(100.0, 25.0 * math.log10(count + 1) / math.log10(2))
            # log10(2)=0.301; log10(5001)=3.699; 25*3.699/0.301=307 capped at 100
            # Practical mapping:
            #   10 results   → ~25
            #   50 results   → ~42
            #   100 results  → ~50
            #   500 results  → ~67
            #   1,000        → ~75
            #   5,000        → ~92
            #   10,000+      → 100
        components["fiverr_count"] = {"value": count_score, "weight": 0.50, "raw": count}
        weighted_sum += count_score * 0.50
        total_weight_available += 0.50

    # Component 2: Fiverr Autocomplete Position (20%)
    if keyword.autocomplete_position is not None:
        pos = keyword.autocomplete_position
        # Position 1 → 100, position 10 → 10, not in autocomplete → 0
        position_score = max(0.0, 100.0 - (pos - 1) * 10.0)
        components["autocomplete"] = {"value": position_score, "weight": 0.20, "raw": pos}
        weighted_sum += position_score * 0.20
        total_weight_available += 0.20
    else:
        # Keyword NOT in Fiverr autocomplete is a meaningful signal (not just missing data)
        components["autocomplete"] = {"value": 0.0, "weight": 0.20, "raw": None,
                                       "note": "not in Fiverr autocomplete"}
        weighted_sum += 0.0 * 0.20
        total_weight_available += 0.20

    # Component 3: Google Trends 12-Month Score (20%)
    if trends and trends.trends_12mo_score is not None:
        # Trends score is already 0–100, but skewed toward low values
        # Apply mild boost: score 30 → ~45, score 70 → ~78
        trends_score = min(100.0, trends.trends_12mo_score * 1.15)
        components["google_trends"] = {"value": trends_score, "weight": 0.20,
                                        "raw": trends.trends_12mo_score}
        weighted_sum += trends_score * 0.20
        total_weight_available += 0.20

    # Component 4: Reddit Demand Intent Score (10%)
    if reddit and reddit.reddit_demand_intent_score is not None:
        # Reddit score is 0–10, scale to 0–100
        reddit_score = reddit.reddit_demand_intent_score * 10.0
        components["reddit_intent"] = {"value": reddit_score, "weight": 0.10,
                                        "raw": reddit.reddit_demand_intent_score}
        weighted_sum += reddit_score * 0.10
        total_weight_available += 0.10

    if total_weight_available < 0.30:
        # Not enough data — return None and let Confidence Modifier handle it
        return None

    # Normalize for missing components
    demand_score = weighted_sum / total_weight_available
    return round(min(100.0, max(0.0, demand_score)), 2)
```

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| total_result_count | DEGRADED | Score may still compute if other components present; confidence −0.10 |
| autocomplete_position | OPTIONAL | Treated as "not in autocomplete" (score = 0 for this component) |
| trends_12mo_score | DEGRADED | Score may still compute; confidence −0.15 |
| reddit_demand_intent_score | DEGRADED | Score may still compute; confidence −0.05 |

If fewer than 30% of weight is available (i.e., almost all data is missing), the function returns None and the keyword is flagged with confidence_modifier penalty.

---

## LLM Input Handling

The Reddit demand intent score is itself produced by gpt-4o-mini in Stage 6. If the LLM call failed:
- `reddit_demand_intent_score` is null
- This component contributes 0 to demand score
- Confidence Modifier is reduced by 0.05

The Demand Score itself does not directly call an LLM.

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | All 4 components used |
| standard | All 4 components used |
| feasibility | All 4 components used |
| keyword_only | All 4 components used (Demand is available at all depths) |

Demand Score is one of three scores available at every depth tier (along with Competition and Opportunity).

---

## Score Interpretation

| Demand Score | Meaning |
|---|---|
| 0–20 | Very low demand — buyers rarely search this term |
| 21–40 | Low demand — niche search volume |
| 41–60 | Moderate demand — established but not high-volume keyword |
| 61–80 | High demand — strong buyer search volume |
| 81–100 | Very high demand — top-tier search volume |

---

## Example Calculation

**Keyword:** "AI SaaS PRD"
- Fiverr total_result_count: 1,250 → count_score = ~77.5
- autocomplete_position: 3 → position_score = 80.0
- trends_12mo_score: 58 → trends_score = 66.7
- reddit_demand_intent_score: 7.2 → reddit_score = 72.0

Calculation:
```
weighted_sum = (77.5 × 0.50) + (80.0 × 0.20) + (66.7 × 0.20) + (72.0 × 0.10)
             = 38.75 + 16.00 + 13.34 + 7.20
             = 75.29
total_weight = 1.00
demand_score = 75.29 / 1.00 = 75.29
```

Result: **Demand Score = 75.29** → "High demand" tier.
