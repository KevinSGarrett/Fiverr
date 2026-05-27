# State Snapshot — Cycle 044

Updated: 2026-05-26 | Agent A setup complete

## Verified Repository State

- Canonical working directory: `C:\Fiverr\Fiverr`
- Active branch: `cycle/044/integration`
- Tests: `2936` | Coverage: `95.61%` | PR #49 and PR #50: MERGED
- Current local `tests/unit` baseline: `2944 passed`
- Config safety: `collection.scrapfly.enabled=false` (verified)
- Worktrees: `1` entry only

## Score Baseline

Source: `sqlite:///data/cycle037_live.db` best `keyword_scores` row.

- Best keyword: `kw=96`
- Final score: `44.22`
- Raw composite: `46.53`
- Derived confidence modifier from stored score row: `0.95`
- Gap to `CONDITIONAL_GO (60)`: `15.78`
- Tags: `PASS=1954`, `CAUTION=73`, `MONITOR=3`

## TRC Baseline (Task 5.3)

- `SearchResult: total=103 with_trc=31 null_trc=72`
- Sample rows with TRC:
  - `kw=1 rank=None trc=21426`
  - `kw=1 rank=None trc=21426`
  - `kw=3 rank=None trc=473`
  - `kw=4 rank=None trc=208`
  - `kw=6 rank=None trc=55`

## Seller Profile Baseline (Task 5.4)

- `Sellers: total=195 with_level=195`

## kw=96 Confidence Context (Task 5.5)

Direct `ConfidenceScoreModifier.calculate_with_breakdown(keyword_id=96, run_context=None)` output:

- `kw96 CM=0.125`
- `data_completeness_ratio: 0.25`
- `data_freshness_score: 1.0`
- `source_diversity_score: 0.25`
- `llm_analysis_completion_ratio: 1.0`
- `base_modifier: 0.475`
- Active deductions:
  - `missing_gig_detail: -0.2`
  - `missing_seller_profiles: -0.1`
  - `missing_reddit_signals: -0.05`
- `deduction_total: -0.35`
- `remaining_modifier: 0.125`
