# Jira Cycle-to-Story Mapping Protocol

Version: Cycle 008 corrective rule

## Non-negotiable rule

Every PM cycle must map changed files and assigned agent tasks to exact Jira product story/task tickets before the final PM response is sent. Governance-only Jira updates are not acceptable when product code, tests, docs, dashboard, reporting, exports, or workflows changed.

## Required sequence every cycle

1. Collect changed files from the branch or PR.
2. Group files by ownership path:
   - `src/collection/`, collection tests, collection docs -> Epic 02 Collection stories.
   - `src/analysis/`, analysis tests -> Epic 03 Analysis stories.
   - `src/scoring/`, scoring tests -> Epic 04 Scoring stories.
   - `src/recommendations/`, recommendation tests -> Epic 05 Recommendation stories.
   - `src/pricing/`, pricing tests -> Epic 06 Pricing stories.
   - `src/discovery/`, discovery tests -> Epic 07 Discovery stories.
   - `src/playbook/`, playbook tests -> Epic 08 Playbook stories.
   - `src/dashboard/`, `src/reports/`, `src/exports/`, dashboard/report/export tests -> Epic 09 Dashboard and Reporting stories.
   - `src/orchestrator.py`, `run.py`, end-to-end tests -> Epic 10 Integration, unless the change clearly belongs to a domain epic.
   - `.github/`, `codecov.yml`, PR templates, governance docs -> PM/GitHub/Jira governance tickets.
3. Search Jira for each affected epic/story area using JQL.
4. For every touched Jira key, add a cycle comment that includes branch, PR, changed files, validation evidence, Codex/CI/Codecov status, completion confidence, and whether the story is partial or full.
5. Transition statuses using this rule:
   - To Do -> In Progress when work starts or merged partial implementation exists.
   - In Progress -> In Review when PR is open and all required checks are passing.
   - In Review -> Done only after merge and full source DOD is satisfied.
   - Never mark full story Done for partial scaffold/fixture/prep work.
6. Include a Jira mapping table in the PM response and PR body.
7. If a changed file group is intentionally not mapped to a Jira product story, document `not_applicable_reason`.

## PM reply gate

The PM reply is rejected if it updates only governance tickets while product files changed.


## Cycle 009 Addendum — No governance-only updates

Every PM cycle must run a broad JQL audit for the epics touched by changed files. The PM must update both:
1. Governance/process tickets, and
2. Product story/task tickets touched by code, tests, fixtures, docs, or reporting.

A cycle response fails if product files changed but only governance tickets were updated.

Required mapping fields per changed file group:
- Changed file group
- Jira key(s)
- Story/DOD status: partial, complete, blocked, or not applicable
- Branch and PR number
- Codex status
- CI/Codecov status
- Next status transition

Done is only allowed when the full source story DOD is satisfied. Partial scaffold, fixture, dry-run, or contract work remains In Progress.


## Cycle 012 Addendum — Board-first and AC/DoD-first

The Cycle 008/009 changed-file mapping protocol remains active, but it is no longer sufficient by itself. Cycle planning must begin from Jira, not from the Git diff.

Every cycle must now include:

1. Board inventory before work selection.
2. Exact Jira issues selected before implementation begins.
3. AC/DoD bullets embedded in every agent task.
4. A ledger update for every touched Jira issue.
5. Explicit evidence for why any broad story remains In Progress rather than Done.
6. A merge gate that checks for uncommitted local work not represented in the PR.
7. PM response evidence that includes board audit findings, or a documented scope-limit explanation when full-board audit is not feasible.
8. A statement that governance/cycle tickets do not replace product-story updates.
9. Explicit key-level Jira authority notes when Cursor agents are assigned Jira actions.

This addendum exists because the project has a large Jira backlog and the PM must avoid drifting into PR-first planning.
