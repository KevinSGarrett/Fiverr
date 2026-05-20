# Profitability Score
# Fiverr Research System — Wave 6, Score 5

**Status:** Complete | **Range:** 0–100 | **Direction:** Higher = better | **Weight:** 10% (default), 25% (profitability_focus) | **Depth:** feasibility, standard, full

---

## What It Measures
The revenue potential of this keyword — combining current niche pricing levels, the upsell opportunity from competitor gig extras, and the AOV (average order value) trajectory based on the Wave 19–20 revenue model.

---

## Data Inputs

| Component | Source | Field | Weight |
|---|---|---|---|
| Niche pricing tier vs. platform average | gigs.packages + config | starter_price_basic/standard/premium | 50% |
| Upsell opportunity from gig extras | gigs.gig_extras | gig_extras JSON | 30% |
| AOV trajectory (revenue model integration) | config.revenue_gates + niche.metadata | starter_price_premium | 20% |

---

## Full Python Formula

```python
import statistics

def calculate_profitability_score(keyword_id: int, db) -> float | None:
    """
    Calculates the Profitability Score (0–100).
    Returns None at keyword_only depth.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
    niche = db.query(NicheConfig).filter(NicheConfig.niche_id == keyword.niche_id).first()
    niche_config = get_niche_config_from_yaml(keyword.niche_id)
    depth = niche.current_depth

    if depth == "keyword_only":
        return None

    components = {}
    weighted_sum = 0.0
    weight_used = 0.0

    # Component 1: Niche Pricing Tier vs. Platform Average (50%)
    # Fiverr platform average starting price across freelance services ≈ $40–60
    PLATFORM_AVG_PRICE = 55.0
    PLATFORM_HIGH_PRICE = 150.0  # Considered "premium" pricing

    gigs = get_gigs_for_keyword(keyword_id, db)
    starting_prices = []
    for gig in gigs:
        if gig.packages:
            basic_prices = [p.get("price", 0) for p in gig.packages if p.get("price", 0) > 0]
            if basic_prices:
                starting_prices.append(min(basic_prices))

    if starting_prices:
        avg_starting = statistics.mean(starting_prices)
        # Map pricing tier to score:
        # $50 (platform avg) → 50; $150 (premium tier) → 90; $300+ → 100
        if avg_starting <= 20:
            price_tier_score = 20.0
        elif avg_starting <= PLATFORM_AVG_PRICE:
            # Linear from 20 to 50 between $20 and $55
            price_tier_score = 20.0 + (avg_starting - 20) / (PLATFORM_AVG_PRICE - 20) * 30.0
        elif avg_starting <= PLATFORM_HIGH_PRICE:
            # Linear from 50 to 90 between $55 and $150
            price_tier_score = 50.0 + (avg_starting - PLATFORM_AVG_PRICE) / (PLATFORM_HIGH_PRICE - PLATFORM_AVG_PRICE) * 40.0
        else:
            # Linear from 90 to 100 between $150 and $400+
            price_tier_score = min(100.0, 90.0 + (avg_starting - PLATFORM_HIGH_PRICE) / 250.0 * 10.0)

        components["pricing_tier"] = {
            "value": price_tier_score,
            "weight": 0.50,
            "avg_starting_price": round(avg_starting, 2),
            "n_gigs": len(starting_prices),
        }
        weighted_sum += price_tier_score * 0.50
        weight_used += 0.50

    # Component 2: Upsell Opportunity from Gig Extras (30%)
    # Count extras and analyze their pricing — strong upsell ecosystems indicate AOV potential
    extras_data = []
    for gig in gigs:
        if gig.gig_extras:
            for extra in gig.gig_extras:
                if extra.get("price", 0) > 0:
                    extras_data.append(extra["price"])

    if extras_data:
        avg_extras_count = sum(1 for g in gigs if g.gig_extras) / max(1, len(gigs))
        avg_extras_price = statistics.mean(extras_data)
        # Combined upsell signal:
        # 0 extras avg → 0; 2 extras avg → 50; 5+ extras avg with high prices → 100
        count_signal = min(100.0, avg_extras_count * 25.0)  # 4 extras avg → 100
        price_signal = min(100.0, (avg_extras_price / 50.0) * 50.0)  # $50 avg extras → 50
        upsell_score = (count_signal * 0.60) + (price_signal * 0.40)

        components["upsell_opportunity"] = {
            "value": upsell_score,
            "weight": 0.30,
            "avg_extras_count": round(avg_extras_count, 1),
            "avg_extras_price": round(avg_extras_price, 2),
        }
        weighted_sum += upsell_score * 0.30
        weight_used += 0.30
    else:
        # No extras data — moderate default
        components["upsell_opportunity"] = {
            "value": 30.0, "weight": 0.30, "note": "No gig extras data — defaulted"
        }
        weighted_sum += 30.0 * 0.30
        weight_used += 0.30

    # Component 3: AOV Trajectory from Revenue Model (20%)
    # Uses the niche's configured premium pricing tier vs. the $30k net target trajectory
    # Higher premium tier = higher trajectory toward revenue gate targets
    premium_price = getattr(niche_config.metadata, "starter_price_premium", 0) or 0

    # Map premium price to trajectory contribution:
    #   $150 premium → 30 (low trajectory — needs many orders to hit gates)
    #   $300 premium → 60 (moderate trajectory)
    #   $500 premium → 85 (strong trajectory)
    #   $750+ premium → 100 (excellent trajectory)
    if premium_price <= 100:
        trajectory_score = 20.0
    elif premium_price <= 200:
        trajectory_score = 20.0 + (premium_price - 100) / 100.0 * 25.0  # 20–45
    elif premium_price <= 400:
        trajectory_score = 45.0 + (premium_price - 200) / 200.0 * 30.0  # 45–75
    elif premium_price <= 600:
        trajectory_score = 75.0 + (premium_price - 400) / 200.0 * 20.0  # 75–95
    else:
        trajectory_score = min(100.0, 95.0 + (premium_price - 600) / 200.0 * 5.0)

    components["aov_trajectory"] = {
        "value": trajectory_score,
        "weight": 0.20,
        "premium_tier_price": premium_price,
    }
    weighted_sum += trajectory_score * 0.20
    weight_used += 0.20

    if weight_used < 0.30:
        return None

    profitability_score = weighted_sum / weight_used
    return round(min(100.0, max(0.0, profitability_score)), 2)
```

