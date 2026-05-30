# 10 — SRDI Developer Handoff
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Audience:** Human developer implementing SRDI in `C:\Fiverr\Fiverr`  
**Read first:** The epic file you're building (`epics/R*.md`), then `04_DOD_AND_ACCEPTANCE.md` and `06_TEST_PLAN_REGRESSION.md`  
**Golden rule:** Facts from the live code; behavior from the waves. Where a spec name differs from live code, change the *name* — never the *logic*. Log every adaptation in `08_REGISTERS.md §6`.

---

## 1. ENVIRONMENT

1. **Repo:** `C:\Fiverr\Fiverr` (live project, Cycle 049)
2. **Python:** use existing interpreter/venv — do not introduce a new one
3. **Dependencies added by SRDI:** only `gpt-4o-mini` via the existing LLM client; `langdetect`-class for R11 multilingual (confirm if already vendored)
4. **DB:** live SQLite — **back it up** before any migration (`05_DATA_SCHEMA_MIGRATION.md`)
5. **Config:** reuse existing config mechanism — every SRDI threshold is a config value with a default, never a buried literal
6. **Run baseline now:** `pytest --collect-only -q` (record count) + one golden research run before touching anything

---

## 2. PRE-FLIGHT CONFIRMATIONS

Run **once** before R1 work begins. Record answers in your branch's `SRDI_PREFLIGHT.md`.

### Schema & Models (R8)
- [ ] Migration harness: Alembic? custom runner? raw SQL on startup? → author M1–M6 in that format
- [ ] `SearchResult` timestamp: does `collected_at` exist? If absent, add in M3
- [ ] `external_signals`: has `created_at` and `raw_value_json`? If not, add additively
- [ ] Keyword deletion: does pipeline ever delete Keyword rows? If yes, switch RSV to soft-delete
- [ ] `DiscoveryOutcome`: confirm current columns so M6 only *adds* new SRDI columns

### Search & Collection (R1, R6)
- [ ] URL param shape: which WAVE_B shape does live Fiverr honor? (`&category_id=…&sub_category=…` vs `&filter=…`) → run R1.6.2 sweep, lock DEC-7
- [ ] Category ID currency: are the 9 hardcoded category IDs still valid vs DL-023?
- [ ] `collect_search_page_minimal`: exists? If not, build thin page-1 wrapper (no gig-detail/seller calls)

### Scoring (R4, R7, R5)
- [ ] Premium price source: `metadata_json.premium_price` or top `packages` price in `profitability.py`?
- [ ] Trends field keys: exact keys from `google_trends.py` (`trends_12mo_score`, `trends_slope`, `trends_related_queries`)?
- [ ] Reddit signature: batch `process_reddit_collection(keyword_ids=…)` or per-keyword?
- [ ] YouTube in demand: is YouTube currently *weighted* in `demand.py`? If yes, set weight→0 = scored change + re-baseline + DEC-6 log
- [ ] LLM client signature: find Stage-7 LLM caller; confirm async method name — reuse it, don't add new client
- [ ] Is discovery engine currently activated? If off, R6 is prerequisite to activation

### Dashboard & Alerting (R10)
- [ ] `alert.py` shape: has `alert_type` / `severity` / `metadata`? If not, add additively (coordinate R8)
- [ ] Dashboard framework/version: Streamlit with `st.badge`? Else markdown-chip fallback
- [ ] Run-summary printer: locate the module that prints end-of-run summary

### Testing & Maintenance (R9, R11)
- [ ] Record live baseline test count (≈3334); set regression floor = baseline + new tests
- [ ] Read `AGENT_EXECUTION_STRATEGY.md §7`; **append** REG-13…30, do not renumber existing entries
- [ ] `passes_recommendation_gates` (or equivalent): find entry point for first-rec gate hook
- [ ] Per-niche rolling history for monitors (≥3 prior runs): exists? If not, define history table

---

## 3. BRANCH & PR STRATEGY

**Branching:** `srdi/r{n}-{slug}` (e.g. `srdi/r8-schema`). Merge in dependency order: R8→R1→R3→R2; don't open R4/R6 branches until Tier-0 gate is green.

**PR checklist (every SRDI PR):**
- [ ] All new behavior behind a **config toggle** with a safe default (NULL/off = legacy behavior)
- [ ] Schema reads guarded — code tolerates NULL on every new column
- [ ] No destructive migration; migrations idempotent + reversible
- [ ] New/changed tests pass; REGs added to §7 if this PR closes one
- [ ] If scoring path changed (R4/R7): **golden-run diff** attached and explained
- [ ] Any spec-vs-code adaptation logged in `08_REGISTERS.md §6`
- [ ] Dashboard changes degrade gracefully (chip fallback) if framework feature missing

