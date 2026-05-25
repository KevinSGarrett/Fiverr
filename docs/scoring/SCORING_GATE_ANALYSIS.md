# Scoring Gate Analysis - Cycle 039

Date: 2026-05-25  
Branch: `cycle/039/integration`  
Database: `sqlite:///data/cycle037_live.db`

## Baseline Inputs

- Agent A checkpoint SHAs: `03c1d5d48e70bba29783a52b52cf300a65c0cee2`, `c2e3f0d`, `25097bd`, `e09c954`
- Jira keys: `SCRUM-531` (cycle control), `SCRUM-532` (scoring)
- Unit baseline from Agent A: `2712 passed`
- Codex parser regressions baseline: nested price + zero review preservation `PASS` (`3 passed`)

## Tag Threshold Logic

Thresholds are aligned in `config.yaml` and `src/scoring/pipeline.py`:

- `STRONG_GO`: `>= 80`
- `CONDITIONAL_GO`: `>= 60`
- `MONITOR`: `>= 40`
- `CAUTION`: `>= 20`
- `PASS`: `< 20`

Recommendation auto-generation is gated to `STRONG_GO` and `CONDITIONAL_GO`.

## Top-5 Score Trace (Before Fixes)

From Agent A Task 6.1 and DB verification:

1. `what is automation support` - `18.54` (`PASS`)
2. `support automation tools` - `18.41` (`PASS`)
3. `best customer support automation tools` - `17.42` (`PASS`)
4. `service automation tools` - `17.12` (`PASS`)
5. `customer support automation tools` - `16.12` (`PASS`)

Per-component pattern (all top keywords):

- `demand_score`: present, low (`~4.9` to `14.0`)
- `competition_score`: present (`46.44`)
- `opportunity_score`: present (`~24.4` to `29.8`)
- `intent_score`: present (`47.14` to `79.29`)
- `feasibility_score`: `None`
- `profitability_score`: `None`
- `weakness_score`: `None`

## Root Cause Table

| Root Cause | Impact on Score | Fixable in Cycle 039? | Fix Type | Evidence |
| --- | --- | --- | --- | --- |
| Null Stage 4 prices in detail-collected gigs | Profitability remained `None` for top keyword set | Yes | Live re-collection + parser fix | Before: `2/20` detail gigs with price, after: `19/20` |
| Parser missed JSON-LD `lowPrice`/`priceSpecification` variants | Stage 4 extracted `None` prices even after nested-price support | Yes | Code fix in parser | Re-collection run 1: `0/18` improved; run 2 after fix: `17/18` improved |
| Stage 11 required `gig_quality_scores` rows that were never populated | `gig_quality_analyses` stayed `0`; weakness inputs absent | Partially | Stage 11 fallback to gig rows | `gig_quality_analyses` moved `0 -> 20` (support niche) |
| Confidence modifier deductions | Composite multiplied by low confidence (`0.2111` to `0.5833`) | Partially | Data enrichment required | Typical top keyword confidence `0.5833`; many keywords `0.2111` |
| Demand signal sparsity | Demand stayed low for top keywords | Partially | Stage 3/Signals expansion required | Top demand values `4.92-14.02`; top keywords have only one search row each |
| Search-result normalization gap (`rank`/`gig_id` null in all rows) | Feasibility/Profitability/Weakness remained unfed (`None`) during scoring | No (full fix) | Pipeline/data-model repair | `search_results_rank_null=14`, `search_results_gig_id_null=14`, `search_results_with_gig_cards_blob=14` |
| Keyword coverage gap | Most keywords scored as zero due no upstream records | No (full fix) | Collection breadth + linking | `97` keywords, only `12` with search rows, `10` with gigs |

## Fixes Applied in Cycle 039

1. Updated `src/collection/gig_detail.py` price extraction logic:
   - Added support for `lowPrice`, `minPrice`, `highPrice`, `maxPrice`
   - Added nested `priceSpecification` extraction
   - Added/updated regressions in `tests/unit/test_gig_detail.py`
2. Ran targeted Stage 4 live re-collection for all detail-collected null-price gigs:
   - Targets: `18`
   - Improved: `17`
   - Failures: `0`
   - Remaining null detail URL: one agency profile URL (non-standard gig page)
3. Updated Stage 11 load path in `src/analysis/gig_quality_rubric.py`:
   - Switched to left join for `gig_quality_scores`
   - Added fallback query from `gigs` when `search_results` linkage is absent
   - Added tests in `tests/unit/test_gig_quality_rubric.py`
4. Re-ran Stage 11:
   - `gig_quality_analyses`: `0 -> 20`
5. Re-ran full scoring:
   - `97` keywords rescored
   - Tags remained all `PASS`

## Top-5 Score Trace (After Fixes)

Latest scoring run (last 97 rows):

1. `what is automation support` - `18.54`, confidence `0.5833`, tag `PASS`
2. `support automation tools` - `18.41`, confidence `0.5833`, tag `PASS`
3. `best customer support automation tools` - `17.42`, confidence `0.5833`, tag `PASS`
4. `service automation tools` - `17.12`, confidence `0.5833`, tag `PASS`
5. `customer support automation tools` - `16.12`, confidence `0.5833`, tag `PASS`

Component pattern remained unchanged for top-5: feasibility/profitability/weakness still `None` in scored payload.

## Composite Histogram (After Fixes)

Latest run (`97` keywords, final score buckets):

- Min: `0.00`
- Max: `18.54`
- Avg: `1.72`
- Buckets:
  - `0-4`: `87`
  - `15-19`: `10`
- Tags: `['PASS']`

Interpretation: scores are far below `CONDITIONAL_GO` (`60`) and `STRONG_GO` (`80`), indicating upstream data/normalization gaps rather than small threshold tuning.

## Recommendation Outcome

- Before Cycle 039 fixes: effectively blocked (no qualifying tags)
- After fixes and full rerun:
  - `run.py recommendations-only` output:
    - `eligible=0`
    - `gates_passed=0`
    - `generated=0`

## Remaining Gaps (Cycle 040 Candidate Work)

1. Normalize Stage 3 outputs into score-ready records:
   - populate per-gig `search_results.rank`, `search_results.gig_id`, `search_results.result_url`
2. Ensure Stage 7/11 bridge is complete:
   - produce `gig_quality_scores` consistently for all scored niches
3. Expand collection breadth:
   - more keywords with search rows and linked gigs (current nonzero scoring coverage is `10/97`)
4. Re-run scoring after normalization, then reassess thresholds only if scores cluster near `60`
5. Re-run recommendations after first `CONDITIONAL_GO` / `STRONG_GO` appears
