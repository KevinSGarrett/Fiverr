# 04 — SRDI Definition of Done & Acceptance Criteria
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Source:** 15_DOD_AND_ACCEPTANCE_CRITERIA.md  
**Tags/Thresholds:** STRONG GO ≥80 · CONDITIONAL GO 60–79 · MONITOR 40–59 · CAUTION 20–39 · PASS <20 · CM floor 0.20

---

## 1. UNIVERSAL DOD CHECKLIST (every epic)

- [ ] All stories' tasks implemented and merged behind the documented config toggle
- [ ] All new/changed code paths are **additive & non-destructive** (NULL/absent → legacy behavior)
- [ ] Scores remain 0–100; confidence remains 0–1 (floor 0.20); tag thresholds unchanged
- [ ] New columns/models present per `05_DATA_SCHEMA_MIGRATION.md`; migrations idempotent and reversible
- [ ] Unit + integration tests for the epic pass; relevant REG-13…REG-30 added to permanent pack
- [ ] Backward-compat test: pre-migration run re-scores **identically** when epic's reads are disabled
- [ ] `score_components` JSON carries human-readable note/reason for every adjustment
- [ ] No PII handling; no new external calls beyond documented LLM (R5) usage
- [ ] Dashboard/alert surface updated where epic produces user-visible signals (R10 coordination)
- [ ] Developer + AI handoff (`10_DEVELOPER_HANDOFF.md`/`11_AI_AGENT_HANDOFF.md`) updated with confirmed live paths

---

## 2. UNIVERSAL ACCEPTANCE CRITERIA

| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-U1 | All scores stay within 0–100 across every calculator after changes | Property test over random + fixture inputs |
| AC-U2 | Confidence modifier ∈ [0.20, 1.0]; never inverts a tag silently | Unit test on CM bounds + integration |
| AC-U3 | NULL flag / absent RSV ⇒ identical score to pre-initiative baseline | Golden-run diff on frozen dataset |
| AC-U4 | Every adjustment explained in `score_components`/`per_gig_relevance` | JSON-shape assertion test |
| AC-U5 | Migrations apply in order, idempotent, reversible; no data loss | Apply+rollback on copy of live DB |
| AC-U6 | Full suite ≥ baseline (~3334) + ~120 new, all green | `pytest -q tests/` |
| AC-U7 | Pipeline completes with LLM (R5) disabled (graceful degrade) | Integration run with `enable_llm_relevance=false` |

---

## 3. PER-EPIC ACCEPTANCE CRITERIA

### R1 — Search URL / Category Hardening
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R1.1 | All 9 production niches map to a Fiverr category; `build_search_url` emits `category_id` | `test_all_9_production_niches_have_category_mapping` |
| AC-R1.2 | SUBCATEGORY → CATEGORY → NONE fallback chain works; recorded in `search_strictness_used` | `search_with_fallback` unit + integration |
| AC-R1.3 | Unconstrained (NONE) collection applies demand confidence deduction | REG-14 |
| AC-R1.4 | Category filter always applied for production niches (no silent NONE) | REG-13 |
| AC-R1.5 | Page 2+ offset + special-char encoding correct | Unit test |

### R2 — Relevance Validation (Stage 3.5)
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R2.1 | Per-gig relevance: exact match ≥0.60, cross-category False, generic ≤0.30 | `test_compute_gig_relevance_*` |
| AC-R2.2 | Result-set relevance = relevant/analyzed; clean ≥0.80; one RSV row per keyword/run | Validator + uniqueness test |
| AC-R2.3 | Ghost market (<0.20 with >5 results) → flag + confidence_deduction = −0.50 | `test_validate_result_set_ghost_market_detected` |
| AC-R2.4 | Contamination 0.40–0.80 → `category_contamination_flag` + tiered deduction | `test_validate_result_set_moderate_contamination` |
| AC-R2.5 | TRC qualified by result-set relevance in demand | REG-16 |
| AC-R2.6 | Ghost market absolutely blocks recommendation generation | REG-15 |

### R3 — Sponsored / Zombie Filtering
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R3.1 | Sponsored gigs flagged + counted; never in competition top-10 | REG-17 |
| AC-R3.2 | Organic TRC adjusted when sponsored fraction >20% (≤20→×.90, ≤35→×.80, else ×.70) | REG-19 |
| AC-R3.3 | Zombie score + flag at threshold 0.50; **new sellers not misclassified** | `test_zombie_*` |
| AC-R3.4 | Zombie gigs never set the feasibility review barrier | REG-18 |
| AC-R3.5 | "10k+" parses to 10000; pagination normalized to TOP_N=10 | Review-parse + pagination test |

### R4 — Scoring Integrity Extensions
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R4.1 | `trc_reliability` ∈ [0,1] computed once; qualified TRC drives demand; persisted | `test_trc_reliability.py` |
| AC-R4.2 | Emerging autocomplete → neutral 50; non-emerging absence stays 0 | Unit test |
| AC-R4.3 | Niche profile excludes <0.40-relevance keywords | REG-20 |
| AC-R4.4 | Opportunity qualified by relevance (×(0.5+0.5×rel)) | REG-21 |
| AC-R4.5 | Price IQR outliers excluded from competition + profitability | REG-22 |
| AC-R4.6 | Feasibility uses clean-gig set; KeywordScore integrity cols populated | Integration + schema test |

