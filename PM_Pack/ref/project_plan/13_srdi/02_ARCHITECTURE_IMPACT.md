# 02 — SRDI Architecture Impact & Technical Blueprint
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Status:** Active — Draft v1  
**Source:** WAVE_A (problem/architecture) + waves B–L + live `src/` tree

---

## 1. TECHNICAL EXECUTIVE SUMMARY

This initiative inserts a **relevance & integrity spine** into the existing pipeline. It adds three
new pipeline stages (3.5, 4.5, 7.5), hardens Stage 3 and all seven scoring calculators, gates the
discovery loop in four places, qualifies four external signals, extends the schema with two new
models and ~30 additive columns, and surfaces everything in the dashboard.

Architecture is a **defense-in-depth funnel:** contamination removed at source (category filter),
flagged after collection (rule-based validator), filtered inside scoring, semantically checked at
LLM boundary for ambiguous band only, and prevented from poisoning autonomous learning.

---

## 2. PIPELINE — BEFORE vs AFTER

### Before (current)
```
Stage 3   Fiverr Search       → SearchResult(gig_cards, total_result_count, rank)
Stage 4   Gig Detail          → Gig(price, reviews, level, …)
Stage 5   Seller Profile      → Seller(level, member_since, response_rate, …)
Stage 6   External Signals    → ExternalSignal(google_trends, reddit, youtube, autocomplete)
Stage 7   Gig Quality (LLM)  → GigQualityScore / rubric
Stage 8   Competitor Profiling → CompetitorProfile
Stage 10  Scoring (7 + CM)   → KeywordScore
Stage 11  Ranking             → OpportunityRanking
Stage 12  Tag assignment      → tags
Stage 16  Discovery Engine    → hypotheses → collect → score → feedback
```

### After (SRDI target, new stages **bold**, hardened marked ⚙)
```
Stage 3 ⚙  Fiverr Search      → + category-constrained URL, fallback, strictness_used,
                                   sponsored_gig_count, organic_gig_count, pages_collected
Stage 3.5  **Result-Set Val** → ResultSetValidation(result_set_relevance_score,
  (NEW)                           ghost_market_flag, category_contamination_flag,
                                   per-gig relevance_flag/score, confidence_deduction)
Stage 4 ⚙  Gig Detail         → + sponsored propagation, last_reviewed_at, category_path
Stage 4.5  **Zombie Detect**  → Gig.is_zombie / zombie_score / zombie_signals
  (NEW)
Stage 5 ⚙  Seller Profile     → + specialization / last-active signals
Stage 6 ⚙  External Signals   → + fiverr_relevance_qualifier, signal_quality_score
Stage 7    Gig Quality (LLM)  → (unchanged; consumes relevance_flag in R5)
Stage 7.5  **LLM Relevance**  → conditional (0.35–0.75 band): RELEVANT/BORDERLINE/
  (NEW)                           IRRELEVANT, llm_verdict, ghost-market override
Stage 8 ⚙  Competitor Profile → + relevance pre-filter (skip <40% relevant clusters)
Stage 10 ⚙ Scoring (7+CM)    → qualified TRC, filtered gig sets, qualifiers
Stage 12 ⚙ Tag assignment     → + ghost-market demotion / block
Stage 16 ⚙ Discovery Engine  → 4 gates (hypothesis, pre-collection, outcome, feedback)
```

---

## 3. AFFECTED COMPONENTS (file-level)

