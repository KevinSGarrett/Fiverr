# CYCLE 062 — AGENT F HANDOFF

Post-merge placeholder (do not replace until D finalizes squash): `[C062_SQUASH_SHA]`

## Execution Order and Zone

- F starts only after C returns GO.
- F zone is `tests/` plus F report only.
- F must not modify `src/`, migrations, config, or model implementation files.

## Mission: Coverage Uplift

Raise low dashboard-page coverage to >=70% for each target:

- `src/dashboard/pages/opportunities.py` (baseline ~52%)
- `src/dashboard/pages/keywords.py` (baseline ~57%)
- `src/dashboard/pages/recommendations.py` (baseline ~50%)
- `src/dashboard/pages/run_history.py` (baseline ~47%)

## Secondary Mission (Conditional)

If B’s new pricing files land below 80% coverage, add targeted tests for those modules:

- `src/pricing/analysis.py`
- `src/pricing/new_seller_pricing.py`
- any additional B-created pricing module with <80% coverage

## Deliverables

- New/updated tests under `tests/` only.
- `docs/cycle_reports/CYCLE_062_AGENT_F.md` with:
  - before/after coverage by targeted file
  - list of tests added
  - final command used
  - F commit SHA

## Gate Notes

- Do not alter production logic to force coverage.
- Validate behavior, edge cases, and empty-state rendering contracts.
- Keep coverage command aligned with project gate (`--cov=src` once).
