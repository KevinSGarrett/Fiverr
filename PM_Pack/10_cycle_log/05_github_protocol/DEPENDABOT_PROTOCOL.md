# DEPENDABOT PROTOCOL
# Added: Cycle 019

---

## Overview

Dependabot is active on the repository. It will automatically open PRs weekly for:
- pip package updates (requirements.txt)
- GitHub Actions version updates (.github/workflows/*.yml)

---

## Handling Dependabot PRs

### If CI passes
1. Review the diff — confirm it is a minor version bump (not major)
2. Squash merge the PR
3. No Jira update required for routine dependency bumps
4. Branch auto-deletes after merge

### If CI fails
1. Close the PR with this comment:
   > Closing: this Dependabot PR was opened against an older state of develop and its CI fails against the current codebase. Dependabot will reopen with a fresh branch on the next schedule. No action needed.
2. Do NOT force-merge a failing Dependabot PR
3. Do NOT manually fix the Dependabot PR branch — let it reopen cleanly

### If it is a major version bump
1. Do NOT auto-merge
2. Test locally first: `pip install {package}=={version}` and run `pytest -q`
3. If tests pass: merge normally
4. If tests fail: close with a comment explaining the version conflict

---

## Dependabot Configuration

File: `.github/dependabot.yml`
- Schedule: weekly (Monday)
- Package ecosystems: pip, github-actions
- Assignee: KevinSGarrett
- Labels auto-applied: `type:chore`, `priority:P4-low`

---

## PM Rule

Never batch Dependabot PRs into a cycle integration branch. They are always handled as standalone PRs separate from cycle work.
