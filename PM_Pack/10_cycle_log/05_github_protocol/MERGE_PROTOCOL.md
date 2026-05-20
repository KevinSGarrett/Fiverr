# MERGE PROTOCOL
# Updated: Cycle 019

---

## Merge Conditions (ALL must be true)

1. All CI checks pass (ci.yml, pr-checks.yml, security.yml)
2. Codecov project coverage ≥90% AND patch coverage ≥90%
3. PM has reviewed all agent work
4. PM confidence ≥80 for each agent
5. No unresolved PR conversations
6. PR body lists all tasks with checkboxes checked
7. Scope, type, priority labels present on PR
8. If diff >1000 lines: `override:large-pr` label present

---

## override:large-pr Label

For batch/audit PRs that legitimately exceed 1000 lines:
1. Add `override:large-pr` label BEFORE opening the PR (or before CI re-runs)
2. The pr-checks.yml workflow reads the label and skips the size gate
3. Document why the PR is large in the PR body
4. This is PM-authorized only — Cursor agents must not self-authorize large PRs

---

## CI Failure Actions

| Failure | Action |
|---|---|
| Ruff lint errors | Fix in same cycle branch — commit and repush |
| Mypy type errors | Fix task for next commit — missing annotations |
| Test failures | Investigate: agent error or environment issue |
| PR title invalid | Fix title format (≤72 chars, type(scope): desc, ASCII only) |
| PR too large | Add override:large-pr label if justified, or split the PR |
| Secret scan hit | Remove secret from src/ — use env vars |
| Dependency audit | Update requirements.txt to patched version |
| Codecov below 90% | Add tests before merging |

---

## Merge Method

- Always: squash merge only
- Never: merge commit or rebase
- Branch auto-deleted after merge (enabled in repo settings)

---

## Post-Merge Checklist

- [ ] Verify develop CI is green after merge
- [ ] `git checkout develop && git pull origin develop` on local
- [ ] Update Jira Done stories with merge SHA comment
- [ ] Verify GitHub Development panel populated on Jira stories
- [ ] Update EPIC_STATUS_TRACKER.md
- [ ] Update STATE_SNAPSHOT.md with new SHA
- [ ] Check for new Dependabot PRs — handle per DEPENDABOT_PROTOCOL.md
