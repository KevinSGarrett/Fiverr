# Active Story AC/DoD Ledger (Cycle 013)

## Ledger Rules

- This ledger is board-first and Jira-source-driven.
- "AC advanced" means at least one explicit acceptance-criteria bullet gained evidence this cycle.
- "DoD remaining" must reference unmet source scope from Jira story/task descriptions.
- Product stories do **not** move to `Done` without full source AC + DoD evidence.
- While PR #10 is open, updates remain on `cycle/012/integration`.

## Cycle 013 Rows (Agent D)

| Jira Key | Jira Status (live read) | Files / Evidence Scope | AC Advanced (Cycle 013) | DoD Remaining / Gaps | Tests / Validation | PR | Next Action |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `SCRUM-256` | In Progress | `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_013.md`, `docs/jira/ACTIVE_STORY_DOD_LEDGER.md`, `docs/cycle_reports/CYCLE_013_AGENT_D.md`, PR #10 live state | Cycle 013 board-first audit refreshed with conservative closure gate and no-main/no-secret evidence. | Keep open until governance closure dependencies (`SCRUM-255`) are resolved and accepted. | `gh pr view 10 ...`; `gh api graphql ... reviewThreads`; full local validation block run. | #10 | Keep `In Progress`; continue Jira-first execution and closure audit. |
| `SCRUM-255` | To Do | `docs/cycle_reports/CYCLE_012_AGENT_A.md`, `docs/cycle_reports/CYCLE_013_AGENT_A.md`, this ledger, Cycle 013 audit addendum | Missing Agent A artifact now exists as formal disposition artifact. | Jira-side acceptance/disposition confirmation still not complete; do not close. | Live Jira read for `SCRUM-255`; cross-check with Agent A/B reports. | #10 | Keep `To Do`; block `SCRUM-254` Done until accepted. |
| `SCRUM-254` | In Progress | `PM_Pack/*` governance evidence via Agent C report + Cycle 013 board audit/ledger | Governance protocol AC remains advanced (full-board protocol + prompt-depth guardrails retained). | Not Done while `SCRUM-255` remains open and explicit closure decision is absent. | Live Jira read + PM Pack/report traceability review. | #10 | Keep `In Progress`. |
| `SCRUM-252` | In Review | `PM_Pack/03_cursor_agent_system/PROMPT_TEMPLATE.md`, `PM_Pack/09_templates/AGENT_PROMPT_C.md`, Agent C report | Prompt governance and Jira-operation rule evidence retained and audited in cycle docs. | Final acceptance/closure pending governance sign-off. | `rg` path/threshold checks; live Jira read. | #10 | Keep `In Review`. |
| `SCRUM-250` | In Review | `docs/jira/ACTIVE_STORY_DOD_LEDGER.md`, `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_013.md` | Cycle-to-story mapping and anti-governance-only enforcement applied in this cycle audit. | Needs explicit closure decision after sustained cycle compliance. | Live Jira read + updated ledger rows for product + governance keys. | #10 | Keep `In Review`. |
| `SCRUM-212` | In Review | `src/dashboard/app.py` descriptors/context, cycle reports, Jira story source | No new full implementation; only related diagnostic scaffolding context exists. | Source scope S9.1 tasks (`9.1.1-9.1.7`) and child-task/waiver closure not evidenced complete. | Regression suite + dashboard targeted tests passed. | #10 | Remain `In Review`; no Done. |
| `SCRUM-213` | In Progress | `src/dashboard/app.py` diagnostics context, Jira source | No full reusable-component build completion evidence in this pass. | Source scope S9.2 tasks (`9.2.1-9.2.11`) still incomplete. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Progress`. |
| `SCRUM-214` | In Review | `src/dashboard/app.py` page descriptors, Jira source | Placeholder descriptor coverage exists; no full opportunities-page implementation closure evidence. | Source scope S9.3 tasks (`9.3.1-9.3.7`) incomplete; child-task/waiver evidence required. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-215` | In Review | `src/dashboard/app.py` page descriptors, Jira source | Placeholder keyword page descriptor remains; no full feature closure evidence. | Source scope S9.4 tasks (`9.4.1-9.4.8`) incomplete. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-219` | In Review | `src/dashboard/app.py` run-history descriptor, Jira source | Run-history placeholder descriptors exist. | Source scope S9.7 tasks (`9.7.1-9.7.5`) not fully evidenced complete. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-225` | In Review | `src/dashboard/app.py` query-layer descriptor contract, Jira source | Query-layer contract scaffolding present; no full query-layer DoD completion evidence. | Source scope S9.11 tasks (`9.11.1-9.11.8`) still open. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-226` | In Review | `src/dashboard/app.py` export descriptor contract, Jira source | Export descriptor contract still placeholder-level. | Source scope S9.12 tasks (`9.12.1-9.12.8`) incomplete. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-227` | In Review | `src/dashboard/app.py` alert descriptor contract, Jira source | Alert descriptor and normalization scaffolding present. | Source scope S9.13 tasks (`9.13.1-9.13.6`) incomplete. | Regression suite + dashboard targeted tests passed. | #10 | Keep `In Review`; no Done. |
| `SCRUM-228` | In Review | `src/dashboard/app.py`, `src/orchestrator.py`, `tests/unit/test_dashboard.py`, `tests/unit/test_orchestrator_helpers.py` | App-entry smoke state, page registration diagnostics, safe empty-state diagnostics, and startup/smoke test evidence advanced. | Full source S9.14 scope (`9.14.1-9.14.5`) still needs complete runtime behavior and closure evidence. | `pytest -q tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`; `pytest -q tests/unit/test_cli.py -k dashboard`; `python run.py dashboard --mode local`; `python run.py phase2-smoke`. | #10 | Keep `In Review`; not Done. |
| `SCRUM-231` | In Progress | `src/orchestrator.py` dashboard stub diagnostics and cycle smoke evidence | Integration/governance smoke behavior improved via dashboard app-entry checks in orchestrator path. | Full S10.1 end-to-end pipeline orchestration scope (`10.1.1-10.1.6`) not complete. | Dashboard CLI and phase2 smoke checks pass; full test suite pass. | #10 | Keep `In Progress`. |
| `SCRUM-235` | In Progress | Full test + coverage evidence in current branch run | Coverage AC evidence reconfirmed in Cycle 013 run (`93.12%`). | S10.5 full coverage-gap remediation workflow still open beyond reporting evidence. | `pytest --cov ... --cov-fail-under=90` pass; `coverage.xml` generated (unstaged). | #10 | Keep `In Progress`. |

