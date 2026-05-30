# 09 — SRDI Traceability Matrix
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Purpose:** Every one of the 20 problems in WAVE_A is owned by a wave, epic, stories/tasks, permanent regression, AC, code component, and dashboard surface.  
**Wave→Epic spine:** B→R1 · C→R2 · D→R3 · E→R4 · F→R5 · G→R6 · H→R7 · I→R8 · J→R9 · K→R10 · L→R11

---

## 1. ISSUE → EVERYTHING MASTER MATRIX

| # | Issue | Sev | Tier | Wave→Epic | Key Stories | REG | AC | Component | Dashboard |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Semantic broadening | CRIT | 0 | B→**R1** | R1.1–R1.4 | REG-13,14 | AC-R1.* | `build_search_url`, Stage 3 URL | strictness badge |
| 2 | Gig title keyword stuffing | HIGH | 2 | F→**R5**/C→R2 | R5.2–R5.4 | REG-23 | AC-R5.* | LLM Stage 7.5, `relevance_v1` prompt | per-gig relevance badge |
| 3 | Sponsored result contamination | HIGH | 0 | D→**R3** | R3.1–R3.2 | REG-17,19 | AC-R3.* | sponsored detector, competition top-10 filter | sponsored chip + count |
| 4 | Category boundary contamination | CRIT | 0 | B→**R1** | R1.1–R1.4 | REG-13 | AC-R1.* | `NICHE_CATEGORY_MAP`, Stage 3 URL | strictness badge |
| 5 | TRC inflation for broad terms | CRIT | 0/1 | E→**R4**/B→R1 | R4.1; R1.6 | REG-16,30 | AC-R4.* | `demand.py` TRC qualifier (×RSV) | TRC reliability indicator |
| 6 | Ghost market keywords | CRIT | 0/1 | C→**R2** | R2.3–R2.5 | REG-15 | AC-R2.* | `validate_result_set`, recommendation block | ghost banner (hard block) |
| 7 | Zombie gig contamination | HIGH | 0 | D→**R3** | R3.3–R3.4 | REG-18 | AC-R3.* | zombie detector, feasibility barrier | zombie chip |
| 8 | Review count abbrev parsing | MED | 2 | D→**R3** | R3.5 | — | AC-R3.* | review-count parser | — (data-quality) |
| 9 | Trends platform-intent mismatch | HIGH | 2 | H→**R7** | R7.1–R7.2 | REG-30 | AC-R7.* | Trends qualifier (0.65 base + modifiers) | ext-signal integrity tab |
| 10 | Autocomplete penalizing emerging niches | HIGH | 3 | H→**R7** | R7.4 | REG-28 | AC-R7.* | shared autocomplete classifier | emerging indicator |
| 11 | Niche competitor profile contamination | CRIT | 1 | E→**R4** | R4.3–R4.4 | REG-20 | AC-R4.* | competition profile aggregation | contamination indicator |
| 12 | Gig title relevance in weakness scoring | MED | 2 | F→**R5** | R5.2–R5.4 | REG-23 | AC-R5.* | weakness calculator + LLM relevance | per-gig relevance |
| 13 | Discovery feedback-loop amplification | HIGH | 1 | G→**R6** | R6.1–R6.4 | REG-25,26,27 | AC-R6.* | discovery gates, `is_invalid` | rejection-rate |
| 14 | Competitor synthesis LLM hallucination | HIGH | 2 | F→**R5** | R5.5 | REG-24 | AC-R5.* | synthesis relevance fraction gate | synthesis status |
| 15 | Freshness score masking data quality | MED | 3 | H→**R7** | R7.5 | — | AC-R7.* | freshness×relevance combiner | freshness indicator |
| 16 | Price contamination cross-category | HIGH | 2 | E→**R4** | R4.5 | REG-22 | AC-R4.* | competition price component, IQR filter | price-outlier note |
| 17 | Seller bio on wrong competitors | MED | 3 | H→**R7**/R5 | R7.* + R5 gating | — | AC-R7.* | seller specialization on relevant set | — |
| 18 | Intent keyword-only classification | MED | 2 | E→**R4**/H | R4.* intent; R7 reddit | REG-21,29 | AC-R4.* | intent cross-check, reddit qualifier | intent indicator |
| 19 | Pagination depth inconsistency | LOW | 3 | D→**R3** | R3.* pagination | — | AC-R3.* | Stage 3 `pages_collected` | pages-collected note |
| 20 | Collection timing staleness | LOW | 3 | H→**R7**/R8 | R7.5 + R8 `collected_at` | — | AC-R7.* | `collected_at`, freshness | freshness/timing note |

**Coverage:** 20/20 issues mapped · 11 epics each tracing to ≥1 issue · 18 permanent regressions each tracing to ≥1 issue.

---

## 2. REGRESSION → ISSUE → EPIC MAP (REG-13…REG-30)

