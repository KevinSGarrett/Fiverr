# New Seller Pricing Model
# Fiverr Research System — Wave 9

**Document Status:** Complete
**Wave:** 9 — Pricing Strategy Engine
**Purpose:** Optimal entry price calculator for zero-review sellers, undercut strategy, price ladder with review milestones, tier-specific recommendations, first-5-orders pricing, and revenue gate integration.

---

## The Core Problem

A keyword might score 80+ on Profitability — but that score reflects what ESTABLISHED sellers earn. A new seller with zero reviews, no portfolio, and no Fiverr reputation cannot charge the same prices. The question isn't "is this niche profitable?" (Wave 6 answers that) — it's "what should I charge TODAY, and how do I raise prices as I grow?"

---

## Pricing Philosophy for New Sellers

The model follows three principles:

1. **Acquisition pricing:** Your first 5–10 orders are purchased at a DISCOUNT — you're buying reviews, not maximizing margin
2. **Ladder pricing:** Every review milestone unlocks a price increase — your pricing grows with your proof
3. **Tier differentiation:** Basic is your acquisition tier (low margin, high volume), Premium is your margin tier (high margin, low volume)

---

## Entry Price Calculator

```python
# src/pricing/new_seller_pricing.py

from dataclasses import dataclass

@dataclass
class PricingRecommendation:
    """Complete pricing recommendation for a new seller."""
    keyword_id: int
    keyword_text: str
    niche_id: str

    # Recommended entry prices (what to charge with 0 reviews)
    entry_basic: float
    entry_standard: float
    entry_premium: float

    # First-5-orders prices (aggressive acquisition pricing)
    acquisition_basic: float
    acquisition_standard: float
    acquisition_premium: float

    # Price ladder (prices at each review milestone)
    price_ladder: list[dict]
    # [{"milestone": 5, "basic": 65, "standard": 145, "premium": 280}, ...]

    # Target prices (after 50+ reviews — competitive with established sellers)
    target_basic: float
    target_standard: float
    target_premium: float

    # Strategy metadata
    undercut_pct: float  # How far below market median
    moat_adjustment: float  # Additional discount if high review moat
    gap_pricing_used: bool  # Whether entry price targets a detected price gap
    gap_target: float | None  # The price gap midpoint targeted
    market_type: str  # From price dispersion analysis
    confidence: str  # HIGH, MEDIUM, LOW


def calculate_new_seller_pricing(
    keyword_id: int,
    price_analysis: "PriceAnalysis",
    niche_config: dict,
    db,
) -> PricingRecommendation:
    """
    Calculates optimal pricing for a new seller entering this keyword.
    """
    keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()

    # Step 1: Determine base reference prices (market medians)
    ref_basic = price_analysis.basic_median or niche_config["starter_price_basic"]
    ref_standard = price_analysis.standard_median or niche_config["starter_price_standard"]
    ref_premium = price_analysis.premium_median or niche_config["starter_price_premium"]

    # Step 2: Calculate undercut percentage based on market conditions
    undercut_pct = _calculate_undercut(price_analysis)

    # Step 3: Apply moat adjustment (extra discount if review moat is strong)
    moat_adj = _calculate_moat_adjustment(price_analysis)

    # Step 4: Check for price gap opportunities
    gap_target, gap_used = _find_gap_opportunity(price_analysis)

    # Step 5: Calculate entry prices
    total_discount = undercut_pct + moat_adj
    entry_basic = _apply_discount(ref_basic, total_discount)
    entry_standard = _apply_discount(ref_standard, total_discount)
    entry_premium = _apply_discount(ref_premium, total_discount)

    # If a price gap exists in the basic tier, consider targeting it
    if gap_used and gap_target:
        # Only use gap pricing if it's lower than our calculated entry price
        if gap_target < entry_basic:
            entry_basic = gap_target

    # Step 6: Apply floor prices (never go below Fiverr minimums or dignity floor)
    entry_basic = max(entry_basic, _get_floor_price("basic", niche_config))
    entry_standard = max(entry_standard, _get_floor_price("standard", niche_config))
    entry_premium = max(entry_premium, _get_floor_price("premium", niche_config))

    # Step 7: Ensure tier ordering (basic < standard < premium)
    entry_standard = max(entry_standard, entry_basic * 1.5)
    entry_premium = max(entry_premium, entry_standard * 1.4)

    # Step 8: Calculate acquisition prices (first 5 orders — extra aggressive)
    acquisition_basic = _apply_discount(entry_basic, 0.15)
    acquisition_standard = _apply_discount(entry_standard, 0.10)
    acquisition_premium = _apply_discount(entry_premium, 0.05)

    acquisition_basic = max(acquisition_basic, _get_floor_price("basic", niche_config))

    # Step 9: Build price ladder
    price_ladder = _build_price_ladder(
        entry_basic, entry_standard, entry_premium,
        ref_basic, ref_standard, ref_premium,
    )

    # Step 10: Set target prices (competitive with established sellers)
    target_basic = ref_basic * 1.0  # At market median after 50+ reviews
    target_standard = ref_standard * 1.0
    target_premium = ref_premium * 1.05  # Slightly above median with proof

    # Confidence assessment
    confidence = _assess_pricing_confidence(price_analysis)

    return PricingRecommendation(
        keyword_id=keyword_id,
        keyword_text=keyword.keyword_text,
        niche_id=keyword.niche_id,
        entry_basic=round(entry_basic, 0),
        entry_standard=round(entry_standard, 0),
        entry_premium=round(entry_premium, 0),
        acquisition_basic=round(acquisition_basic, 0),
        acquisition_standard=round(acquisition_standard, 0),
        acquisition_premium=round(acquisition_premium, 0),
        price_ladder=price_ladder,
        target_basic=round(target_basic, 0),
        target_standard=round(target_standard, 0),
        target_premium=round(target_premium, 0),
        undercut_pct=round(total_discount * 100, 1),
        moat_adjustment=round(moat_adj * 100, 1),
        gap_pricing_used=gap_used,
        gap_target=round(gap_target, 0) if gap_target else None,
        market_type=price_analysis.market_type or "UNKNOWN",
        confidence=confidence,
    )
```

