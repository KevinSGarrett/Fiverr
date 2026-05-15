# Active Story AC/DoD Ledger (Cycle 014)

## Ledger Rules

- This ledger is board-first and Jira-source-driven.
- "AC advanced" means at least one explicit acceptance-criteria bullet gained evidence this cycle.
- "DoD remaining" must reference unmet source scope from Jira story/task descriptions.
- Product stories do **not** move to `Done` without full source AC + DoD evidence.
- Cycle 014 work starts only after PR #10 merge-gate is green and merged/authorized.

## Cycle 014 Rows (Agent A)

| Jira Key | Jira Status (recommended) | Files / Evidence Scope | AC Advanced (Cycle 014) | DoD Remaining / Gaps | Tests / Validation | PR/Branch | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SCRUM-258` | In Progress | PR #10 gate checks; `docs/cycle_reports/CYCLE_014_AGENT_A.md`; this ledger | PR #10 merge gate executed and merged before product edits; Cycle 014 integration branch started from updated `develop`; no PM Pack rewrite performed in this pass. | Story remains open for full cycle governance closure and cross-agent completion. | `gh pr view 10 --json ...`; `gh pr checks 10`; `git fetch origin develop`; `git worktree add ... cycle/014/integration`; `git merge --ff-only origin/develop`. | PR #10; `cycle/014/integration` | Keep `In Progress`; hold Done until end-of-cycle governance closeout. |
| `SCRUM-225` | In Review | `src/dashboard/contracts.py`, `src/dashboard/queries.py`, `src/dashboard/query_layer.py`, `tests/unit/test_dashboard_queries.py` | Added typed query contracts, reusable query-layer boundary, sparse-data warnings/empty states, source+freshness metadata, filters/sorts, and pagination/truncation behavior with deterministic tests and docstrings. | Full product/story closure still needs integration into final dashboard pages and broader story acceptance evidence. | `python -m pytest -q tests/unit/test_dashboard_queries.py`; `python -m ruff check ...`; `python -m mypy src/dashboard src/orchestrator.py`. | `cycle/014/integration` | Keep `In Review`; do not transition to Done. |
| `SCRUM-228` | In Review | `src/dashboard/app.py`, `tests/unit/test_dashboard.py` | Hardened app entry with deterministic page registry, required-contract mapping, startup diagnostics, readiness severity helper, and import-safe app entry smoke output. | Full app runtime wiring and complete page implementation remain pending. | `python -m pytest -q tests/unit/test_dashboard.py`; `python -m ruff check ...`; `python -m mypy src/dashboard src/orchestrator.py`. | `cycle/014/integration` | Keep `In Review`; do not transition to Done. |
| `SCRUM-231` | In Progress | `src/orchestrator.py`, `tests/unit/test_orchestrator_helpers.py` | Added orchestrator dashboard-readiness handoff contract (stage status, warnings, blocked pages, next actions) and phase2-smoke metadata requirements for dashboard handoff fields. | Full end-to-end phase wiring and integration story closure remain open. | `python -m pytest -q tests/unit/test_orchestrator_helpers.py`; `python -m ruff check ...`; `python -m mypy src/dashboard src/orchestrator.py`. | `cycle/014/integration` | Keep `In Progress`; do not transition to Done. |
| `SCRUM-237` | In Progress | `src/dashboard/app.py`, `src/orchestrator.py`, `tests/unit/test_dashboard.py`, `tests/unit/test_orchestrator_helpers.py` | Startup diagnostics and readiness handoff contracts now expose warning counts, blocked pages, stage status, and next-action hints for monitoring-oriented visibility in smoke runs. | Full logging/monitoring pipeline implementation remains open beyond deterministic helper contracts. | `python -m pytest -q tests/unit/test_dashboard_queries.py tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`; `python -m pytest -q tests/unit/test_orchestrator.py`; `python run.py phase2-smoke`; `python -m ruff check ...`; `python -m mypy ...`. | `cycle/014/integration` | Keep `In Progress`; do not transition to Done. |
| `SCRUM-235` | In Progress | `tests/unit/test_dashboard_queries.py`, `tests/unit/test_dashboard.py`, `tests/unit/test_orchestrator_helpers.py` | Expanded deterministic unit coverage for query contracts, sparse-data behavior, app readiness, and orchestrator handoff logic. | Broader repository-wide coverage evidence and closure workflow still required by story scope. | `python -m pytest -q tests/unit/test_dashboard_queries.py tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`. | `cycle/014/integration` | Keep `In Progress`; do not transition to Done. |
| `SCRUM-214` | In Review | `src/dashboard/queries.py`, `tests/unit/test_dashboard_queries.py` | Opportunities query supports reusable status/niche/confidence filtering and score sorting descriptors with pagination and deterministic warning behavior. | Full opportunities page UI + acceptance artifacts remain open. | Targeted dashboard query tests and static checks above. | `cycle/014/integration` | Keep `In Review`; no Done recommendation. |
| `SCRUM-215` | In Review | `src/dashboard/queries.py`, `tests/unit/test_dashboard_queries.py` | Keywords query now returns standardized payloads with source/freshness metadata and sparse-data empty-state warnings. | Full keyword page UX story closure remains open. | Targeted dashboard query tests and static checks above. | `cycle/014/integration` | Keep `In Review`; no Done recommendation. |
| `SCRUM-219` | In Review | `src/dashboard/queries.py`, `tests/unit/test_dashboard_queries.py` | Run-history query now standardizes records + pagination/truncation metadata and deterministic limit/offset coercion behavior. | Full run-history page UX story closure remains open. | Targeted dashboard query tests and static checks above. | `cycle/014/integration` | Keep `In Review`; no Done recommendation. |
| `SCRUM-241` | In Progress | `src/dashboard/app.py`, `git status` hygiene checks, report evidence | Import safety preserved: dashboard module import does not auto-load Streamlit/network/secret reads; runtime behavior remains explicit-entry (`main`). | Full security/data-hygiene closure and branch finalization evidence still required at cycle completion. | Import-safety unit test + branch hygiene checks. | `cycle/014/integration` | Keep `In Progress`; no Done recommendation. |
| `SCRUM-254` | In Progress | PR #10 merge-gate evidence and cycle branch start evidence | Governance gate advanced by completing PR #10 merge and starting Cycle 014 from updated `develop`. | Story still depends on broader governance completion outside Agent A code scope. | PR gate commands listed above. | PR #10 | Keep `In Progress`. |
| `SCRUM-255` | In Progress | `docs/cycle_reports/CYCLE_014_AGENT_A.md` and cycle evidence chain | Cycle 014 Agent A report artifact created with command evidence, touched files, and handoff guidance. | Cross-agent completion and final reconciliation still required. | Report + validation evidence commands. | `cycle/014/integration` | Keep `In Progress`. |

## Cycle 014 Rows (Agent B)

| Jira Key | Jira Status (recommended) | Files / Evidence Scope | AC Advanced (Cycle 014) | DoD Remaining / Gaps | Tests / Validation | PR/Branch | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SCRUM-212` | In Review | `src/dashboard/design.py`, `src/dashboard/components.py`, `src/dashboard/app.py`, `tests/unit/test_dashboard.py` | Added deterministic design tokens (severity labels/icons, confidence text rules, accessible state labels) and reusable state/badge conventions used by dashboard payload contracts. | Visual QA review and full Streamlit rendering integration still required by source DoD; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass (ruff/mypy/pytest-cov/config-check/foundation-gate/phase2-smoke). | `cycle/014/integration` | Keep `In Review`; continue app-level visual integration evidence. |
| `SCRUM-213` | In Review | `src/dashboard/components.py`, `tests/unit/test_dashboard.py` | Implemented reusable card contracts (metric/status/ranking/evidence), reusable table/list descriptor (columns/rows/sort/warnings/empty/source/freshness), and standardized state descriptors (loading/empty/warning/error/blocked/ready). | Full page-level UX rendering and QA consistency checks remain open; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`; extend into final page render layer. |
| `SCRUM-214` | In Review | `src/dashboard/opportunities.py`, `src/dashboard/pages.py`, `src/dashboard/app.py`, `tests/fixtures/dashboard/factories.py`, `tests/unit/test_dashboard.py` | Built opportunities page payload core with filter/sort passthrough, ranking cards, table payload, source/freshness metadata, deterministic empty states, and opportunity-to-keyword cross-link ids. | Full UI drill-in behavior and real-data smoke acceptance evidence remain open; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`; coordinate with final UI layer. |
| `SCRUM-215` | In Review | `src/dashboard/keywords.py`, `src/dashboard/pages.py`, `src/dashboard/app.py`, `tests/fixtures/dashboard/factories.py`, `tests/unit/test_dashboard.py` | Built keywords payload core with cluster context handling, confidence text, sorting/filtering support, source/freshness context, deterministic sparse-data warnings, and opportunity linkage references. | Full keyword UI flows and final clustering story closure remain open; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`; maintain dependency note on `SCRUM-157`. |
| `SCRUM-219` | In Review | `src/dashboard/run_history.py`, `src/dashboard/pages.py`, `src/dashboard/app.py`, `tests/fixtures/dashboard/factories.py`, `tests/unit/test_dashboard.py` | Built run-history payload core with run ids, statuses, stages, durations, warning/failure summaries, next-actions, and deterministic severity mapping (`pass/warning/failed/blocked/unknown/skipped`). | Full run-history UI smoke and end-to-end completion evidence remain open; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`; continue integration with app shell. |
| `SCRUM-228` | In Review | `src/dashboard/app.py`, `src/dashboard/pages.py`, `tests/unit/test_dashboard.py` | Added import-safe product page payload registry integration (`get_product_page_payloads`) with deterministic registry-level safe-empty/ready state diagnostics. | Full app startup UX and runtime wiring still pending beyond payload contracts; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`. |
| `SCRUM-227` | In Review | `src/dashboard/design.py`, `src/dashboard/run_history.py`, `tests/unit/test_dashboard.py` | Added reusable severity mapping and display tokens to keep status/alert semantics consistent across payload components. | Full alert behavior integration and operational workflow checks still pending; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Review`. |
| `SCRUM-157` | In Progress | `src/dashboard/keywords.py`, `tests/unit/test_dashboard.py` | Added deterministic dependency handling (`cluster not available yet`) so dashboard payloads remain stable when clustering outputs are incomplete. | Core clustering delivery is outside this scope and remains open; do not mark Done. | `python -m pytest -q tests/unit/test_dashboard.py`; full validation block pass. | `cycle/014/integration` | Keep `In Progress` until analysis cluster implementation closes. |
| `SCRUM-235` | In Progress | `tests/unit/test_dashboard.py`, `tests/fixtures/dashboard/factories.py`, `tests/fixtures/dashboard/__init__.py`, `tests/fixtures/__init__.py`, `tests/__init__.py` | Added deterministic fixture factories and expanded dashboard unit coverage for component contracts, page payloads, severity rules, and registry integration. | Story closure still depends on end-of-cycle integrated coverage evidence and final PR checks. | `python -m pytest -q tests/unit/test_dashboard.py` (36 passed); `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90` (pass, 93.16%). | `cycle/014/integration` | Keep `In Progress`. |
| `SCRUM-258` | In Progress | This ledger; `docs/cycle_reports/CYCLE_014_AGENT_B.md`; Jira comments for touched stories | Agent B evidence chain updated with AC/DoD progress, validation results, and Jira issue comments for touched dashboard stories/dependencies. | Final cross-agent cycle reconciliation remains open. | Full validation block pass; report + Jira evidence updates. | `cycle/014/integration` | Keep `In Progress` until cycle closeout. |

