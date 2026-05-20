# Conversion Intent Score
# Fiverr Research System — Wave 6, Score 6

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Weight:** 10% (default), 20% (profitability_focus) | **Depth:** standard, full

---

## What It Measures
How likely buyers searching this keyword are to actually purchase — distinguishing high-intent commercial searches from informational browsing. Higher score = buyers are closer to making a purchase decision.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| LLM intent classification | keywords | intent_class | 50% |
| Reddit demand intent score (LLM-derived) | external_signals (reddit_demand) | reddit_demand_intent_score | 30% |
| Autocomplete position bonus for HIGH_INTENT/TRANSACTIONAL | keywords | autocomplete_position + intent_class | 20% |

---

## Full Python Formula

```python
INTENT_CLASS_SCORES = {
    "TRANSACTIONAL": 100,    # "hire me to build", "I need someone who"
    "HIGH_INTENT":    80,    # "best PRD writer", "build my AI agent"
    "CONSIDERATION":  50,    # "how to write a PRD", "what is MCP server"
    "INFORMATIONAL":  20,    # "what is product management", "AI tutorials"
}

def calculate_conversion_intent_score(keyword_id: int, db) -> float | None:
    """
    Calculates the Conversion Intent Score (0–100).
    Returns None at keyword_only and feasibility depths.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    depth = niche.current_depth

    if depth in ("keyword_only", "feasibility"):
        return None

    components = {}
    weighted_sum = 0.0
    weight_used = 0.0

    # Component 1: LLM Intent Class (50%)
    if keyword.intent_class:
        intent_score = INTENT_CLASS_SCORES.get(keyword.intent_class, 30)
        components["intent_class"] = {
            "value": float(intent_score),
            "weight": 0.50,
            "class": keyword.intent_class,
        }
        weighted_sum += intent_score * 0.50
        weight_used += 0.50

    # Component 2: Reddit Demand Intent Score (30%)
    reddit = get_external_signal_for_niche(keyword.niche_id, "reddit_demand", db)
    if reddit and reddit.reddit_demand_intent_score is not None:
        reddit_score = reddit.reddit_demand_intent_score * 10.0  # 0–10 → 0–100
        components["reddit_intent"] = {
            "value": reddit_score,
            "weight": 0.30,
            "raw": reddit.reddit_demand_intent_score,
        }
        weighted_sum += reddit_score * 0.30
        weight_used += 0.30

    # Component 3: Autocomplete Position Bonus (20%)
    # Strong only when keyword is HIGH_INTENT or TRANSACTIONAL — being in Fiverr's
    # top autocomplete for a commercial keyword is a powerful intent signal.
    if (keyword.intent_class in ("HIGH_INTENT", "TRANSACTIONAL")
            and keyword.autocomplete_position is not None):
        pos = keyword.autocomplete_position
        # Position 1 → 100, position 5 → 60, position 10 → 10
        autocomplete_bonus_score = max(0.0, 100.0 - (pos - 1) * 10.0)
        components["autocomplete_bonus"] = {
            "value": autocomplete_bonus_score,
            "weight": 0.20,
            "position": pos,
        }
        weighted_sum += autocomplete_bonus_score * 0.20
        weight_used += 0.20
    elif keyword.autocomplete_position is not None:
        # Keyword IS in autocomplete but is informational/consideration intent
        # Moderate score — still a popular term but less commercial
        autocomplete_score = 40.0
        components["autocomplete_bonus"] = {
            "value": autocomplete_score,
            "weight": 0.20,
            "position": keyword.autocomplete_position,
            "note": "Lower bonus — keyword is not high commercial intent",
        }
        weighted_sum += autocomplete_score * 0.20
        weight_used += 0.20
    else:
        # Not in autocomplete — weak commercial discovery signal
        components["autocomplete_bonus"] = {
            "value": 10.0,
            "weight": 0.20,
            "note": "Not in Fiverr autocomplete",
        }
        weighted_sum += 10.0 * 0.20
        weight_used += 0.20

    if weight_used < 0.30:
        return None

    conversion_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, conversion_score)), 2)
```

---

## LLM Input Handling

This score is **heavily LLM-driven**:
1. `intent_class` is set by gpt-4o-mini in Stage 2 (Keyword Expansion)
2. `reddit_demand_intent_score` is set by gpt-4o-mini in Stage 6 (Reddit Collection)

If both LLM outputs failed:
- The score falls back to autocomplete-position-only signal (20% weight)
- Score returns very low or None depending on autocomplete presence
- Confidence Modifier reduces by 0.10

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| intent_class | DEGRADED | Score still computable from other components; confidence −0.10 |
| reddit_demand_intent_score | DEGRADED | Score computable from intent_class alone; confidence −0.05 |
| autocomplete_position | OPTIONAL | Treated as "not in autocomplete" → score 10 for this component |

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Full calculation |
| standard | Full calculation |
| feasibility | **NOT AVAILABLE** — returns None |
| keyword_only | **NOT AVAILABLE** — returns None |

This score requires both LLM intent classification AND Reddit demand analysis, so it's only available at standard and full depths.

---

## Score Interpretation

| Conversion Intent Score | Meaning |
|---|---|
| 0–20 | Pure informational — buyers are researching, not purchasing |
| 21–40 | Mostly informational with some consideration intent |
| 41–60 | Mixed intent — some buyers ready to purchase, others browsing |
| 61–80 | Strong commercial intent — buyers actively evaluating options |
| 81–100 | Transactional — buyers are ready to hire now |

---

## Example Calculation

**Keyword:** "AI SaaS PRD"

- intent_class: "HIGH_INTENT" → intent_score = 80
- reddit_demand_intent_score: 7.2 → reddit_score = 72.0
- autocomplete_position: 3, intent_class HIGH_INTENT → bonus eligible
  - autocomplete_bonus_score = 100 - (3-1) × 10 = 80.0

Calculation:
```
weighted_sum = (80 × 0.50) + (72.0 × 0.30) + (80.0 × 0.20)
             = 40.00 + 21.60 + 16.00
             = 77.60
conversion_score = 77.60
```

Result: **Conversion Intent Score = 77.60** → "Strong commercial intent" tier.

---

## Second Example — Informational Keyword

**Keyword:** "what is a PRD"
- intent_class: "INFORMATIONAL" → intent_score = 20
- reddit_demand_intent_score: 2.5 → reddit_score = 25.0
- autocomplete_position: 7, intent_class INFORMATIONAL → no commercial bonus
  - Falls into "autocomplete_bonus = 40.0" branch (in autocomplete but low intent)

Calculation:
```
weighted_sum = (20 × 0.50) + (25.0 × 0.30) + (40.0 × 0.20)
             = 10.00 + 7.50 + 8.00
             = 25.50
conversion_score = 25.50
```

Result: **Conversion Intent Score = 25.50** → "Mostly informational" — this keyword attracts researchers, not buyers. Not worth targeting as a primary gig keyword.

---

## Why This Score Matters

In the user's revenue model, every order is worth $50–$550. A keyword with high search volume but low conversion intent wastes effort because:
- Buyers click but don't message
- Messages don't convert to orders
- Time spent responding to "what is this?" inquiries doesn't pay

A keyword with moderate search volume but high conversion intent is more valuable because:
- Every click is a potential buyer
- Messages convert to orders
- Time spent is revenue-generating

This score helps the user prioritize keywords where the buyers are actually trying to hire someone.
