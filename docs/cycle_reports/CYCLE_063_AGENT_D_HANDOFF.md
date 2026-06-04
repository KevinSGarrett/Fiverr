# CYCLE 063 — AGENT D HANDOFF

## Execution Order
- D runs last, after A/B/E/C/F complete.

## Merge Gate Responsibilities
- Build complete G1 attribution from full commit range (`git log`) and verify zone compliance:
  - E must remain docs-only.
- Execute §12.3 playbook:
  - apply `override:large-pr`
  - run Codex review checks twice
  - treat `codecov/patch` as advisory
  - validate `mergeable_state`

## Independent Validation (Do Not Trust Prior Reports)
- Run independent golden parity check (pricing task must be additive).
- Run independent demo-data check (9D must not reintroduce demo-data refs).
- Verify pricing task is not called in golden mode (via override posture / execution evidence).

## Jira Closeout
- After merge success:
  - transition `SCRUM-1023` -> Done
  - transition `SCRUM-1024` -> Done
  - post closeout comments with PR number, squash SHA, and gate summary.