## Cycle 014 Validation Evidence

- Targeted app-entry commands:
  - `python -m pytest -q tests/unit/test_dashboard_queries.py tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`
- Targeted Agent B dashboard commands:
  - `python -m pytest -q tests/unit/test_dashboard.py` (`36 passed`)
- Full validation block:
  - `python -m ruff check .` (`pass`)
  - `python -m mypy src` (`pass`)
  - `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90` (`pass`, total coverage `93.16%`)
  - `python run.py config-check` (`pass`)
  - `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle014.db` (`pass`)
  - `python run.py phase2-smoke` (`pass`)
- Additional integration checks:
  - `python -m pytest -q tests/unit/test_orchestrator.py`
  - `python run.py config-check`
  - `python run.py phase2-smoke`
- Continuation pass evidence (Agent B runtime activation):
  - Enabled product pages in `src/dashboard/navigation.py` (`opportunities`, `keywords`, `run_history`) and updated app runtime render summaries in `src/dashboard/app.py`.
  - Updated `tests/unit/test_dashboard.py` expectations for activated product pages and `main()` product payload smoke output.
  - Re-ran full validation block successfully (`coverage 93.18%`).
- Merge-gate governance checks:
  - `git status --short --branch`
  - `git fetch origin`
  - `git checkout develop`
  - `git pull`
  - `git checkout cycle/014/integration`
  - `git merge-base --is-ancestor origin/develop HEAD`
  - `gh pr checks 10`
  - `gh api graphql ... pullRequest(number:10) ... reviewThreads ... isResolved`

## Security and Branch Safety Evidence (Cycle 014)

- `.env` ignore/staging check:
  - `git status --short`
- Branch safety:
  - Active implementation branch is `cycle/014/integration`, based on merged `develop`.
  - No `main` branch operations were executed.
