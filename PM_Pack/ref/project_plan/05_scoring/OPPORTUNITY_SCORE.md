# Opportunity Score
# Fiverr Research System — Wave 6, Score 3

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Weight:** 25% (default — highest weight) | **Depth:** All

---

## What It Measures
The net opportunity for a new seller — combining demand and competition with **non-linear interaction**. High demand + weak competition is amplified; high demand + strong competition is dampened.

This is the highest-weighted single score in the default profile because it captures the core question: "Is there room for a new seller to win here?"

---

## Data Inputs

| Component | Source | Field |
|---|---|---|
| Demand Score | keyword_scores | demand_score |
| Competition Score | keyword_scores | competition_score |

This score is derived — it does not pull from any raw collection data directly.

---

## Why Not Just `demand - competition`?

A simple subtraction would miss important non-linear patterns:
- `Demand=80, Competition=20` → Subtraction gives 60. But this is actually a **rare**, exceptional opportunity (high demand + weak competition). It should score higher than 60.
- `Demand=50, Competition=50` → Subtraction gives 0. But moderate demand with moderate competition is a viable opportunity, not a zero.
- `Demand=30, Competition=70` → Subtraction gives -40 (clamped to 0). But "low demand + strong competition" is meaningfully different from "moderate demand + slightly stronger competition" — both shouldn't be the same 0.

We use an **interaction formula** that rewards favorable combinations non-linearly.

---

## Full Python Formula

```python
def calculate_opportunity_score(demand_score: float, competition_score: float) -> float:
    """
    Calculates the Opportunity Score using non-linear interaction.

    Formula:
        base = demand × (1.0 - competition / 100)
        leverage_bonus = bonus when demand is high AND competition is low
        opportunity = base + leverage_bonus, clipped to [0, 100]

    The leverage_bonus rewards the rare "high demand + weak competition" quadrant
    that represents the most valuable opportunities for a new seller.
    """
    if demand_score is None or competition_score is None:
        return None

    # Component 1: Base opportunity = demand × (1 - competition normalized)
    # If demand=80 and competition=20:  80 × 0.80 = 64
    # If demand=80 and competition=80:  80 × 0.20 = 16
    # If demand=50 and competition=50:  50 × 0.50 = 25
    base = demand_score * (1.0 - competition_score / 100.0)

    # Component 2: Leverage bonus for high-demand + low-competition combination
    # Both must be on the right side of the midpoint to earn a bonus.
    # The bonus increases with the distance both factors are from 50.
    if demand_score > 50 and competition_score < 50:
        demand_excess = (demand_score - 50) / 50.0          # 0.0 to 1.0
        competition_gap = (50 - competition_score) / 50.0   # 0.0 to 1.0
        leverage_bonus = demand_excess * competition_gap * 35.0
        # Max bonus when demand=100, competition=0: 1.0 × 1.0 × 35 = 35
        # At demand=80, competition=20: 0.6 × 0.6 × 35 = 12.6
    else:
        leverage_bonus = 0.0

    # Component 3: Penalty for low demand + high competition (worst quadrant)
    # Already captured in the base calculation (base → 0), but we add an explicit floor.
    if demand_score < 30 and competition_score > 70:
        # Cap at base value (no penalty beyond what base already gives)
        opportunity = base
    else:
        opportunity = base + leverage_bonus

    return round(min(100.0, max(0.0, opportunity)), 2)
```

---

## Score Behavior Matrix

| Demand | Competition | Base | Leverage Bonus | Opportunity | Quadrant |
|---|---|---|---|---|---|
| 80 | 20 | 64.0 | 12.6 | 76.6 | Best — rare ideal |
| 80 | 50 | 40.0 | 0.0 | 40.0 | Good demand but tough field |
| 80 | 80 | 16.0 | 0.0 | 16.0 | High demand crowded |
| 50 | 20 | 40.0 | 0.0 | 40.0 | Open field but moderate demand |
| 50 | 50 | 25.0 | 0.0 | 25.0 | Balanced — modest opportunity |
| 50 | 80 | 10.0 | 0.0 | 10.0 | Tough niche |
| 30 | 30 | 21.0 | 0.0 | 21.0 | Low demand even with weak comp |
| 30 | 70 | 9.0 | 0.0 | 9.0 | Bad quadrant |
| 90 | 10 | 81.0 | 28.0 | 100.0 (capped) | Exceptional opportunity |
| 100 | 0 | 100.0 | 35.0 | 100.0 (capped) | Theoretical maximum |

