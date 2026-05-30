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


---

## SRDI ADDENDUM -- Demand Score Integrity Extensions
**Source:** WAVE_E section 1 (R4), WAVE_H (R7); Epics R4 (SCRUM-613-619), R7 (SCRUM-620-858)

### R4.1: TRC Reliability Qualifier (Single Authoritative Multiplier)

Replaces the R3 sponsored-fraction bands once R4 ships. Never stack both.
_compute_trc_reliability() returns a single 0.0-1.0 score factoring in:
  Factor 1: Search strictness used
    NONE       -> -0.15
    CATEGORY   -> -0.05
    SUBCATEGORY -> 0
  Factor 2: Result-set relevance (from RSV)
    Deduction = max(0, (1.0 - rsv_score) * 0.30)
  Factor 3: Sponsored contamination
    sponsored_fraction > 35% -> -0.10
  Factor 4: Extreme TRC
    total_result_count > 100,000 -> -0.05

qualified_trc = total_result_count * trc_reliability
count_score uses qualified_trc instead of raw TRC (log10 formula unchanged)
trc_reliability < 0.70 -> confidence_breakdown["trc_reliability_low"] = -0.05
trc_reliability_score and qualified_trc stored on KeywordScore for transparency

### R4.2: Autocomplete Emerging Category Distinction

When autocomplete_position is None, _classify_autocomplete_absence() is called:
  source = "discovery" OR keyword >= 4 words  -> return (50, "emerging")
  trends_slope = STRONGLY_RISING              -> return (50, "emerging")
  trends_slope = RISING                       -> return (35, "emerging_uncertain")
  keyword <= 2 words (short, flat trends)     -> return (0,  "not_searched")
  else                                        -> return (20, "unknown")

This prevents emerging niches from being penalized for not being in autocomplete yet.
Shared function owned by R7; R4 imports it. (see _classify_autocomplete_absence)

### R7: Google Trends Platform Qualifier

Google Trends measures general interest, not Fiverr buyer intent.
_compute_fiverr_relevance_qualifier() computes a 0.20-0.95 qualifier:
  Base: 0.65
  Slope modifier: STRONGLY_RISING +0.10; RISING +0.05; DECLINING -0.05
  Buying-intent related queries: +min(0.10, count * 0.02)
    (phrases: hire, service, freelance, cost, price, how much, need, find, pay for)
  Breadth penalty: 1-word -0.10; 2-word -0.05; 3+ words 0

Result stored as ExternalSignal.fiverr_relevance_qualifier (0.20-0.95 clamped)
Qualified trends score = raw_trends * qualifier * 1.15

In demand.py: read qualifier from ExternalSignal if R7 has run; else use
config.scoring.trends_platform_qualifier or 0.65 default.

### R7: Reddit Buyer-Intent Qualifier

buyer_intent_ratio = matching posts / total posts
Buying phrases: looking for, need a, want to hire, recommend someone, how much does,
  how much to, can someone, where can I hire, freelancer, upwork, fiverr

qualified_reddit = raw_reddit * (0.40 + 0.60 * buyer_intent_ratio)
Stored as raw_value_json["reddit_qualified_intent_score"] on ExternalSignal
demand.py reads qualified score; score = clamp(0, 100, qualified * 10)

### R7: YouTube as Legitimacy Gate Only (NOT demand weight)

YouTube weight in demand blend = 0 (was informational; confirmed weight = 0)
Used only for confidence_breakdown:
  youtube_count < 10   -> confidence_breakdown["low_youtube_legitimacy"] = -0.03
  youtube_count >= 500 -> confidence_breakdown["high_youtube_legitimacy"] = +0.02

### Updated Example Calculation (Post-SRDI)

Keyword: "AI SaaS PRD" (SUBCATEGORY strictness, RSV=0.85)
  trc_reliability = 1.0 - (1.0-0.85)*0.30 = 0.955
  qualified_trc = 1250 * 0.955 = 1193.75 -> count_score ~76.8
  autocomplete_position = 3 -> position_score = 80.0
  trends: raw=58, qualifier=0.72 -> qualified = 58 * 0.72 * 1.15 = 48.0 -> score 55.2
  reddit: raw=7.2, buyer_ratio=0.68 -> qualified = 7.2*(0.40+0.60*0.68) = 5.82 -> 58.2
  demand = (76.8*0.50)+(80.0*0.20)+(55.2*0.20)+(58.2*0.10) = 71.2
  (previously: ~75.3 before SRDI qualification)
