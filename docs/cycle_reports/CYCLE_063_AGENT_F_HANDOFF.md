# CYCLE 063 — AGENT F HANDOFF

## Zone Contract (Strict)
- F runs only after C issues GO.
- F may modify:
  - `tests/` (unit tests only)
  - `docs/cycle_reports/CYCLE_063_AGENT_F.md`
- F must not modify `src/`.

## Mission
- Coverage uplift focused on pages modified by B for 9D widgets.
- Target coverage floors:
  - `src/dashboard/pages/opportunities.py` >= 70%
  - `src/dashboard/pages/keywords.py` >= 70%
  - `src/dashboard/pages/recommendations.py` >= 70%
  - `src/dashboard/pages/run_history.py` >= 70%

## Required Test Additions
- Empty-data path tests for pricing widgets (no `PriceAnalysis` rows, graceful render).
- With-data path tests for pricing widgets.
- Pricing LLM task `None` return test when no price-analysis data exists.
- Keep all new tests in `tests/unit/` only (not `tests/integration/`).

## Reporting Requirement
- Report per-file coverage before vs after uplift.
- Flag any target still below threshold with precise remaining gaps.
