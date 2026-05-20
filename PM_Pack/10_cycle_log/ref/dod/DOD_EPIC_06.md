# DOD — EPIC 06: Pricing Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 6.1 — Price Distribution Analysis

### Definition of Done
- [ ] PriceAnalysis computed per keyword (p25, median, p75)
- [ ] NichePriceAnalysis aggregate computed
- [ ] price_clusters identified and labelled

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-6.1.1 | KDE produces ≥ 1 cluster for keyword with ≥ 3 gigs priced differently | Cluster count test |
| AC-6.1.2 | Clusters are labeled BUDGET/MID/PREMIUM in ascending price order | Label order test |
| AC-6.1.3 | Price gap detected when adjacent clusters differ by ≥ 30%: gap at ($50, $80) → gap_size=60% | Gap calculation test |
| AC-6.1.4 | market_type COMMODITY when std/mean < 0.15 | Tight distribution test |
| AC-6.1.5 | market_type WIDE_SPREAD when std/mean > 0.50 | Wide distribution test |
| AC-6.1.6 | moat_strength HIGH when correlation(reviews, price) > 0.6 | Correlation test |
| AC-6.1.7 | moat_strength LOW when correlation(reviews, price) < 0.3 | Correlation test |
| AC-6.1.8 | PriceAnalysis row created for every keyword with ≥ 3 gigs | Coverage test |
| AC-6.1.9 | NichePriceAnalysis row created for every niche with ≥ 5 keywords having price data | Aggregate test |

---

## Story 6.2 — New Seller Entry Pricing Model

### Definition of Done
- [ ] entry_price recommendation computed
- [ ] Milestone pricing roadmap generated
- [ ] moat_strength and market_type classified

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-6.2.1 | Entry price = lowest cluster × (1 - undercut). $50 cluster, 20% undercut → $40 | Formula test |
| AC-6.2.2 | HIGH moat → undercut ≥ 25%; LOW moat → undercut ≤ 15% | Moat-dependent undercut test |
| AC-6.2.3 | Entry price never below $5 (Fiverr minimum) | Floor test: $3 cluster → entry = $5 |
| AC-6.2.4 | Price ladder has exactly 6 milestones (0, 5, 10, 25, 50, 100 reviews) | Milestone count test |
| AC-6.2.5 | Milestone prices are monotonically increasing | Sort order test |
| AC-6.2.6 | 100-review milestone price ≈ market median (within ±10%) | Target convergence test |
| AC-6.2.7 | Acquisition pricing (first 5 orders) is 30-40% below market | Discount range test |

---

## Story 6.3 — Pricing LLM Task

### Definition of Done
- [ ] generate_pricing_strategy() returns valid PricingStrategy schema
- [ ] Output stored in Recommendation pricing_strategy field

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-6.3.1 | pricing_strategy.j2 renders with price cluster and moat context | Template render test |
| AC-6.3.2 | PricingStrategy output has entry_price_basic < entry_price_standard < entry_price_premium | Price tier order test |
| AC-6.3.3 | Task 12 integrates into the 14-task async gather without errors | Integration test |

---

## Story 6.4 — Price Ladder Tracker

### Definition of Done
- [ ] Price ladder changes tracked over time per gig
- [ ] Price history queryable for dashboard

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-6.4.1 | Crossing 5-review milestone generates PRICE_RAISE_DUE alert | Alert creation test |
| AC-6.4.2 | Alert includes suggested new price from ladder milestone | Alert content test |

---

## Story 6.5 — Revenue Gate Tracker

### Definition of Done
- [ ] Revenue gate thresholds defined per niche tier
- [ ] Order model populated with revenue tracking data

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-6.5.1 | Gate thresholds match spec: Month 4=$1,720, Month 6=$4,770, etc. | Config test |
| AC-6.5.2 | `log-order` CLI creates Order row with correct amount, niche, date | DB insertion test |
| AC-6.5.3 | At Month 4 with $2,000 cumulative → status = ON_TRACK | Status calculation test |
| AC-6.5.4 | At Month 4 with $800 cumulative → status = BEHIND | Status calculation test |

---

## Epic 06 — Overall Definition of Done

1. ✅ Stage 10.5 produces PriceAnalysis for every keyword with ≥ 3 gigs
2. ✅ Entry pricing calculator generates valid price ladders with moat-adjusted undercuts
3. ✅ Pricing LLM task integrates cleanly into recommendation generation
4. ✅ Revenue gate tracker correctly computes ON_TRACK/BEHIND/AHEAD
5. ✅ All pricing tests pass
