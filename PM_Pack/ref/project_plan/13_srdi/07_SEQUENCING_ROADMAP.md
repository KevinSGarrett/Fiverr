# 07 — SRDI Sequencing Roadmap & Cycle Plan
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Sources:** WAVE_A (tier order), WAVE_L §4 (phase roadmap), live `AGENT_EXECUTION_STRATEGY.md`

---

## 1. HARD DEPENDENCY ORDER

```
R8 (schema, Tier 0)  ─ FIRST, alone, behaviorally inert
     │
     ▼
R1 (search URL/category, Tier 0)
     │
     ▼
R3 (sponsored/zombie, Tier 0) ──► R2 (Stage 3.5 validation, Tier 0/1)
                                        │
                              ┌──── Tier-0 gate ────┐
                              ▼                      ▼
                    R4 (scoring, Tier 1)       R6 (discovery gates, Tier 1)
                              │                      │
                              ▼                      ▼
                    R5 (LLM 7.5, Tier 2)      R7 (ext signals, Tier 2)
                              │
                              ▼
                    R10 (dashboard, Tier 3)
                              │
                              ▼
                    R11 (edge/maintenance, Tier 4)

R9 (testing) ── CONTINUOUS alongside every epic; gates each tier.
```

---

## 2. PHASE / TIER ROADMAP

| Phase | Tier | Weeks | Epics | Theme |
|---|---|---|---|---|
| 1 | 0 | 1–4 | R8, R1, R3, R2 | Clean data at source + schema + ghost detection |
| 2 | 1 | 5–10 | R4, R6, R9 | Scoring quality-aware; discovery gated; test suite hardened |
| 3 | 2 | 11–16 | R5, R7 | Semantic LLM layer + external-signal qualifiers |
| 4 | 3 | 17–22 | R10 | Dashboard, badges, alerts, run-summary |
| 5 | 4 | 23+ | R11 | Edge cases, monitors, monthly audit, first-rec gate |

---

## 3. TIER COMPLETION GATES

### Tier 0 Gate (R8+R1+R3+R2 complete)
- R8 migrations applied + reversible; R1 category filter active for all 9 niches (REG-13/14)
- R3 sponsored/zombie flags populated (REG-17/18/19)
- R2 RSV produced per keyword; ghost blocks recommendations (REG-15/16)
- Golden-run diff shows legacy parity when reads disabled (AC-U3)

### Tier 1 Gate (R4+R6+R9 complete)
- R4 single-TRC-multiplier + opportunity qualifier + clean-gig sets (REG-20/21/22)
- R6 four gates live + discovery rejection rate 20–40% on test run (REG-25/26/27)
- R9 suite at ~3454+ green
- **Discovery activation approved** only after this gate

### Tier 2 Gate (R5+R7 complete)
- R5 Stage 7.5 triggers only in-band, ≤50 calls/run, graceful degrade (REG-23/24)
- R7 qualifiers applied + shared autocomplete classifier (REG-28/29/30)

### Tier 3 Gate (R10 complete)
- Badges/alerts/filters live; ghost hidden by default; run-summary block present

### Tier 4 Gate (R11 complete)
- Monitors + first-recommendation quality gate + monthly audit in place

---

## 4. CYCLE-BY-CYCLE PLAN

| Cycle | Focus | A (plan) | B (build) | D (regress) | E (integrate) |
|---|---|---|---|---|---|
| C1 | R8 schema | Finalize column list | M1–M6 + models + base.py | Apply+rollback, golden-run diff | Merge inert; toggles off |
| C2 | R1 search URL | Confirm NICHE_CATEGORY_MAP | `build_search_url`+fallback | REG-13/14 + url tests | Enable category_filter per niche |
| C3 | R3 sponsored/zombie | Confirm seller fields | Sponsored flag + zombie detector | REG-17/18/19 + zombie tests | Enable flags |
| C4 | R2 Stage 3.5 | Confirm validator config (9 niches) | `validate_result_set`+RSV+stage | REG-15/16 + 14 validator tests | Enable `relevance_validation` |
| — | **Tier-0 gate** | — | — | Full bundle green | Sign-off |
| C5 | R4 scoring | OQ: profitability premium field | TRC reliability + qualifiers | REG-20/21/22 | Enable per calculator |
| C6 | R6 discovery | Confirm discovery flag names | 4 gates + pre-validator | REG-25/26/27 | **Approve discovery activation** |
| C7 | R9 consolidation | Test-structure audit | Fixtures + remaining tests | Full suite ~3454+ | CI floor set |
| C8 | R5 LLM 7.5 | Confirm LLM client signature | Classifier + orchestrator | REG-23/24 | Enable `llm_relevance` |
| C9 | R7 external | Confirm field names | Qualifiers + classifier | REG-28/29/30 | Enable qualifiers |
| C10 | R10 dashboard | Confirm alert model + Streamlit ver | Panels, badges, alerts, filters | Dashboard tests | Release dashboard |
| C11 | R11 edge/ops | Confirm history store + rec gate | Monitors + first-rec gate + audit | Edge-case tests | Enable monitors |