| Component | Issues | Change | Epic |
|---|---|---|---|
| `src/collection/fiverr_search.py` | 1,2,3,4,5,6,7 | Category URL builder; strictness; counts | R1, R3 |
| **`src/collection/search_url_builder.py`** (NEW) | 1,4,5 | `NICHE_CATEGORY_MAP`, `build_search_url`, `search_with_fallback` | R1 |
| `src/collection/search_result_parser.py` | 2,3,8 | Review-abbrev parse; sponsored flag | R3 |
| **`src/analysis/result_set_validator.py`** (NEW) | 1,2,6,12 | `compute_gig_relevance`, `validate_result_set` | R2 |
| **`src/analysis/zombie_gig_detector.py`** (NEW) | 7 | `compute_zombie_score`, `is_zombie_gig` | R3 |
| **`src/analysis/llm_relevance_classifier.py`** (NEW) | 1,6,12,14 | `LLMRelevanceClassifier`, trigger, apply | R5 |
| **`src/discovery/pre_validator.py`** (NEW) | 13 | `DiscoveryPreValidator` dry-run | R6 |
| `src/collection/gig_detail.py` | 7,16,20 | Sponsored propagation; zombie; `last_reviewed_at` | R3 |
| `src/scoring/demand.py` | 5,9,10 | Qualified TRC; emerging autocomplete; trends qualifier | R4, R7 |
| `src/scoring/competition.py` | 2,3,4,7,11,16 | Sponsored+zombie+relevance filters; price-outlier | R4 |
| `src/scoring/feasibility.py` | 1,3,4,7 | Clean-gig set for level ratio + review barrier | R4 |
| `src/scoring/profitability.py` | 16 | Relevant/organic/non-zombie prices + outlier filter | R4 |
| `src/scoring/confidence.py` | 3,7,15 | RSV deductions; zombie concentration; freshness×relevance | R2, R3, R7 |
| `src/scoring/opportunity.py` | composite | Relevance qualifier on final opportunity | R4 |
| `src/analysis/competitor_profiler.py` | 11,14,17 | Contamination outlier exclusion; synthesis pre-filter | R4, R5 |
| `src/discovery/orchestrator.py` | 13 | Specificity gate + pre-validation + validated-only insert | R6 |
| `src/discovery/feedback.py` | 13 | Relevance-gated outcomes; feedback exclusion | R6 |
| `src/models/*` | all | New models + additive columns + indexes | R8 |
| `src/recommendations/eligibility.py` | 6 | Ghost-market hard block; first-rec quality gate | R2, R11 |
| `src/dashboard/*` | all | Badges, integrity tab, alerts, run summary, filters | R10 |

---

## 4. NEW DATA OBJECTS (overview; full spec in `05_DATA_SCHEMA_MIGRATION.md`)

| Object | Type | Grain | Key Fields |
|---|---|---|---|
| `ResultSetValidation` | NEW table | 1/(keyword, run) | `result_set_relevance_score`, `ghost_market_flag`, `category_contamination_flag`, `confidence_deduction`, `per_gig_relevance` JSON, `llm_validated`, `llm_verdict` |
| `DiscoveryOutcome` (ext) | +cols | 1/discovery kw | `is_invalid`, `is_contaminated`, `invalid_reason`, `relevance_score`, `pre_validation_passed` |
| `Gig` (+cols) | +cols | gig | `is_sponsored`, `is_zombie`, `zombie_score`, `zombie_signals`, `last_reviewed_at`, `relevance_flag`, `relevance_score`, `category_path` |
| `SearchResult` (+cols) | +cols | (kw, run) | `search_strictness_used`, `result_set_relevance_score`, `ghost_market_flag`, `sponsored_gig_count`, `organic_gig_count`, `pages_collected` |
| `KeywordScore` (+cols) | +cols | (kw, run) | `relevance_qualifier`, `trc_reliability_score`, `qualified_trc`, `sponsored_gigs_excluded`, `zombie_gigs_excluded`, `clean_gig_count` |
| `Keyword` (+cols) | +cols | keyword | `discovery_needs_recollection`, `pre_validation_data`, `specificity_confidence` |
| `ExternalSignal` (+cols) | +cols | signal | `fiverr_relevance_qualifier`, `signal_quality_score` |

---

## 5. RELEVANCE SIGNAL PROPAGATION DATA FLOW

