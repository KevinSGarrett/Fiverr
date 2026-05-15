# Cycle 008 - Agent D (Dashboard, Reporting, Export, Steward)

## Scope and ownership

- Jira stories in scope: `SCRUM-212`, `SCRUM-213`, `SCRUM-228`, `SCRUM-226`, `SCRUM-250`.
- Code areas: `src/dashboard/`, `src/reports/`, `src/exports/`, `tests/unit/test_dashboard.py`, `tests/unit/test_reports.py`.
- Steward expectations: full local validation, Jira mapping visibility, governance evidence contracts, and PR handoff readiness.

## Task D1 - Dashboard governance/status presentation model (`SCRUM-212`, `SCRUM-213`)

Implemented import-safe governance presentation helpers in `src/dashboard/app.py`:

- Added deterministic category order for:
  - `local_parity`
  - `github_actions`
  - `codecov_project`
  - `codecov_patch`
  - `codex_disposition`
  - `jira_mapping`
  - `merge_readiness`
- Added `build_governance_presentation_state(...)` that returns plain dictionaries (no Streamlit dependency).
- Added normalization where missing/blank status becomes `unknown` with `warning` severity.
- Updated `get_governance_status_state()` to expose all categories and include severity for UI rendering.

Test evidence:

- `tests/unit/test_dashboard.py` now verifies all categories are rendered.
- Missing status fallback behavior (`unknown` + `warning`) is covered.
- Streamlit import safety at module import time remains enforced.

## Task D2 - Jira mapping reporting placeholder (`SCRUM-213`, `SCRUM-228`, `SCRUM-250`)

Implemented Jira mapping helper in `src/reports/placeholders.py`:

- Added `build_jira_mapping_table(rows, output_format="dict"|"markdown")`.
- Supports deterministic dict output for programmatic use.
- Supports Markdown table output for PR/report rendering.
- Enforces Jira-key presence per row unless `not_applicable_reason` is explicitly provided.

Test evidence in `tests/unit/test_reports.py`:

- Valid mapping renders in dict and Markdown forms.
- Missing Jira key without `not_applicable_reason` fails with validation error.
- Not-applicable row with explicit reason is accepted.

## Task D3 - Export manifest governance evidence fields (`SCRUM-226`, `SCRUM-250`)

Extended export manifest evidence in `src/exports/manifest.py` and `src/exports/placeholders.py`:

- Added manifest metadata fields:
  - `jira_keys`
  - `github_pr_number`
  - `codex_threads_resolved`
  - `codecov_project_status`
  - `codecov_patch_status`
  - `coverage_percent`
- Added `build_governance_manifest_metadata(...)` for deterministic normalization and validation.
- Added guardrails for secret-like values in Jira/status fields.
- Added validation for status values, PR number, thread count, and coverage percent range.

Test evidence in `tests/unit/test_reports.py`:

- Manifest serialization includes required governance evidence fields.
- Secret-like values are rejected.
- Coverage percent out-of-range is rejected.

## Task D4 - Required validation bundle

Executed and passed:

- `python -m ruff check .`
- `python -m mypy src`
- `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90` (coverage: 93.09%)
- `python run.py config-check`
- `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle008.db`
- `python run.py phase2-smoke`

Cleanup completed:

- Removed generated `coverage.xml`.
- Removed generated `data/foundation_gate_cycle008.db`.

## Jira mapping coverage notes for steward PR

Final steward PR must include both governance and product-story mapping in one table, including at least:

- `SCRUM-250`
- `SCRUM-154`
- `SCRUM-156`
- `SCRUM-149`
- `SCRUM-164`
- `SCRUM-163`
- `SCRUM-212`
- `SCRUM-213`
- `SCRUM-228`
- `SCRUM-226`

## Blockers

- No implementation blockers encountered during Agent D owned work.
