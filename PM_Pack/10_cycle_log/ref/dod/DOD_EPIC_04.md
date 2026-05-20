# DOD — EPIC 04: Scoring Engine
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## All Scores — Universal Acceptance Criteria

| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-4.0.1 | Every score is a float in range 0-100 (except confidence which is 0-1) | Range assertion on all computed scores |
| AC-4.0.2 | Every score handles null inputs gracefully (returns None, not crash) | Null input test per calculator |
| AC-4.0.3 | Score components JSON is populated with all sub-component values | JSON structure test |
| AC-4.0.4 | All 4 weight profiles have weights summing to 1.0 ± 0.001 | Sum assertion per profile |
| AC-4.0.5 | `--mode score-only` runs Stages 10-12 and produces tags for all scored keywords | Integration test |

## Score-Specific Acceptance Criteria

| AC ID | Score | Criteria | Validation Method |
|---|---|---|---|
| AC-4.1.1 | Demand | Keyword with 5000 Fiverr results, autocomplete pos 1, RISING trend, high Reddit → score ≥ 80 | High-demand scenario test |
| AC-4.1.2 | Demand | Keyword with 10 results, no autocomplete, no trends, no Reddit → score ≤ 20 | Low-demand test |
| AC-4.2.1 | Competition | All Level 2+ sellers with 500+ reviews → competition ≥ 80 (=tough market) | High-competition test |
| AC-4.2.2 | Competition | Mostly new sellers with < 10 reviews → competition ≤ 30 | Low-competition test |
| AC-4.3.1 | Opportunity | High demand (80) + low competition (20) → opportunity ≥ 70 with leverage bonus | Quadrant test |
| AC-4.3.2 | Opportunity | Low demand (20) + high competition (80) → opportunity ≤ 15 | Anti-quadrant test |
| AC-4.4.1 | Feasibility | Entry feasibility 9/10 + high new_seller_ratio → feasibility ≥ 75 | High-feasibility test |
| AC-4.10.1 | Confidence | Keyword with all data sources present and fresh → confidence ≥ 0.85 | Full-data test |
| AC-4.10.2 | Confidence | Keyword with only Fiverr search data (no trends, no Reddit) → confidence ≤ 0.50 | Sparse-data test |
| AC-4.11.1 | Final | Score 82, confidence 0.95 → final ≈ 77.9 (82 × 0.95) | Multiplication test |
| AC-4.11.2 | Final | Score 82, confidence 0.15 → final ≈ 16.4 (82 × 0.20, floor applied) | Floor test |
| AC-4.11.3 | Tags | Final 85 → STRONG GO, Final 65 → CONDITIONAL GO, Final 45 → MONITOR | Threshold tests |
| AC-4.11.4 | Tags | Final 82, confidence 0.45 → CONDITIONAL GO (demoted from STRONG GO) | Demotion test |

## Epic 04 — Overall Definition of Done

1. ✅ All 11 score calculators produce valid 0-100 scores for every keyword with sufficient data
2. ✅ All 4 weight profiles produce different final scores for the same keyword
3. ✅ Tags are assigned correctly based on final score thresholds
4. ✅ Confidence-based tag demotion works for low-confidence keywords
5. ✅ OpportunityRanking table populated with rank, tag, final_score per keyword per run
6. ✅ All scoring tests pass