**CI gates:** (1) schema-presence assertion before R1–R7 tests; (2) full suite ≥ baseline floor; (3) LLM unit tests run with **mocked** client — no live calls

---

## 4. FILE-BY-FILE CHANGE LIST

### R8 — Schema (build first)
| File | Action | Change |
|---|---|---|
| `src/models/result_set_validation.py` | **NEW** | `ResultSetValidation` model; UNIQUE(keyword_id, run_id); relationship to Keyword |
| `src/models/gig.py` | Touch | +is_sponsored, is_zombie, zombie_score, zombie_signals, last_reviewed_at, relevance_flag, relevance_score, category_path (all nullable) |
| `src/models/search_result.py` | Touch | +search_strictness_used, result_set_relevance_score, ghost_market_flag, category_contamination_flag, sponsored_gig_count, organic_gig_count, pages_collected |
| `src/models/keyword_score.py` | Touch | +relevance_qualifier, trc_reliability_score, qualified_trc, sponsored_gigs_excluded, zombie_gigs_excluded, clean_gig_count |
| `src/models/keyword.py` | Touch | +discovery_needs_recollection, pre_validation_data, specificity_confidence |
| `src/models/external_signal.py` | Touch | +fiverr_relevance_qualifier, signal_quality_score |
| `src/models/discovery.py` | Touch | +is_invalid, is_contaminated, invalid_reason, relevance_score, pre_validation_passed |
| migrations/ | **NEW** | M1–M6 + M-ext, idempotent + reversible |

### R1 — Search URL
| File | Action | Change |
|---|---|---|
| `src/collection/search_url_builder.py` | **NEW** | `NICHE_CATEGORY_MAP` (9 niches, both URL shapes), `build_search_url`, `search_with_fallback` SUBCATEGORY→CATEGORY→NONE, check_category_mapping_freshness |
| `src/collection/fiverr_search.py` | Touch | Use `build_search_url`; store `search_strictness_used`, sponsored/organic counts, `pages_collected` |
| `src/scoring/demand.py` | Touch | Legacy-NONE −0.08 confidence deduction only (do NOT change `_normalize_count`) |

### R3 — Sponsored & Zombie
| File | Action | Change |
|---|---|---|
| `src/analysis/zombie_gig_detector.py` | **NEW** | `compute_zombie_score`, `is_zombie_gig`, date parsers, new-seller disambiguator |
| `src/collection/search_result_parser.py` | Touch | Review count: "10k+"→10000; pagination depth normalization |
| `src/collection/gig_detail.py` | Touch | Propagate `is_sponsored` from card; extract `last_reviewed_at`; call zombie detect |
| `src/scoring/competition.py` | Touch | Exclude sponsored from top-10; sponsored-fraction TRC bands (active until R4 ships) |
| `src/scoring/feasibility.py` | Touch | Zombie never sets review barrier |

### R2 — Relevance Validation (Stage 3.5)
| File | Action | Change |
|---|---|---|
| `src/analysis/result_set_validator.py` | **NEW** | `compute_gig_relevance` (4 signals), `validate_result_set`, `NICHE_VALIDATION_CONFIG` (9 niches), ghost detection |
| Stage 3.5 orchestrator | **NEW** | `run_stage_3_5_validation`; write RSV; update SearchResult; fail-soft per keyword |
| `src/scoring/demand.py` | Touch | TRC × `result_set_relevance_score` (multiplicative, AD-5) |
| `src/recommendations/eligibility.py` | Touch | Ghost = absolute hard block (AD-3) |

### R4 — Scoring Integrity
| File | Action | Change |
|---|---|---|
| `src/scoring/demand.py` | Touch | TRC **reliability single multiplier** (no stacking — DEC-3); emerging autocomplete = neutral 50; consume R7 trends qualifier |
| `src/scoring/competition.py` | Touch | Per-keyword profile when relevance<0.60; niche when ≥0.80; drop <0.40-relevance keywords from niche aggregate; price IQR filter |
| `src/scoring/opportunity.py` | Touch | × (0.5 + 0.5 × relevance) |
| `src/scoring/feasibility.py` | Touch | Clean-gig set (organic ∧ non-zombie ∧ relevance≠False) for level ratio + review barrier |
| `src/scoring/profitability.py` | Touch | Relevant/organic/non-zombie prices; IQR outlier filter |

