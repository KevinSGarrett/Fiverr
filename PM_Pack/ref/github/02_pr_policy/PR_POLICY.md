# Pull Request Policy
# Fiverr Research System — Complete PR Rules

---

## PR Golden Rules

1. **Every change goes through a PR** — No exceptions, no direct pushes
2. **One PR = one logical change** — Don't bundle unrelated changes
3. **Small PRs merge fast** — Target < 300 lines changed
4. **PR must pass all CI checks** before merge
5. **PR must have correct labels** before merge
6. **Squash merge only** — One clean commit per PR on the target branch
7. **Branch auto-deletes after merge** — No stale branches

---

## PR Lifecycle

```
1. CREATE    Agent creates feature branch from develop
2. DEVELOP   Agent implements changes (multiple commits OK)
3. PUSH      Agent pushes branch to origin
4. OPEN PR   Agent creates PR with template filled out
5. LABEL     Agent applies required labels (type, priority, scope, size, risk)
6. CI RUNS   Automated checks run (lint, type-check, test, pr-validation)
7. FIX       If CI fails → agent fixes and pushes (CI re-runs)
8. MERGE     When all checks green → squash merge to develop
9. CLEANUP   Branch auto-deleted, issue linked/updated
```

---

## PR Requirements Checklist

Every PR MUST have:

| Requirement | Enforced By | Required For |
|---|---|---|
| Title follows conventional format | CI (pr-checks) | All PRs |
| Description filled using template | CI (pr-checks) | All PRs |
| At least 1 type label | CI (pr-checks) | All PRs |
| At least 1 priority label | CI (pr-checks) | All PRs |
| At least 1 scope label | CI (pr-checks) | All PRs |
| Size label (auto-applied) | CI (pr-checks) | All PRs |
| Risk label | CI (pr-checks) | All PRs |
| All CI checks passing | Branch protection | All PRs |
| Linked issue (if task/story) | Convention | feature/ PRs |
| Tests for new functionality | CI (coverage gate) | feature/ PRs |
| No secrets in diff | CI (security scan) | All PRs |

---

## PR Merge Conditions

### To merge into `develop`:
- ✅ All required CI checks pass
- ✅ No unresolved conversations
- ✅ Required labels present
- ✅ PR is not marked as draft

### To merge into `main` (release PR):
- ✅ All required CI checks pass
- ✅ PR title starts with `release:`
- ✅ PR body lists all stories included
- ✅ Integration tests pass
- ✅ No unresolved conversations

---

## PR Description Requirements

### Minimum Content (enforced by template):
1. **What** — 1-2 sentence summary of what this PR does
2. **Why** — Which story/task this implements (link to issue)
3. **How** — Key implementation decisions or approach
4. **Testing** — What tests were added/modified
5. **Checklist** — Filled-out checklist from template

### Good Description Example:
```markdown
## What
Implements the DemandScoreCalculator (Story 4.1) with all 4 components:
Fiverr count (log-scaled), autocomplete position, Google Trends slope, and Reddit intent.

## Why
Closes #47 — Part of Epic 04 (Scoring Engine). The demand score is the first
of 11 score calculators and is required before the composite final score.

## How
- Used log10 scaling for Fiverr result count to handle range 0-50,000+
- Autocomplete position maps linearly: position 1=100, 10=10, absent=0
- Trend slope uses thresholds from DEMAND_SCORE.md spec
- Reddit signal normalized to 0-100 from raw intent score

## Testing
- Added 12 unit tests in test_scoring.py covering:
  - Each component independently
  - Composite score with all components
  - Null/missing input handling
  - Edge cases (0 results, max results)

## Checklist
- [x] Tests added for new functionality
- [x] All existing tests still pass
- [x] Follows spec in project-pack/05_scoring/DEMAND_SCORE.md
- [x] No secrets or sensitive data in changes
```

### Bad Description Example:
```markdown
## What
Added demand score

## Why
Needed

## Checklist
- [x] Done
```
This would fail the PR validation check for insufficient description.

---

## Draft PRs

### When to Use Draft PRs
- Work in progress that needs early visibility
- Requesting feedback before completion
- Spike/exploration work

### Draft PR Rules
- Draft PRs do NOT trigger required checks
- Draft PRs CANNOT be merged
- Agent marks as "Ready for Review" when complete
- At that point, all normal PR rules apply

---

## Stale PR Policy

| Age | Action |
|---|---|
| 3 days | Bot adds `stale` label and comment |
| 5 days | Bot adds second warning comment |
| 7 days | Human decision: close, update, or justify keeping open |

PRs should not live more than 3 days. If a PR is stale, the agent should:
1. Rebase from develop (resolve conflicts)
2. Reduce scope if too large
3. Close and create smaller PRs