The leverage_bonus is what distinguishes this scoring approach. It captures that the "high demand × low competition" quadrant is exponentially more valuable than the others.

---

## Visual: The Four Quadrants

```
         Competition (lower is better →)
                 0                            100
   Demand     +----+----+----+----+----+----+
   (higher    |   IDEAL          |  TOUGH   |
   is         |   QUADRANT       |  NICHE   |
   better)    |   (leverage      |  (high   |
       100    |    bonus)        |   demand,|
              |                  |   crowded)|
              +----+----+----+----+----+----+
              |   OPEN FIELD     |  WORST   |
              |   (low demand,   |  (low    |
              |    open market)  |  demand, |
              |                  |  crowded)|
        0     +----+----+----+----+----+----+
```

The IDEAL quadrant (high demand × low competition) gets the non-linear leverage bonus that pushes Opportunity Score above 70 even when individual components aren't extreme.

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| demand_score | REQUIRED | Returns None — cannot compute Opportunity without Demand |
| competition_score | REQUIRED | Returns None — cannot compute Opportunity without Competition |

When None is returned, Confidence Modifier reduces by 0.25 (this is the highest-weighted score, so missing it is most impactful).

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Uses full depth Demand and Competition Scores |
| standard | Uses full depth Demand and Competition Scores |
| feasibility | Uses Demand and Competition derived from limited data — Opportunity may be less accurate |
| keyword_only | Uses Demand and Competition from search card data only — Opportunity still computable |

This is one of three scores available at all depths.

---

## Score Interpretation

| Opportunity Score | Meaning |
|---|---|
| 0–20 | Very weak opportunity — high competition or low demand |
| 21–40 | Weak opportunity — marginal entry case |
| 41–60 | Moderate opportunity — entry possible with good execution |
| 61–80 | Strong opportunity — favorable demand/competition balance |
| 81–100 | Exceptional opportunity — high demand with weak competition |

---

## Example Calculation

Continuing the "AI SaaS PRD" example:
- Demand Score: 75.29 (calculated in DEMAND_SCORE.md)
- Competition Score: 65.55 (calculated in COMPETITION_SCORE.md)

Calculation:
```
base = 75.29 × (1.0 - 65.55 / 100.0)
     = 75.29 × 0.3445
     = 25.94

# Does this earn a leverage bonus?
demand_score > 50? Yes (75.29 > 50)
competition_score < 50? No (65.55 > 50)
→ leverage_bonus = 0.0

opportunity = 25.94 + 0.0 = 25.94
```

Result: **Opportunity Score = 25.94** → "Weak opportunity" tier.

Despite high demand, strong competition pulls this keyword into the "Tough Niche" quadrant — a new seller would need exceptional positioning to win.

---

## Second Example — Different Quadrant

**Keyword:** "Gumloop workflow blueprint" (hypothetical)
- Demand Score: 68
- Competition Score: 35

Calculation:
```
base = 68 × (1.0 - 0.35) = 68 × 0.65 = 44.20

demand > 50? Yes. competition < 50? Yes. → leverage_bonus applies
demand_excess = (68 - 50) / 50 = 0.36
competition_gap = (50 - 35) / 50 = 0.30
leverage_bonus = 0.36 × 0.30 × 35 = 3.78

opportunity = 44.20 + 3.78 = 47.98
```

Result: **Opportunity Score = 47.98** — modest opportunity. The leverage bonus added 3.78 points, recognizing that this combination is favorable for a new seller despite the modest individual scores.
