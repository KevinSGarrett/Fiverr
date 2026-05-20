# EPIC 06 — Pricing Engine
# Fiverr Research System — Implementation To-Do

**Source Specs:** Wave 9 (09_pricing)
**Depends On:** Epic 02 (Collection — gig pricing data), Epic 04 (Scoring — competition context)
**Priority:** P1
**Estimated Stories:** 8 | **Estimated Tasks:** 42

---

## Story 6.1 — Price Distribution Analysis (Stage 10.5)

| ID | Task | Type | Description |
|---|---|---|---|
| 6.1.1 | Create PriceDistributionAnalyzer | TASK | `src/pricing/distribution.py` — Per-keyword price cluster detection using KDE. Source: PRICE_DISTRIBUTION_ANALYSIS.md |
| 6.1.2 | Implement KDE-based cluster detection | TASK | scipy.stats.gaussian_kde on gig prices per keyword. Detect peaks (price clusters) via local maxima |
| 6.1.3 | Implement cluster labeling | TASK | Label clusters as BUDGET, MID, PREMIUM based on relative position in distribution |
| 6.1.4 | Implement price gap detection | TASK | Find gaps ≥ 30% between adjacent clusters — these are positioning opportunities |
| 6.1.5 | Implement market type classification | TASK | COMMODITY (tight spread), WIDE_SPREAD (high variance), FRAGMENTED (no clear clusters), PREMIUM_HEAVY, BUDGET_HEAVY |
| 6.1.6 | Implement moat strength analysis | TASK | Correlation of reviews × price — HIGH moat = established sellers charge significantly more |
| 6.1.7 | Implement price-to-quality ratio | TASK | Cross-reference gig_quality_score vs price to find overpriced/underpriced gigs |
| 6.1.8 | Store PriceAnalysis entries | TASK | Per-keyword: clusters (JSON), market_type, moat_strength, price_gaps (JSON), median, mean, std |
| 6.1.9 | Store NichePriceAnalysis entries | TASK | Per-niche: aggregate stats, tier distribution, niche-wide market type |
| 6.1.10 | Create price distribution tests | TASK | Test KDE peaks, gap detection, market classification, moat calculation |

---

## Story 6.2 — New Seller Entry Pricing Model

| ID | Task | Type | Description |
|---|---|---|---|
| 6.2.1 | Create EntryPricingCalculator | TASK | `src/pricing/entry_pricing.py` — Calculate optimal entry price for new seller. Source: NEW_SELLER_PRICING_MODEL.md |
| 6.2.2 | Implement undercut strategy | TASK | Entry price = lowest viable cluster price × (1 - undercut_pct). Default undercut: 15-25% |
| 6.2.3 | Implement moat-adjusted undercut | TASK | HIGH moat → deeper undercut (25%), LOW moat → smaller undercut (10%) |
| 6.2.4 | Implement price floor enforcement | TASK | Never recommend below $5 (Fiverr minimum) or below config.min_viable_price |
| 6.2.5 | Implement price ladder milestones | TASK | 6 milestones: 0 reviews ($entry), 5 reviews (+10%), 10 reviews (+15%), 25 reviews (+20%), 50 reviews (+25%), 100 reviews (=market rate) |
| 6.2.6 | Implement acquisition pricing | TASK | First 5 orders: recommend 30-40% below market to maximize early review velocity |
| 6.2.7 | Calculate projected revenue per tier | TASK | estimated_monthly_orders × price_at_tier for each milestone |
| 6.2.8 | Create entry pricing tests | TASK | Test undercut calculation, moat adjustment, floor enforcement, ladder milestones |

---

## Story 6.3 — Pricing LLM Task (Task 12)

| ID | Task | Type | Description |
|---|---|---|---|
| 6.3.1 | Create pricing_strategy.j2 template | TASK | Template includes: price clusters, market type, moat, competitor prices, entry pricing model output |
| 6.3.2 | Create PricingStrategy output schema | TASK | entry_price_basic/standard/premium, target_prices, milestone_prices, reasoning |
| 6.3.3 | Integrate with recommendation engine | TASK | Task 12 runs during Stage 13 as part of generate_recommendation() |
| 6.3.4 | Create pricing LLM tests | TASK | Test template rendering, output schema validation |

---

## Story 6.4 — Price Ladder Tracker

| ID | Task | Type | Description |
|---|---|---|---|
| 6.4.1 | Create PriceLadderTracker | TASK | `src/pricing/ladder_tracker.py` — Tracks actual review count per gig, suggests when to raise prices |
| 6.4.2 | Implement milestone detection | TASK | On each run, check if any of your gigs crossed a review milestone |
| 6.4.3 | Generate price raise alert | TASK | Alert.alert_type="PRICE_RAISE_DUE" when milestone crossed |
| 6.4.4 | Create ladder tracker tests | TASK | Test milestone detection, alert generation |

---

## Story 6.5 — Revenue Gate Tracker

| ID | Task | Type | Description |
|---|---|---|---|
| 6.5.1 | Create RevenueGateTracker | TASK | `src/pricing/revenue_gate.py` — Tracks monthly revenue vs target gates |
| 6.5.2 | Implement monthly gate thresholds | TASK | Month 4: $1,720, Month 6: $4,770, Month 9: $17,795, Month 10: $25,045, Month 12: $37,500 |
| 6.5.3 | Implement manual order entry | TASK | CLI command: `python run.py log-order --niche X --amount Y --date Z` |
| 6.5.4 | Implement gate status calculation | TASK | ON_TRACK / BEHIND / AHEAD based on cumulative revenue vs prorated target |
| 6.5.5 | Create revenue gate tests | TASK | Test gate thresholds, status calculation |

---

## Story 6.6 — Stage 10.5 Wiring

| ID | Task | Type | Description |
|---|---|---|---|
| 6.6.1 | Wire Stage 10.5 into orchestrator | TASK | Runs after Stage 10 (scoring), before Stage 11 (ranking). PriceDistributionAnalyzer + EntryPricingCalculator |
| 6.6.2 | Implement price analysis skip for keyword_only depth | TASK | Skip detailed pricing for keyword_only niches (insufficient gig data) |
| 6.6.3 | Create Stage 10.5 integration test | TASK | Pre-seed gig data → run pricing analysis → verify PriceAnalysis and NichePriceAnalysis populated |

---

## Story 6.7 — Pricing Dashboard Widgets (Data Layer)

| ID | Task | Type | Description |
|---|---|---|---|
| 6.7.1 | Create get_price_distribution_chart_data() | TASK | Returns histogram + KDE overlay data for Plotly chart |
| 6.7.2 | Create get_price_gap_table_data() | TASK | Returns dataframe of gaps with gap_size, lower_bound, upper_bound |
| 6.7.3 | Create get_price_ladder_chart_data() | TASK | Returns current position + future milestones for step chart |
| 6.7.4 | Create get_revenue_gate_data() | TASK | Returns cumulative revenue + gate thresholds for dual-axis chart |

---

## Story 6.8 — Pricing Export

| ID | Task | Type | Description |
|---|---|---|---|
| 6.8.1 | Create export_pricing_analysis_excel() | TASK | Worksheet per niche: price clusters, gaps, entry prices, ladder milestones |
| 6.8.2 | Create export_pricing_summary_markdown() | TASK | Per-keyword pricing summary with entry price + ladder |
| 6.8.3 | Create pricing export tests | TASK | Test Excel structure, markdown content |

---

## Epic 06 Summary: 8 Stories, 42 Tasks
