# MERGE PROTOCOL

---

## Conditions (ALL must be true)
1. All CI checks pass (lint, type-check, test, pr-validation)
2. PM has reviewed all agent work
3. PM confidence >= 80 for each agent
4. No unresolved PR conversations
5. PR body lists all tasks with checkboxes
6. Scope and risk labels present

## CI Failure Actions
| Failure | Action |
|---|---|
| Lint errors | Quick-fix in same cycle or next |
| Type errors | Fix task — missing annotations |
| Test failures | Investigate: agent error or dep issue |
| PR validation | Fix title/labels — PM responsibility |

## Merge Method
- Always: squash merge
- Never: merge commit or rebase
- Branch auto-deleted after merge

## Post-Merge
1. Verify develop is green
2. Update Jira tickets with merge comment
3. Update EPIC_STATUS_TRACKER.md

## Cycle 005 Addendum — Codex, CI, and Codecov Merge Blockers

No PR may merge unless all Codex review threads are dispositioned and resolved, GitHub Actions checks are present and passing, and Codecov project/patch coverage is at least 90%. See `05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md` and `05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md`.
