# Scoring System Integrity Extensions
# Fiverr Research System -- SRDI Initiative Wave E (R4)

**Document Status:** Active
**Source:** WAVE_E_SCORING_SYSTEM_DATA_INTEGRITY_EXTENSIONS.md
**Epic:** R4 (SCRUM-613 to SCRUM-619, SCRUM-813)
**Tier:** 1 -- depends on R8+R1+R3+R2 (Tier 0) shipping first

---

## Overview

R4 extends all 7 scoring calculators and the confidence modifier to use quality
signals produced by R1 (strictness), R2 (RSV), and R3 (sponsored/zombie flags).

Core principle: contaminated inputs produce lower, transparently-explained scores.
Never silently inflated ones.

CRITICAL CONSTRAINT: TRC reliability multiplier (R4.1) is the single authoritative
TRC adjustment. R3.2.3 sponsored-fraction bands are active ONLY until R4 ships.
Never stack both. (Decision DL-209)

---

## R4.1: TRC Reliability Qualifier

See DEMAND_SCORE.md SRDI ADDENDUM for full implementation.

_compute_trc_reliability(search_strictness_used, result_set_relevance_score,
                          sponsored_fraction, total_result_count) -> (float, str):

  reliability = 1.0
  Factor 1 (strictness):   NONE -> -0.15; CATEGORY -> -0.05
  Factor 2 (RSV quality):  deduction = max(0, (1.0 - rsv_score) * 0.30)
  Factor 3 (sponsored):    > 35% -> -0.10
  Factor 4 (extreme TRC):  > 100,000 -> -0.05
  reliability = max(0.0, reliability)

qualified_trc = total_result_count * trc_reliability
count_score uses qualified_trc (log10 normalization formula UNCHANGED)
confidence_breakdown["trc_reliability_low"] = -0.05 when reliability < 0.70
KeywordScore columns written: trc_reliability_score, qualified_trc

---

## R4.2: Autocomplete Emerging Category Distinction

See DEMAND_SCORE.md SRDI ADDENDUM for _classify_autocomplete_absence() implementation.

When autocomplete_position is None, classify instead of defaulting to 0:
  emerging (score=50): discovery source, OR 4+ word keyword, OR STRONGLY_RISING
  emerging_uncertain (score=35): RISING trend
  not_searched (score=0): <= 2 word keyword with flat/declining trends
  unknown (score=20): everything else

Shared function: R7 owns implementation; R4 imports it (Decision DEP-6).

---

## R4.3: Per-Keyword vs Per-Niche Profile Selection

In competition.py, select profile type based on RSV score:
  RSV >= 0.80:  niche-level aggregate profile (high quality result set)
  RSV 0.60-0.80: per-keyword profile (moderate contamination)
  RSV < 0.60:   per-keyword profile with contamination outlier exclusion

See COMPETITOR_PROFILING.md SRDI ADDENDUM for build_niche_competitor_profile() detail.

---

## R4.4: Niche Profile Contamination Outlier Exclusion

Keywords with RSV < 0.40 excluded from niche aggregate profile.
Fallback to full set + WARNING when all keywords would be excluded.
See COMPETITOR_PROFILING.md SRDI ADDENDUM.

Regression: REG-20 test_competition_profile_excludes_contaminated_keywords_in_niche_aggregate

---

## R4.5: Price Outlier Exclusion (IQR Method)

_filter_price_outliers(prices) applied in competition.py AND profitability.py:
  Requires >= 4 prices to activate
  upper_bound = Q3 + 2.5 * IQR
  Returns filtered list (never empty -- falls back to original if all filtered)

See COMPETITION_SCORE.md SRDI ADDENDUM.

Regression: REG-22 test_price_outliers_excluded_from_competition_price_component

---

## R4.6: Clean Gig Set for Feasibility

All feasibility metrics use clean gigs: organic AND non-zombie AND relevance_flag != False.
Fallback to full set + WARNING when < 3 clean gigs.
See NEW_SELLER_FEASIBILITY.md SRDI ADDENDUM.

---

## R4.7: Opportunity Relevance Qualifier

opportunity_score * (0.50 + 0.50 * rsv_score) when rsv_score < 0.70.
See OPPORTUNITY_SCORE.md SRDI ADDENDUM.

Regression: REG-21 test_opportunity_score_qualified_by_result_set_relevance

---

## R4.7: Intent Result-Set Cross-Check

In intent.py (conversion intent scoring): add result-set intent alignment check.
When RSV indicates contamination, intent signals from cross-category gig titles
may incorrectly classify the keyword intent.
RSV.result_set_relevance_score < 0.60: apply -0.05 intent confidence adjustment.

---

## KeywordScore Transparency Columns

After all scoring, write to KeywordScore (schema from R8 M4):
  trc_reliability_score  -- the computed reliability 0.0-1.0
  qualified_trc          -- TRC * reliability
  relevance_qualifier    -- RSV score used for opportunity qualification
  sponsored_gigs_excluded -- count
  zombie_gigs_excluded    -- count
  clean_gig_count         -- len(clean_gigs) used in feasibility

These columns power the Data Integrity dashboard tab (R10).

---

## Backward Compatibility

When RSV is None (legacy keyword): all R4 qualifications fall back to pre-SRDI behavior.
NULL on is_sponsored/is_zombie: treated as organic/non-zombie (include).
No retroactive penalization of historical scores.

AC-U3: NULL flag / absent RSV -> identical score to pre-SRDI baseline.