### R5 — LLM Relevance (Stage 7.5)
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R5.1 | Triggers only in band 0.35–0.75 ∧ final≥45 (+discovery/ghost-watch exceptions) | `test_llm_relevance_trigger.py` |
| AC-R5.2 | ≤50 calls/run; caching active; ≈$0.06/typical run | Cost-cap test |
| AC-R5.3 | Verdict→action: IRRELEVANT↓, RELEVANT↑, BORDERLINE no-op, GHOST_MARKET→RSV ghost | REG-23 |
| AC-R5.4 | Competitor synthesis: skipped <40% / trimmed 40–80% / passthrough ≥80% | REG-24 |
| AC-R5.5 | LLM failure never crashes run (None + log; keeps rule-based RSV) | Failure-path test |

### R6 — Discovery Relevance Gates
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R6.1 | All 4 mode prompts include anti-contamination instructions + `specificity_confidence` | Prompt-content test |
| AC-R6.2 | Hypotheses below confidence(0.50)/specificity(0.65) rejected | REG-27 |
| AC-R6.3 | Pre-validation dry-run rejects ghost/low-relevance/too-low-TRC before full collection | `test_discovery_pre_validator.py` |
| AC-R6.4 | Ghost discovery → `is_invalid` (not miss) + retired | REG-25 |
| AC-R6.5 | Contaminated/invalid outcomes excluded from feedback learning | REG-26 |

### R7 — External Signal Integrity
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R7.1 | Trends qualifier (0.65 base + modifiers) computed, clamped [0.20,0.95], applied before demand | REG-30 |
| AC-R7.2 | Reddit qualified score = raw×(0.40+0.60×ratio); lower than raw when intent low | REG-29 |
| AC-R7.3 | YouTube weight 0; <10 deducts confidence, ≥500 adds confidence | `test_external_signal_integrity.py` |
| AC-R7.4 | Autocomplete emerging→50 / not_searched→0 / unknown→20 (shared classifier) | REG-28 |
| AC-R7.5 | Freshness×relevance geometric mean; fresh+irrelevant scores low | `test_freshness_relevance_quality.py` |

### R8 — Schema Extensions & Migrations
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R8.1 | `result_set_validations` created with UNIQUE(keyword_id, run_id) + 5 indexes | Migration test |
| AC-R8.2 | ~30 additive columns across 5 tables + DiscoveryOutcome extended | Schema-parity test |
| AC-R8.3 | Keyword↔RSV relationship registered; cascade correct | ORM test |
| AC-R8.4 | NULL/default values preserve legacy scoring (AC-U3) | Golden-run diff |
| AC-R8.5 | Storage impact <1 MB/run | Storage sanity check |

### R9 — Testing & Validation Framework
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R9.1 | 10 unit + 3 integration + 2 fixture files created per test plan | File presence + collection |
| AC-R9.2 | REG-13…REG-30 defined, green, registered in `AGENT_EXECUTION_STRATEGY.md §7` | Pack run |
| AC-R9.3 | All LLM tests mocked; integration isolated per run_id | Review + CI |

### R10 — Dashboard & Alerting
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R10.1 | Relevance Quality Score panel + 7 badges render; emerging clearly marked | `test_badge_rendering.py` + UI check |
| AC-R10.2 | 6 alert types generated at Stage 3.5 + run end | `test_relevance_alerts.py` |
| AC-R10.3 | Ghost markets excluded by default in Opportunities; relevance bars shown | Filter-logic test |
| AC-R10.4 | No auto-actions; NULL rows render gracefully | Review |

### R11 — Edge Cases, Future-Proofing, Maintenance
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-R11.1 | Negation-aware exclusion + multilingual neutral handling | Edge-case unit tests |
| AC-R11.2 | Monitors (cliff, filter-health) fire correctly + don't over-fire | Monitor tests on fixtures |
| AC-R11.3 | Emerging bonus only for high-integrity emerging keywords | Unit test |
| AC-R11.4 | First-recommendation quality gate blocks on missing RSV/ghost/<0.70/not-LLM/NONE | Quality-gate test |
| AC-R11.5 | Legacy scores tagged; monthly audit + new-niche checklist in place | Review + audit dry-run |

---

## 4. INITIATIVE-LEVEL OVERALL DoD

1. Every production niche collects with a category filter; `search_strictness_used` recorded each run
2. Every keyword has a Stage 3.5 RSV; ghost markets flagged and **cannot** produce a recommendation
3. Sponsored and zombie gigs never inflate competition/feasibility; new sellers not misclassified
4. Every scoring calculator is input-quality-aware; contaminated inputs lower scores transparently
5. Ambiguous keywords (and all discovery hypotheses) LLM-validated within ≤50-call/run budget
6. Discovery loop cannot amplify phantom markets (4 gates; invalid≠miss; feedback filtered)
7. External signals report Fiverr-buyer intent (qualifiers), not generic interest
8. All schema changes additive, idempotent, reversible; legacy rows score unchanged
9. 120+ new tests pass; REG-13…REG-30 run every cycle
10. Users see clear integrity badges/alerts; ghost markets hidden by default; emerging keywords explained
11. Platform-change monitors alert instead of silently degrading; first-recommendation gate enforced
12. System-health KPIs tracked monthly: ghost <8%, avg relevance >0.78, fallback <10%, discovery rejection 20–40%

---

*Cross-references: `07_SEQUENCING_ROADMAP.md` (gates), `06_TEST_PLAN_REGRESSION.md` (test detail)*