### R5 — LLM Stage 7.5
| File | Action | Change |
|---|---|---|
| `src/analysis/llm_relevance_classifier.py` | **NEW** | Stage 7.5 trigger (band 0.35–0.75 ∧ final≥45); cap 50/run; cache `relevance_v1:{hash}`; CLEAN/MIXED/CONTAMINATED/GHOST_MARKET verdicts; apply-back |
| `src/analysis/competitor_profiler.py` | Touch | Synthesis pre-filter (<40% skip / 40–80% trim / ≥80% passthrough) |

### R6 — Discovery Gates
| File | Action | Change |
|---|---|---|
| `src/discovery/pre_validator.py` | **NEW** | `DiscoveryPreValidator`; page-1 dry-run; ghost/low-relevance/trc-too-low rejection |
| `src/discovery/orchestrator.py` | Touch | Specificity gate (0.65) + confidence gate (0.50); pre-validation loop; validated-only insert |
| `src/discovery/feedback.py` | Touch | Exclude `is_invalid` and `is_contaminated` outcomes from feedback |

### R7 — External Signals
| File | Action | Change |
|---|---|---|
| `src/collection/google_trends.py` | Touch | Qualifier: 0.65 base + slope(±0.10) + related-query buying + breadth penalty; clamp [0.20,0.95]; store on ExternalSignal |
| `src/collection/reddit_signals.py` | Touch | `compute_fiverr_buyer_intent_ratio`; qualified = raw × (0.40 + 0.60 × ratio) |
| Shared autocomplete classifier | **NEW** | `_classify_autocomplete_absence`: emerging→50 / not_searched→0 / unknown→20; R7-owned, R4-imported |
| `src/scoring/confidence.py` | Touch | freshness×relevance quality = √(f×r) |
| `src/scoring/demand.py` | Touch | YouTube weight→0 (DEC-6); consume qualified Trends/Reddit |

### R9 — Tests
| File | Action | Change |
|---|---|---|
| `tests/unit/*.py` | **NEW** | 10 test files (~100 unit tests, all LLM-mocked) |
| `tests/integration/*.py` | **NEW** | 3 integration files (~20 tests, transactional sessions) |
| `tests/fixtures/*.py` | **NEW** | `relevance_fixtures.py`, `contaminated_data_fixtures.py` |
| `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md §7` | Touch | **Append** REG-13…REG-30 (DEC-2, no renumbering) |

### R10 — Dashboard
| File | Action | Change |
|---|---|---|
| Dashboard module(s) | Touch | 7 integrity badges; Data Integrity tab (lazy-load); relevance filters; ghost hidden by default |
| Alert module | Touch | 6 alert types; niche-level aggregation; ghost per-keyword |
| Run-summary printer | Touch | Relevance/integrity block + immediate ghost prints |

### R11 — Edge Cases
| File | Action | Change |
|---|---|---|
| `src/analysis/monitors.py` | **NEW** | `CategoryFilterHealthMonitor`, `detect_sponsored_markup_change`, `detect_relevance_cliff(0.25)` |
| Validator | Touch | Negation-aware exclusion; multilingual neutral 0.50/include |
| Recommendation gate | Touch | First-rec quality gate as additional pre-check (DEC-8) |
| `selector_version_tracker.py` | **NEW** (if needed) | Track selector/test-id versions |

---

## 5. DEFINITION OF READY (per task)
- [ ] Epic's pre-flight items answered; hard dependencies merged and green
- [ ] Live field/method names confirmed; no open `[ASSUMPTION]` for this task
- [ ] Relevant AC and test names identified
- [ ] Config key + default defined for any new threshold

## 6. DO NOT LIST (hard constraints)
- Do **not** change `demand.py`'s `_normalize_count` (log10) or existing weights (except YouTube→0)
- Do **not** stack TRC multipliers (DEC-3 / R4.1.5)
- Do **not** hard-block anything except a confirmed ghost market (AD-3)
- Do **not** penalize legacy NULL rows retroactively (only NONE-strictness rows get R1.6 deduction)
- Do **not** introduce a new LLM client without confirming one isn't already present
- Do **not** renumber existing live regression entries (DEC-2)

---

*Cross-references: `08_REGISTERS.md` (OQ/decision dispositions), `05_DATA_SCHEMA_MIGRATION.md` (migrations), `11_AI_AGENT_HANDOFF.md` (agent-specific build order)*