---

## 5. RE-COLLECTION STRATEGY

- **After R1:** re-collect all niches so `search_strictness_used` = SUBCATEGORY/CATEGORY.  
  Legacy keywords carry NONE deduction + "UNCONSTRAINED" badge until re-collected.
- **After R2/R3:** re-collection produces RSV rows + sponsored/zombie flags;  
  legacy scores tagged `legacy_pre_relevance_v1` until keyword is re-run.
- **Prioritized order:** (1) recommendation-feeding keywords; (2) discovery flagged `discovery_needs_recollection`; (3) rest by descending legacy final score
- **Batch by niche** to keep category-filter validation and run-summary block meaningful
- **No destructive backfill:** new rows written; historical rows retained for audit

---

## 6. ROLLOUT SAFETY RAILS

- Every epic merges **behind a config toggle** (`enable_*`); pause by flipping toggles off
- **Golden-run diff** after each scoring change confirms no unintended score movement
- **Re-baseline** distribution before/after R7 (YouTube→0, qualified Trends/Reddit) and R4 (TRC reliability)
- **Discovery stays off** until Tier-1 gate; activation is explicit, logged decision
- **First-recommendation quality gate** (R11.7) guards every first acted-on recommendation

---

## 7. PERMANENT REGRESSION PACK (REG-13…REG-30)

Registered in `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md §7`:

| REG | Test Name | Epic | Tier |
|---|---|---|---|
| REG-13 | test_url_always_includes_category_filter | R1 | 0 |
| REG-14 | test_none_searchresult_applies_demand_deduction | R1 | 0 |
| REG-15 | test_ghost_market_blocks_recommendation_absolutely | R2 | 0 |
| REG-16 | test_trc_qualified_by_result_set_relevance | R2 | 0 |
| REG-17 | test_sponsored_never_in_competition_top_10 | R3 | 0 |
| REG-18 | test_zombie_never_sets_feasibility_review_barrier | R3 | 0 |
| REG-19 | test_organic_trc_adjusted_when_sponsored_exceeds_20pct | R3 | 0 |
| REG-20 | test_niche_profile_excludes_contaminated_keywords | R4 | 1 |
| REG-21 | test_opportunity_qualified_by_relevance | R4 | 1 |
| REG-22 | test_price_outlier_excluded_from_competition_and_profitability | R4 | 1 |
| REG-23 | test_llm_relevance_only_triggers_in_ambiguous_band | R5 | 2 |
| REG-24 | test_llm_ghost_verdict_blocks_recommendation | R5 | 2 |
| REG-25 | test_ghost_discovery_recorded_as_invalid_not_miss | R6 | 1 |
| REG-26 | test_feedback_excludes_contaminated_outcomes | R6 | 1 |
| REG-27 | test_low_specificity_hypothesis_rejected | R6 | 1 |
| REG-28 | test_autocomplete_emerging_not_zero_penalized | R7 | 2 |
| REG-29 | test_reddit_buyer_intent_qualifies_score | R7 | 2 |
| REG-30 | test_trends_qualifier_applied_before_demand | R7 | 2 |

---

*Cross-references: `01_INITIATIVE_CHARTER.md` (goals), `03_EPIC_BREAKDOWN_MASTER.md` (stories/tasks), `06_TEST_PLAN_REGRESSION.md` (test detail)*