---

## Undercut Strategy

How far below market median should a new seller price? Depends on market conditions:

```python
def _calculate_undercut(price_analysis: "PriceAnalysis") -> float:
    """
    Returns the base undercut percentage (0.0–0.40).
    How far below market median to price as a new seller.
    """
    market_type = price_analysis.market_type

    # Base undercut by market type
    base_undercut = {
        "COMMODITY": 0.10,       # Tight pricing — small undercut to win on price
        "MODERATE_SPREAD": 0.20, # Moderate room — standard undercut
        "WIDE_SPREAD": 0.25,     # Wide range — can undercut significantly
        "FRAGMENTED": 0.20,      # Fragmented — moderate undercut, differentiate on clarity
    }.get(market_type, 0.20)

    # Adjust based on competition density
    if price_analysis.basic_n and price_analysis.basic_n > 15:
        # Crowded market — need more aggressive pricing
        base_undercut += 0.05
    elif price_analysis.basic_n and price_analysis.basic_n < 5:
        # Sparse market — less undercut needed
        base_undercut -= 0.05

    # Adjust based on skewness
    if price_analysis.basic_skewness and price_analysis.basic_skewness > 0.5:
        # Right-skewed (most sellers are cheap, few are expensive)
        # Most competition is at the low end — less room to undercut
        base_undercut -= 0.05
    elif price_analysis.basic_skewness and price_analysis.basic_skewness < -0.3:
        # Left-skewed (most sellers are expensive, few are cheap)
        # Opportunity to be the affordable option
        base_undercut += 0.05

    return max(0.05, min(0.40, base_undercut))


def _calculate_moat_adjustment(price_analysis: "PriceAnalysis") -> float:
    """
    Additional discount if the review moat is strong.
    When established sellers charge a big premium due to reviews,
    new sellers need a bigger undercut to compensate for zero reviews.
    """
    moat = price_analysis.moat_strength
    if moat == "HIGH":
        return 0.10  # Extra 10% off — strong review moat to overcome
    elif moat == "MEDIUM":
        return 0.05  # Extra 5% off
    else:
        return 0.00  # No additional adjustment — reviews don't command premium
```

---

## Price Gap Opportunity Detection

