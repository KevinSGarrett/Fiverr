# GITHUB RULES FOR PM — v2
# Updated: Cycle 022 (2026-05-18)
# CRITICAL UPDATE: Two failures from Cycles 020/021 added as hard rules.

---

## PM Responsibilities
1. Define integration branch name for each cycle
2. Specify exact branch name in every agent prompt
3. Define PR title and body content
4. Verify ALL required CI checks pass before approving merge
5. Ensure all agents commit to SAME branch (no separate branches)
6. Track branch lifecycle in cycle log

## Key Rules
- Repo: https://github.com/KevinSGarrett/Fiverr
- Default branch: main (production)
- Integration branch: develop
- Cycle branches: cycle/{NNN}/integration (from develop)
- Merge strategy: squash merge only
- Auto-delete branches: enabled
- Required CI: lint (Ruff), type-check (Mypy), test (Pytest), PR validation
- PR title: feat(cycle-{NNN}): {summary}
- Labels required: type, priority, scope, risk (size auto-calculated)

## Push / PR / Main Rules

- Cursor agents do not push to `main`.
- Cursor agents should not push any branch unless Kevin explicitly asks them to. The default is agent commits locally; the human operator pushes once after all agents complete.
- Cycle PR target is always `develop`, not `main`.
- `main` is production/stable and is updated by release PR only after release gates pass.
- The PM must include these rules in every cycle reply, not just in this protocol file.

---

## ⛔ HARD MERGE GATE — ADDED CYCLE 022 (ENFORCED PERMANENTLY)

PRs #24 and #25 merged while `codecov/patch` was failing. This violates the
coverage gate and must never happen again. The following rules are now absolute:

### Rule G-001: codecov/patch IS a hard merge blocker

`codecov/patch` failing means NEW code added in the PR is below 90% coverage.
This is NOT non-blocking. This is NOT optional. This is a hard blocker.

REQUIRED action when codecov/patch fails:
1. STOP. Do not merge.
2. Run: python -m pytest -q --cov=src/[changed_module] --cov-report=term-missing
3. Identify every uncovered line in NEW code added this PR.
4. Add tests for every uncovered branch/function/line until coverage reaches >=90%.
5. Push the tests. Wait for codecov/patch to re-check and pass.
6. Only merge after BOTH codecov/project AND codecov/patch show PASS.

### Rule G-002: All 6 Codecov status entries must be PASS before merge

Required codecov checks that must show PASS (not FAIL, not MISSING, not PENDING):
- codecov/project
- codecov/patch

If either shows FAIL: add tests. If either shows PENDING: wait. Never merge while any
Codecov status is not PASS.

### Rule G-003: Codex review threads — complete mandatory disposition protocol

Codex threads being absent ("0 findings") is acceptable. But if ANY Codex thread exists:
1. EVERY thread must be classified with one of: VALID_FIXED | VALID_DEFERRED_BLOCKER |
   VALID_DEFERRED_NONBLOCKING | NOT_APPLICABLE | FALSE_POSITIVE | DUPLICATE
2. EVERY VALID_FIXED thread requires: code fix + regression test + push + CI green + thread reply + resolve
3. EVERY other category requires: evidence reply + PM approval (in the PR body or comment) + resolve
4. A thread cannot be "resolved" without a disposition reply. GitHub auto-resolving via push
   does NOT count. The agent must manually reply and resolve.
5. Zero unresolved/undispositioned Codex threads = REQUIRED before merge.

See: PM_Pack/05_github_protocol/CODEX_REVIEW_DISPOSITION_PROTOCOL.md for full protocol.
See: PM_Pack/05_github_protocol/PR_CHECKS_CODECOV_PROTOCOL.md for Codecov gate protocol.

### Rule G-004: Agent D Steward checklist before EVERY merge recommendation

Agent D must explicitly confirm ALL of the following in their report and PR freeze comment:

CODECOV CHECKLIST:
- [ ] codecov/project: PASS (value >= 90%)
- [ ] codecov/patch: PASS (value >= 90%)
- [ ] Local pytest --cov-fail-under=90: PASS
- [ ] Coverage % (project-level): [exact value]
- [ ] Coverage % (patch-level): [exact value or "not separately reported"]

CODEX CHECKLIST:
- [ ] Total Codex threads found: [N]
- [ ] All threads dispositioned: YES / NO
- [ ] All VALID_FIXED threads have regression tests: YES / N/A
- [ ] All non-VALID_FIXED threads have PM-approved evidence replies: YES / N/A
- [ ] All threads resolved (manually, with reply posted): YES
- [ ] Zero unresolved threads: YES

If ANY item above is NO or cannot be confirmed: PR must NOT be merged. Document the
specific blocker, create a Jira task, and leave the PR open.

---

# CYCLE 029 ADDENDUM — BRANCH HYGIENE (Rule G-005)

## Rule G-005: Stale Branch Cleanup (PERMANENT, enforced every cycle)

After each successful PR merge, Agent A must clean up the merged branch.
This prevents accumulation of stale cycle branches in the remote repo.

### Standard Action (every cycle):

After `gh pr merge {N} --merge` succeeds, Agent A runs:

```powershell
# Delete the merged branch from remote
git push origin --delete cycle/{N}/integration

# Delete from local
git branch -D cycle/{N}/integration

# Verify deletion
git branch -r | Select-String "cycle/{N}/integration"
# Expected output: empty (branch is gone)
```

### Periodic Full Cleanup (every 5th cycle: 030, 035, 040, etc.):

In cycles ending in 0 or 5, Agent A also performs the broader cleanup:

```powershell
# List all remote branches
git fetch --all --prune
git branch -r | Select-String "cycle/" | Select-Object -ExpandProperty Line

# For each cycle/NNN/integration branch where NNN < (current_cycle - 3):
# Verify the PR for that branch is MERGED, then delete:
git push origin --delete cycle/{old_N}/integration
```

### Protected Branches — NEVER Delete

- main
- develop
- Any branch containing "backup", "archive", "release", "hotfix"
- Any branch that has an OPEN PR

### Branch Hygiene Report

Agent A documents the cleanup in their cycle report under a "Branch Hygiene"
section:

```
Branch Hygiene (Cycle NNN):
- Merged + deleted: cycle/NNN-1/integration
- Total remote cycle branches before cleanup: X
- Total remote cycle branches after cleanup: Y
- Periodic cleanup performed: YES (cycle ends in 0 or 5) / NO
- Branches deleted in periodic cleanup: [list or N/A]
```

### Failure Mode

If deletion fails with "branch is protected" or "permission denied":
- Document the error
- Do not retry forcefully
- Note in handoff to Agent D for resolution
- Continue with the rest of the cycle work