## Cycle 013 Validation Evidence

- Targeted app-entry commands:
  - `python -m pytest -q tests/unit/test_dashboard.py tests/unit/test_orchestrator_helpers.py`
  - `python -m pytest -q tests/unit/test_cli.py -k dashboard`
  - `python run.py dashboard --mode local`
  - `python run.py phase2-smoke`
- Full validation block:
  - `python -m ruff check .`
  - `python -m mypy src`
  - `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
  - `python run.py config-check`
  - `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle013.db`
  - `python run.py phase2-smoke`
- Governance/path checks:
  - `rg -n "HYDRATION_HEADER.md|STATE_SNAPSHOT.md" PM_Pack/00_index/MASTER_INDEX.md`
  - `rg -n "src/scoring/|tests/unit/test_scoring.py|Conditional scoring validation|Path preflight" PM_Pack/09_templates/AGENT_PROMPT_C.md`
  - `rg -n "50 words|100 words" PM_Pack/03_cursor_agent_system/PROMPT_TEMPLATE.md`

## Security and Branch Safety Evidence (Cycle 013)

- `.env` ignore/staging check:
  - `git check-ignore .env`
  - `git status --short -- .env coverage.xml data .pytest_cache .ruff_cache`
- Branch safety:
  - Active branch remained `cycle/012/integration`.
  - No `main` branch operations were executed.
