# CYCLE 070 — AGENT F HANDOFF

## Required Test Expansion (S7.6)

Add focused tests for `src/discovery/feedback.py`:

- `evaluate_discovery_results`
  - empty DB
  - partial scored outcomes
  - all gold outcomes
  - all misses
  - all misses below retire threshold
  - idempotent re-run (no duplicate outcomes, no duplicate alerts)
  - retire applied only when score <30
  - retire not applied for hits

- `build_feedback_summary`
  - no outcomes
  - single outcome
  - mixed outcomes across all discovery modes
  - mode buckets with zero outcomes handled gracefully
  - deterministic best/worst mode selection

- Derived field checks
  - `score_delta = actual_final_score - (hypothesis_confidence * 100)`
  - gold implies hit
  - monitor band (40-59) is neither hit nor miss

## Test Quality Gates

- >=30 new S7.6 tests.
- Preserve suite >=90% overall coverage.
- Keep test scope inside `tests/` plus F report doc.