```
Stage 3 → gig_cards JSON (sponsored_flag, titles, urls) → search_strictness_used
   │
   ▼ (per niche)
Stage 3.5 result_set_validator
   │   compute_gig_relevance(per gig) → relevance_flag/score (→ Gig)
   │   validate_result_set(keyword) → result_set_relevance_score, ghost_market_flag,
   │                                  category_contamination_flag, confidence_deduction
   ▼
ResultSetValidation row ─────────────────────────────────┐
                                                          │
Stage 4/4.5 → Gig.is_sponsored, is_zombie, last_reviewed_at
                                                          │
                                                          ▼
Stage 7.5 (ambiguous band) → LLM overrides relevance_flag; may set ghost_market_flag
                                                          │
                                                          ▼
Scoring (Stage 10) — per keyword:
   demand.py        : qualified_trc = TRC × trc_reliability
   competition.py   : top-10 = organic ∧ non-zombie ∧ relevance_flag≠False, outlier-filtered
   feasibility.py   : clean_gigs only for level ratio + review barrier
   profitability.py : relevant/organic/non-zombie prices, outliers removed
   confidence.py    : + RSV deduction, zombie-concentration, freshness×relevance
   opportunity.py   : score × (0.5 + 0.5×relevance)
                                                          │
                                                          ▼
Stage 12: ghost_market_flag → demote/block tag
Recommendation eligibility: ghost_market_flag → HARD BLOCK
Discovery feedback: is_invalid / is_contaminated excluded from learning
Dashboard: badges + integrity tab + alerts + run summary
```

**Invariant:** If `ResultSetValidation` absent (legacy), scoring uses pre-initiative behavior
and applies **no** deduction or filter (backward compatible).

---

## 6. CONFIGURATION SURFACE

```yaml
niches:
  - niche_id: <id>
    search:
      category_strictness: SUBCATEGORY     # SUBCATEGORY | CATEGORY | NONE  (R1)
      fallback_on_empty: CATEGORY          #                                  (R1)
      min_results_threshold: 5             #                                  (R1)
    scoring:
      trends_platform_qualifier: 0.65      # 0.40 broad … 0.90 specific     (R7)
relevance:                                 # global toggles
  enable_stage_3_5: true                   # (R2)
  enable_zombie_filter: true               # (R3)
  enable_sponsored_filter: true            # (R3)
  enable_llm_relevance: true               # (R5)
  llm_relevance_max_calls_per_run: 50      # (R5)
  ghost_market_block_recommendations: true # (R2)
```

---

## 7. ARCHITECTURAL DECISIONS

| # | Decision | Rationale |
|---|---|---|
| AD-1 | Stage 3.5 rule-based; LLM is Stage 7.5 conditional | Cost-proportional; rules clear clean/contaminated ends |
| AD-2 | NULL relevance/sponsored/zombie = "include" | Backward compat; legacy rows never penalized |
| AD-3 | Ghost market is the only HARD block | False-positive tolerance |
| AD-4 | Schema is additive only (ALTER ADD COLUMN + new tables) | No destructive migration; trivially reversible |
| AD-5 | `result_set_relevance_score` qualifies TRC multiplicatively | Preserves log10 normalization untouched |
| AD-6 | Per-keyword profile only when contamination detected | Avoids cost/complexity (full version = V1.1) |
| AD-7 | Discovery records `is_invalid` distinct from `is_miss` | Ghost market ≠ low score; must not teach LLM to avoid |
| AD-8 | Constrained TRC needs no demand.py formula change | Constrained search yields corrected count directly |

---

## 8. BUILD SEQUENCE (architectural ordering)

```
R8 (schema) → R1 (category) → R3 (sponsored/zombie) → R2 (Stage 3.5) → [Tier-0 gate]
                                                               │
                                  ┌────────────────────────────┤
                                  ▼                            ▼
                              R4 (scoring)               R6 (discovery gates) → [Tier-1 gate]
                                  │
                                  ▼
                              R5 (LLM 7.5) + R7 (ext signals) → [Tier-2 gate]
                                  │
                                  ▼
                              R10 (dashboard) → R11 (edge/maint) → [Tier-3/4 gate]

R9 (tests): continuous — each epic ships its tests; R9 owns suite structure + permanent pack.
```

---

*See `05_DATA_SCHEMA_MIGRATION.md` for full schema spec. See `03_EPIC_BREAKDOWN_MASTER.md` for all stories/tasks.*
