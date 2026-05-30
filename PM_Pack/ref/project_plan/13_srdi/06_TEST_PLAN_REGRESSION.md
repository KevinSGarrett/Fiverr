# 06 — SRDI Test Plan & Regression Register
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Source:** WAVE_J (authoritative). **Owning epic:** R9. **Tier:** 1 (continuous).  
**Target:** 120+ new tests (baseline ~3334 → ~3454+) · **18 permanent regressions: REG-13…REG-30**

---

## 1. TEST FILE MAP

```
tests/
├── unit/
│   ├── test_search_url_builder.py            (R1 — 8 tests)
│   ├── test_result_set_validator.py          (R2 — 14 tests)
│   ├── test_zombie_gig_detector.py           (R3 — 10 tests)
│   ├── test_sponsored_gig_filtering.py       (R3 — 8 tests)
│   ├── test_trc_reliability.py               (R4 — 8 tests)
│   ├── test_scoring_integrity_extensions.py  (R4 — 12 tests)
│   ├── test_llm_relevance_classifier.py      (R5 — 10 tests)
│   ├── test_discovery_gates.py               (R6 — 12 tests)
│   ├── test_external_signal_integrity.py     (R7 — 10 tests)
│   └── test_relevance_confidence_modifier.py (cross — 8 tests)
├── integration/
│   ├── test_stage_3_5_pipeline.py            (8 tests)
│   ├── test_scoring_with_relevance_filters.py(6 tests)
│   └── test_discovery_relevance_gates.py     (6 tests)
└── fixtures/
    ├── relevance_fixtures.py                 (clean/contaminated/ghost RSV + flagged-gig factory)
    └── contaminated_data_fixtures.py         (ghost + contamination card sets)
```

**Layers:**
- **Unit** — pure functions/classes with mocked DB/LLM. Fast (<30s for R1–R3 bundle)
- **Integration** — seeded transactional DB session, real scoring path, mocked network/LLM
- **Regression (REG-13…30)** — curated subset run every cycle; fast, deterministic, mocked

---

## 2. PERMANENT REGRESSION REGISTER (REG-13…REG-30)

Register in `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md §7`:

| REG | Test Name | Epic | Issues | Asserts |
|---|---|---|---|---|
| REG-13 | `test_fiverr_search_url_always_includes_category_filter_for_production_niches` | R1 | 1,4 | Every production niche emits category filter |
| REG-14 | `test_unconstrained_search_result_applies_demand_confidence_deduction` | R1 | 1 | NONE strictness → demand confidence deduction |
| REG-15 | `test_ghost_market_blocks_recommendation_generation_absolutely` | R2 | 6 | Ghost flag → no recommendation regardless of score |
| REG-16 | `test_trc_qualified_by_result_set_relevance_score_in_demand` | R2 | 5 | TRC scaled by result-set relevance in demand |
| REG-17 | `test_sponsored_gigs_never_included_in_competition_top10` | R3 | 4 | Sponsored excluded from competition top-10 |
| REG-18 | `test_zombie_gigs_never_used_in_feasibility_review_barrier` | R3 | 7 | Zombie never sets review barrier |
| REG-19 | `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent` | R3 | 4 | Sponsored-fraction TRC bands applied |
| REG-20 | `test_competition_profile_excludes_contaminated_keywords_in_niche_aggregate` | R4 | 11 | Niche profile drops <0.40-relevance keywords |
| REG-21 | `test_opportunity_score_qualified_by_result_set_relevance` | R4 | 16 | Opportunity ×(0.5+0.5×rel) |
| REG-22 | `test_price_outliers_excluded_from_competition_price_component` | R4 | 18 | IQR price outliers excluded |
| REG-23 | `test_llm_ghost_market_verdict_propagates_to_recommendation_block` | R5 | 6,12 | LLM GHOST_MARKET → recommendation blocked |
| REG-24 | `test_competitor_synthesis_skipped_when_relevance_fraction_below_40_percent` | R5 | 14 | Synthesis skipped <40% relevant |
| REG-25 | `test_ghost_market_discovery_outcome_marked_invalid_not_miss` | R6 | 13 | Ghost discovery → is_invalid, not is_miss |
| REG-26 | `test_contaminated_discovery_outcome_excluded_from_feedback_learning` | R6 | 13 | Contaminated excluded from feedback |
| REG-27 | `test_hypothesis_rejected_when_specificity_confidence_below_threshold` | R6 | 13 | Specificity <0.65 → rejected |
| REG-28 | `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score` | R7 | 10 | Emerging autocomplete → 50, not 0 |
| REG-29 | `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low` | R7 | 18 | Reddit qualified < raw at low intent |
| REG-30 | `test_trends_platform_qualifier_applied_before_demand_score_calculation` | R7 | 9 | Trends qualifier applied pre-demand |

---

## 3. KEY UNIT-TEST SPECIFICATIONS

### R1 — `test_search_url_builder.py` (8 tests)
- Subcategory filter present in URL; CATEGORY drops subcategory; NONE has no `category_id`
- Unknown niche → graceful unconstrained URL (no exception)
- Page 2 → `offset=20`; special chars encoded (C++ → C%2B%2B)
- All 9 production niches mapped; config returns required fields

### R2 — `test_result_set_validator.py` (14 tests)
- Exact-match keyword → relevant ≥0.60
- Cross-category gig title → False + `exclusion_terms_found`
- Generic title (no niche terms) → ≤0.30
- All-relevant set → relevance ≥0.80; zero-card → ghost + deduction −0.50
- Moderate contamination (0.40–0.70) → contamination flag; ghost deduction is the max
- Sponsored counted separately; all-9 validation configs present (≥3 core, ≥2 exclusion terms)