```python
def _find_gap_opportunity(price_analysis: "PriceAnalysis") -> tuple[float | None, bool]:
    """
    Checks if there's a price gap worth targeting.
    Returns (gap_midpoint, should_use_gap).
    """
    if not price_analysis.basic_gaps:
        return None, False

    # Find the most promising gap:
    # - Must be in the lower half of the price range (new seller territory)
    # - Must be wide enough to be meaningful (>15% of range)
    basic_median = price_analysis.basic_median or 0
    best_gap = None

    for gap in (price_analysis.basic_gaps or []):
        gap_mid = gap.get("gap_midpoint", 0)
        # Only target gaps BELOW the median (new seller pricing zone)
        if gap_mid < basic_median and gap.get("pct_of_range", 0) > 15:
            if best_gap is None or gap["gap_width"] > best_gap["gap_width"]:
                best_gap = gap

    if best_gap:
        return best_gap["gap_midpoint"], True
    return None, False
```

---

## Floor Prices

Never price below these minimums:

```python
def _get_floor_price(tier: str, niche_config: dict) -> float:
    """
    Returns the absolute minimum price for a tier.
    Combines Fiverr platform minimum with a dignity floor.
    """
    FIVERR_MINIMUM = 5.0  # Fiverr's platform minimum

    # Dignity floors — below these prices, the work isn't worth doing
    DIGNITY_FLOORS = {
        "basic": 15.0,     # At least $15 for any deliverable
        "standard": 30.0,  # At least $30 for standard scope
        "premium": 50.0,   # At least $50 for premium scope
    }

    # Niche-specific floors from config (if defined)
    config_floor = niche_config.get(f"price_floor_{tier}", 0)

    return max(FIVERR_MINIMUM, DIGNITY_FLOORS.get(tier, 10.0), config_floor)
```

---

## Price Ladder — Review Milestone Increases

```python
def _build_price_ladder(
    entry_basic: float, entry_standard: float, entry_premium: float,
    target_basic: float, target_standard: float, target_premium: float,
) -> list[dict]:
    """
    Builds a price increase schedule tied to review milestones.
    Each milestone brings prices closer to target (market median).
    """
    milestones = [
        {"reviews": 0,   "label": "Launch (0 reviews)",        "progress": 0.00},
        {"reviews": 5,   "label": "First proof (5 reviews)",   "progress": 0.25},
        {"reviews": 10,  "label": "Established (10 reviews)",  "progress": 0.45},
        {"reviews": 25,  "label": "Growing (25 reviews)",      "progress": 0.65},
        {"reviews": 50,  "label": "Proven (50 reviews)",       "progress": 0.85},
        {"reviews": 100, "label": "Authority (100 reviews)",   "progress": 1.00},
    ]

    ladder = []
    for milestone in milestones:
        p = milestone["progress"]
        ladder.append({
            "milestone_reviews": milestone["reviews"],
            "label": milestone["label"],
            "basic": round(_lerp(entry_basic, target_basic, p), 0),
            "standard": round(_lerp(entry_standard, target_standard, p), 0),
            "premium": round(_lerp(entry_premium, target_premium, p), 0),
            "basic_increase_pct": (
                round((_lerp(entry_basic, target_basic, p) / entry_basic - 1) * 100, 1)
                if entry_basic > 0 else 0
            ),
        })

    return ladder


def _lerp(start: float, end: float, progress: float) -> float:
    """Linear interpolation between start and end."""
    return start + (end - start) * progress


def _apply_discount(price: float, discount_pct: float) -> float:
    """Apply a percentage discount to a price."""
    return price * (1 - discount_pct)
```

---

## Revenue Gate Integration

Does the recommended entry pricing support the revenue targets?

