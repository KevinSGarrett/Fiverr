# Active Story AC/DoD Ledger (Cycle 012)

## Ledger Rules

- This ledger tracks only keys touched by Cycle 012 integration/governance work.
- "Advanced" means evidence moved at least one acceptance criterion forward.
- "Not advanced" means no new source-backed progress in this cycle.
- Product stories must not transition to `Done` until full source DoD is satisfied.

## Governance and Integration Tasks

- `SCRUM-254` (`In Progress`)
  - Advanced:
    - Full-board AC/DoD-first protocol reinforced in PM Pack updates.
    - Prompt depth and task volume guardrails reinforced (Cycle 012 governance updates).
    - PR/local discrepancy merge gate confirmed by PR #9 reconciliation evidence.
  - Not advanced / remaining:
    - Final closure depends on durable adoption evidence across later cycles.
    - Agent A report artifact still missing from branch.

- `SCRUM-250` (`In Progress`)
  - Advanced:
    - Cycle-to-story mapping and anti-governance-only drift rules strengthened.
    - Integration ledger now records all touched Cycle 012 keys with AC/DoD posture.
  - Not advanced / remaining:
    - Requires formal review signal before Done.

- `SCRUM-252` (`In Review`)
  - Advanced:
    - Cursor-agent Jira authority and enforcement surfaced in Cycle 012 protocol updates.
    - PR #9 discrepancy handling demonstrates governance expansion in practice.
  - Not advanced / remaining:
    - Final review/approval pending.

- `SCRUM-253` (`In Review`)
  - Advanced:
    - PR #9 discrepancy was resolved, validated, and merged with explicit evidence.
  - Not advanced / remaining:
    - No additional product-code scope added by Agent D in this pass.

## Product Stories (No Done transition in this pass)

- `SCRUM-212` (`In Review`)
  - Advanced: validation gate evidence reviewed.
  - Not advanced: full design-system source DoD completion not evidenced in this pass.

- `SCRUM-213` (`In Progress`)
  - Advanced: validation gate evidence reviewed.
  - Not advanced: full reusable-component source DoD completion not evidenced in this pass.

- `SCRUM-214` (`In Review`)
  - Advanced: merge-gate and PR stewardship evidence reviewed.
  - Not advanced: full opportunities-page source DoD completion not evidenced in this pass.

- `SCRUM-215` (`In Review`)
  - Advanced: branch/merge-governance evidence reviewed.
  - Not advanced: full keywords-page source DoD completion not evidenced in this pass.

- `SCRUM-219` (`In Review`)
  - Advanced: Codex-thread gate evidence reviewed.
  - Not advanced: full run-history source DoD completion not evidenced in this pass.

- `SCRUM-225` (`In Review`)
  - Advanced: CI/Codecov gate verification completed.
  - Not advanced: full query-layer source DoD completion not evidenced in this pass.

- `SCRUM-226` (`In Review`)
  - Advanced: PR body requirements codified in template update.
  - Not advanced: full export-system source DoD completion not evidenced in this pass.

- `SCRUM-227` (`In Review`)
  - Advanced: AC/DoD progress reporting requirement codified in template update.
  - Not advanced: full alert-system source DoD completion not evidenced in this pass.

- `SCRUM-228` (`In Review`)
  - Advanced: discrepancy reconciliation and app-entry evidence reviewed from prior cycle work.
  - Not advanced: full app-entry source DoD completion not evidenced in this pass.

- `SCRUM-231` (`In Progress`)
  - Advanced: full local validation commands executed on branch head.
  - Not advanced: full end-to-end source DoD completion not evidenced in this pass.

- `SCRUM-235` (`In Progress`)
  - Advanced: coverage gate and test evidence executed.
  - Not advanced: full coverage-audit source DoD closure beyond this cycle not evidenced.

## Evidence Sources

- Local validation run on `cycle/012/integration`:
  - `python -m ruff check .`
  - `python -m mypy src`
  - `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
  - `python run.py config-check`
  - `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle012.db`
  - `python run.py phase2-smoke`
  - `git status --short`
- Jira issue reads for all in-scope keys (statuses, AC, DoD text).
- Prior cycle reports:
  - `docs/cycle_reports/CYCLE_012_AGENT_B.md`
  - `docs/cycle_reports/CYCLE_012_AGENT_C.md`