### R3 — `test_zombie_gig_detector.py` (10 tests)
- Zero-review + old account → zombie score ≥0.50
- Recent active account → NOT zombie
- **New seller Dec 2025 + 2 reviews → NOT zombie** (false-positive guard — critical)
- Old-no-advancement → zombie; threshold 0.50 boundary; snippet date extraction

### R5 — `test_llm_relevance_classifier.py` (10 tests)
- Skip clean (RSV 0.92); skip low-score (0.50/30); fire ambiguous (0.55/58)
- IRRELEVANT@pos → `Gig.relevance_flag=False`; GHOST_MARKET → RSV ghost flags + llm_validated
- Synthesis: skipped <40% / trimmed 40–80%; cost-cap 50 calls

### R6 — `test_discovery_gates.py` (12 tests)
- Prompt includes anti-contamination; specificity 0.50 rejected; 0.70 passes
- Pre-validator: ghost reject; 8-of-10 accept; TRC-too-low reject
- Ghost outcome → is_invalid + retired; 0.30 → contaminated + recollection
- Feedback excludes invalid+contaminated; orchestrator inserts validated-only (3 of 5)

### R7 — `test_external_signal_integrity.py` (10 tests)
- Trends qualifier ↑ on STRONGLY_RISING / ↓ on 1-word breadth penalty
- Reddit ratio: high(hiring posts) → qualified > raw; low(tutorials) → qualified < raw
- YouTube <10 → confidence deduction; autocomplete emerging→50 / not_searched→0
- Freshness×relevance: fresh+irrelevant low; fresh+relevant ≥0.90

---

## 4. INTEGRATION-TEST SPECIFICATIONS

### `test_stage_3_5_pipeline.py` (8 tests)
- 5 keywords → 5 RSV rows (one per keyword/run, UPSERT)
- Ghost → `SearchResult.ghost_market_flag=True`
- Gig relevance flags propagated from RSV `per_gig_relevance`
- Low relevance → confidence deduction reaches final score
- Backward-compat: absent RSV → identical to pre-initiative baseline

### `test_scoring_with_relevance_filters.py` (6 tests)
- Organic-only competition < full-set (sponsored Level-2 + organic Level-1)
- Feasibility barrier from organic gigs (50+), not zombie (0)
- Demand reflects `qualified_trc` (10000×0.40=4000)
- Ghost keyword (final 75 but flagged) → recommendation `eligible=False`

### `test_discovery_relevance_gates.py` (6 tests)
- 3 pass/2 fail pre-validation → exactly 3 inserted
- Ghost → `is_invalid`; feedback excludes contaminated; pre_validation_data stored on keyword

---

## 5. RUN COMMANDS

```bash
# Fast bundle (~40 tests, <30s)
pytest -q tests/unit/test_search_url_builder.py \
         tests/unit/test_result_set_validator.py \
         tests/unit/test_zombie_gig_detector.py \
         tests/unit/test_sponsored_gig_filtering.py --no-header

# Integrity regression bundle (REG pack)
pytest -q tests/unit/ tests/integration/ \
  -k "category_filter or ghost_market or zombie or sponsored or relevance or trc_reliability" \
  -v --no-header

# Full suite (target ~3454+)
pytest -q tests/ --no-header

# Baseline count check
pytest --collect-only -q | tail -1
```

---

## 6. REFERENCE DATA SETS

```python
KNOWN_GHOST_MARKET_EXAMPLES = [
    {"keyword": "fiverr gig seo",  "niche": "support_kb_readiness"},
    {"keyword": "automation",      "niche": "python_automation"},    # too broad
    {"keyword": "ai",              "niche": "ai_agent_development"},  # too generic
]
KNOWN_CLEAN_KEYWORD_EXAMPLES = [
    {"keyword": "Python Playwright web scraping script", "niche": "python_web_scraping"},
    {"keyword": "n8n workflow automation setup",         "niche": "workflow_automation"},
    {"keyword": "product requirements document writer",  "niche": "prd_ai_saas"},
]
```

Fixtures (`relevance_fixtures.py`):
- `clean_keyword_fixture`
- `ghost_market_rsv_fixture` (relevance=0.10, deduction=-0.50)
- `contaminated_rsv_fixture` (relevance=0.40, deduction=-0.15)
- `clean_rsv_fixture` (relevance=0.90, deduction=0.0)
- `make_gig_with_flags(is_sponsored, is_zombie, relevance_flag, relevance_score)`

---

## 7. CI GATES & DISCIPLINE

- **Baseline floor:** CI asserts collected count ≥ confirmed_baseline + ~120; a drop fails the build
- **Mock discipline:** no live LLM/network calls in CI; R5 verdicts injected; only prompt shape + apply logic asserted
- **Isolation:** each integration test uses its own `run_id` + transactional rollback; no cross-test state
- **Tier gates:** tier not "done" until all its REGs are green and registered (see `07_SEQUENCING_ROADMAP.md`)
- **Determinism:** REG pack must be fully deterministic (no time-of-day, no randomness without seed)

---

*Cross-references: `03_EPIC_BREAKDOWN_MASTER.md` (stories), `04_DOD_AND_ACCEPTANCE.md` (AC), `07_SEQUENCING_ROADMAP.md` (tier gates)*
