# Cursor-agent Jira Operations

## Scope and authority

Cursor agents may perform Jira read/write/edit actions only when the active cycle prompt explicitly assigns Jira responsibilities.

## Allowed Jira operations

- Read Jira issue descriptions, acceptance notes, status, transitions, and linked context.
- Post cycle comments with implementation and validation evidence.
- Move assigned tickets to `In Progress` or `In Review` when source work and validation support the transition.
- Create bug tasks from Codex findings and link them to the active cycle when requested.
- Maintain changed-file-to-Jira mapping tables in cycle reports and PR descriptions.

## Guardrails

- Do not mark broad product stories `Done` unless source Definition of Done is fully satisfied.
- Do not close governance tickets before the implementation is merged into `develop`.
- Do not post ambiguous Jira updates. Every update must include cycle id, branch, changed files, and validation evidence.
- Do not transition tickets outside assigned prompt scope.
- Do not use Jira updates as a substitute for missing code, tests, or documentation evidence.

## Required comment template

Use this minimum structure for each cycle update:

- Cycle: `Cycle 010`
- Agent: `Agent A`
- Branch: `cycle/010/integration`
- Changed files: `<repo paths>`
- Validation evidence: `<commands/checks and outcome>`
- DOD status: `Partial` or `Full`
- Recommendation: `To Do`, `In Progress`, `In Review`, or `Done` with reason

## Status transition rules

- `To Do` -> `In Progress`: implementation or validation work has started.
- `In Progress` -> `In Review`: branch/PR-ready evidence exists and checks pass.
- `In Review` -> `Done`: merged code and full source DOD confirmed.

If work is partial (for example docs or contract scaffolding only), keep the ticket `In Progress` or `In Review` with explicit partial-DOD language.