---

## Missing Data Handling

| Component | Required Status | If Missing |
|---|---|---|
| Pricing data | DEGRADED | Score may compute from other components; confidence −0.08 |
| Gig extras data | OPTIONAL | Defaults to 30.0 (moderate); no confidence deduction |
| Premium tier price | REQUIRED (from config) | Should always be available from niche metadata |

---

## Depth-Tier Behavior

| Depth | Behavior |
|---|---|
| full | Full calculation with top 20 gigs' packages and extras |
| standard | Full calculation with top 10 gigs' packages and extras |
| feasibility | Full calculation with top 5 gigs (less reliable averages) |
| keyword_only | **NOT AVAILABLE** — returns None |

This is the lowest-depth score available (feasibility+) because it depends on `gigs.packages` data which requires Stage 4 collection.

---

## Score Interpretation

| Profitability Score | Meaning |
|---|---|
| 0–20 | Very low profitability — race-to-bottom pricing, no upsells |
| 21–40 | Low profitability — sub-platform-average pricing |
| 41–60 | Moderate profitability — typical Fiverr economics |
| 61–80 | Strong profitability — premium pricing with healthy upsell ecosystem |
| 81–100 | Exceptional profitability — premium niche with high AOV potential |

---

## Example Calculation

**Keyword:** "AI SaaS PRD" (full depth)

Top 10 gigs analyzed:
- Average starting price: $187 → price_tier_score = (50 + (187-55)/(150-55) × 40) = (50 + 132/95 × 40) = 50 + 55.6 = capped at 90.0 (since 187 > 150)
  Actually: 50 + (187-55)/95 × 40 = 50 + 55.6 — but this should be capped against $150 boundary
  Correcting: 187 > 150, so use third bracket: 90 + (187-150)/250 × 10 = 90 + 1.48 = 91.48
- Gig extras data: avg 3.2 extras per gig, avg extra price $42
  - count_signal = min(100, 3.2 × 25) = 80.0
  - price_signal = min(100, 42/50 × 50) = 42.0
  - upsell_score = 80 × 0.60 + 42 × 0.40 = 48 + 16.8 = 64.8
- Niche premium tier: $395 (from config: starter_price_premium)
  - trajectory_score = 45 + (395-200)/200 × 30 = 45 + 29.25 = 74.25

Calculation:
```
weighted_sum = (91.48 × 0.50) + (64.8 × 0.30) + (74.25 × 0.20)
             = 45.74 + 19.44 + 14.85
             = 80.03
profitability_score = 80.03
```

Result: **Profitability Score = 80.03** → "Strong profitability" tier.

For the profitability_focus profile (25% weight), this score significantly contributes to the Final Recommendation Score.

---

## Integration with Revenue Gates

The Profitability Score is calibrated to the Wave 19–20 revenue model:
- Target net: $30,000
- Target gross: $37,500
- Premium tier price across niches: $200 (Python Scraping) to $550 (AI Agent)
- Higher Profitability Score = niche pricing supports the revenue trajectory more efficiently
- The dashboard Revenue Gate Tracker uses Profitability Score to project order count needed per niche