```python
def project_revenue_at_entry_pricing(
    pricing: PricingRecommendation,
    niche_config: dict,
) -> dict:
    """
    Projects order counts needed at entry pricing to hit revenue gates.
    """
    REVENUE_GATES = {4: 1720, 6: 4770, 9: 17795, 10: 25045, 12: 37500}

    # Weighted average order value at entry pricing
    # Assumption: 60% basic, 30% standard, 10% premium (new seller mix)
    entry_aov = (
        pricing.entry_basic * 0.60 +
        pricing.entry_standard * 0.30 +
        pricing.entry_premium * 0.10
    )

    # Net after Fiverr's 20% cut
    net_aov = entry_aov * 0.80

    projections = {}
    for month, target_gross in REVENUE_GATES.items():
        target_net = target_gross * 0.80  # Net after Fiverr cut
        orders_needed = target_gross / entry_aov if entry_aov > 0 else float("inf")
        orders_per_month = orders_needed / month if month > 0 else float("inf")
        orders_per_week = orders_per_month / 4.33

        projections[f"month_{month}"] = {
            "target_gross": target_gross,
            "entry_aov": round(entry_aov, 2),
            "orders_needed_cumulative": round(orders_needed, 0),
            "orders_per_month": round(orders_per_month, 1),
            "orders_per_week": round(orders_per_week, 1),
            "feasible": orders_per_week <= 10,  # Realistic for one person
        }

    # At what review milestone does pricing support the revenue gates?
    for step in pricing.price_ladder:
        step_aov = (
            step["basic"] * 0.50 +  # Mix shifts toward standard as reviews grow
            step["standard"] * 0.35 +
            step["premium"] * 0.15
        )
        step["projected_aov"] = round(step_aov, 2)
        step["month_12_orders_needed"] = round(37500 / step_aov, 0) if step_aov > 0 else None

    return projections


def _assess_pricing_confidence(price_analysis: "PriceAnalysis") -> str:
    """Confidence in the pricing recommendation based on data quality."""
    n = price_analysis.basic_n or 0
    if n >= 10:
        return "HIGH"
    elif n >= 5:
        return "MEDIUM"
    else:
        return "LOW"
```

---

## Pricing Strategy Summary Output

The final output stored per keyword:

```python
@dataclass
class PricingStrategySummary:
    """Human-readable pricing strategy stored in recommendations."""

    # One-paragraph strategy
    strategy_text: str
    # e.g., "Enter at $65 Basic / $145 Standard / $280 Premium — 25% below market median.
    #        The review moat is MEDIUM (established sellers charge ~$45 more).
    #        After your first 5 orders, raise Basic to $75. At 25 reviews, raise to $90.
    #        A price gap exists at $75–$125 in Basic tier — your $65 entry targets the
    #        lower edge of this gap for maximum visibility."

    # Key numbers
    entry_prices: dict  # {basic, standard, premium}
    target_prices: dict  # {basic, standard, premium}
    undercut_pct: float
    price_ladder_summary: str
    # e.g., "$65 → $75 (5 reviews) → $85 (10) → $95 (25) → $105 (50) → $115 (100)"

    # Revenue projection
    orders_to_month_4_gate: int
    feasible_at_entry_pricing: bool

    # Risk flags
    risk_flags: list[str]
    # e.g., ["Acquisition pricing below dignity floor — consider reducing scope instead",
    #        "At entry pricing, month 12 gate requires 577 orders — may need premium upsells"]
```

---

## Integration Points

| System Component | How Pricing Model Integrates |
|---|---|
| Stage 10.5 | Price distribution analysis runs after scoring, before ranking |
| Stage 13 | NEW LLM task #12 (pricing recommendation) uses this model's output as context |
| RecommendationOutput | New `pricing_strategy` field added |
| Dashboard — Opportunities | Price distribution histogram per keyword |
| Dashboard — Recommendations | Pricing strategy card with entry prices + ladder |
| Export — Excel | New "Pricing" sheet with entry/target/ladder columns |
| Revenue Gate Tracker | Orders-needed projection at entry pricing |

---

## Example: Full Pricing Recommendation

**Keyword:** "AI SaaS PRD"
**Market:** WIDE_SPREAD (CV 0.489), median $100, review moat MEDIUM

```
Strategy: Enter at $65 Basic / $145 Standard / $280 Premium — 30% below market median.

Price Ladder:
  Launch (0 reviews):    $65 / $145 / $280
  First proof (5):       $75 / $160 / $305
  Established (10):      $83 / $172 / $325
  Growing (25):          $90 / $183 / $345
  Proven (50):           $97 / $193 / $363
  Authority (100):       $100 / $200 / $375

Revenue Projection at Entry Pricing:
  Entry AOV: $97.75 (60% basic, 30% standard, 10% premium)
  Month 4 gate ($1,720): 18 orders needed (4.5/month, 1.0/week) — FEASIBLE
  Month 12 gate ($37,500): 384 orders needed (32/month, 7.4/week) — FEASIBLE with ladder

Risk Flags:
  - None — entry pricing is sustainable and supports revenue trajectory
```