| REG | Test Name | Epic | Guards Issues |
|---|---|---|---|
| REG-13 | `test_fiverr_search_url_always_includes_category_filter_for_production_niches` | R1 | 1, 4 |
| REG-14 | `test_unconstrained_search_result_applies_demand_confidence_deduction` | R1 | 1 |
| REG-15 | `test_ghost_market_blocks_recommendation_generation_absolutely` | R2 | 6 |
| REG-16 | `test_trc_qualified_by_result_set_relevance_score_in_demand` | R2 | 5 |
| REG-17 | `test_sponsored_gigs_never_included_in_competition_top10` | R3 | 3 |
| REG-18 | `test_zombie_gigs_never_used_in_feasibility_review_barrier` | R3 | 7 |
| REG-19 | `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent` | R3 | 3 |
| REG-20 | `test_competition_profile_excludes_contaminated_keywords_in_niche_aggregate` | R4 | 11 |
| REG-21 | `test_opportunity_score_qualified_by_result_set_relevance` | R4 | 16, 18 |
| REG-22 | `test_price_outliers_excluded_from_competition_price_component` | R4 | 16 |
| REG-23 | `test_llm_ghost_market_verdict_propagates_to_recommendation_block` | R5 | 2, 6, 12 |
| REG-24 | `test_competitor_synthesis_skipped_when_relevance_fraction_below_40_percent` | R5 | 14 |
| REG-25 | `test_ghost_market_discovery_outcome_marked_invalid_not_miss` | R6 | 13 |
| REG-26 | `test_contaminated_discovery_outcome_excluded_from_feedback_learning` | R6 | 13 |
| REG-27 | `test_hypothesis_rejected_when_specificity_confidence_below_threshold` | R6 | 13 |
| REG-28 | `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score` | R7 | 10 |
| REG-29 | `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low` | R7 | 18 |
| REG-30 | `test_trends_platform_qualifier_applied_before_demand_score_calculation` | R7 | 9 |

Per-epic counts: R1=2 · R2=2 · R3=3 · R4=3 · R5=2 · R6=3 · R7=3 = **18 total**

---

## 3. PROTECTION MATRIX (defense-in-depth)

| Threat | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
|---|---|---|---|---|---|---|---|
| Semantic broadening | **PRIMARY** | ✓ | — | ✓ | ✓ | — | — |
| Gig title stuffing | ✓ | ✓ | — | ✓ | **PRIMARY** | — | — |
| Sponsored contamination | — | ✓ | **PRIMARY** | ✓ | — | — | — |
| Category boundary cross | **PRIMARY** | ✓ | — | ✓ | ✓ | — | — |
| TRC inflation | ✓ | ✓ | — | **PRIMARY** | — | — | — |
| Ghost markets | ✓ | **PRIMARY** | — | ✓ | ✓ | ✓ | — |
| Zombie gigs | — | ✓ | **PRIMARY** | ✓ | — | — | — |
| Trends mismatch | — | — | — | ✓ | — | — | **PRIMARY** |
| Autocomplete penalty | — | — | — | — | — | — | **PRIMARY** |
| Niche contamination | ✓ | ✓ | — | **PRIMARY** | ✓ | — | — |
| Discovery amplification | — | — | — | — | ✓ | **PRIMARY** | — |
| LLM hallucination | — | — | — | — | **PRIMARY** | ✓ | — |
| Price contamination | ✓ | ✓ | — | **PRIMARY** | — | — | — |

R8/R9/R10/R11 are cross-cutting structural enablers (schema/tests/dashboard/monitoring).

---

## 4. EPIC → WAVE → TIER → DEPENDENCY QUICK MAP

| Epic | Wave | Tier | Hard Deps | Adds REGs |
|---|---|---|---|---|
| R8 Schema | I | 0 (foundation) | — | structural |
| R1 Search-URL | B | 0 | R8 | REG-13, REG-14 |
| R3 Sponsored/zombie | D | 0 | R8, R1 | REG-17/18/19 |
| R2 Relevance validation | C | 0/1 | R8, R1 | REG-15, REG-16 |
| **Tier-0 gate** | | | R8+R1+R3+R2 | |
| R4 Scoring integrity | E | 1 | R2, R3 | REG-20/21/22 |
| R6 Discovery gates | G | 1 | R8, R2 | REG-25/26/27 |
| R5 LLM Stage 7.5 | F | 2 | R2, gpt-4o-mini | REG-23, REG-24 |
| R7 External signals | H | 2 | DEP-6 (shared classifier) | REG-28/29/30 |
| R10 Dashboard | K | 3 | R8, all flag producers | structural |
| R11 Edge/maintenance | L | 4 | all | structural |
| R9 Testing | J | continuous | spans all | owns all 18 REGs |

---

## 5. ORPHAN / GAP AUDIT

- **Issues with no primary epic:** none (20/20 owned)
- **Epics with no source issue:** none (every R-epic traces to ≥1 WAVE_A issue or is a declared cross-cutting enabler)
- **REGs with no issue:** none (18/18 mapped)
- **Issues with no permanent REG:** #8, #15, #17, #19, #20 — guarded by epic-local tests; candidates for promotion in monthly audit (R11) if regression occurs
- **Dashboard gaps:** data-quality-only issues (#8, #17, #19) surface in run-summary integrity block, not per-keyword chips

---

*Cross-references: `03_EPIC_BREAKDOWN_MASTER.md` (epic detail), `04_DOD_AND_ACCEPTANCE.md` (AC text), `06_TEST_PLAN_REGRESSION.md` (REG names)*
