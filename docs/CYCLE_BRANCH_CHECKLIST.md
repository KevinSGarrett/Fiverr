# Cycle Branch Checklist

Use this checklist every cycle to prevent branch/push/PR ambiguity.

- [ ] Agent D (or PM-assigned steward agent) is on the cycle branch (example: `cycle/004/integration`).
- [ ] Steward agent ran `git status` and confirmed expected changes only.
- [ ] Steward agent ran `git log --oneline -8` and verified recent agent commits.
- [ ] Each agent committed only owned files.
- [ ] Steward agent ran validation checks on the cycle branch (`ruff`, `mypy`, `pytest`).
- [ ] Steward agent pushed the cycle branch:
      `git push -u origin cycle/004/integration`
- [ ] Steward agent opened/updated a PR with base branch `develop`.
- [ ] PR head branch is `cycle/003/integration`.
- [ ] Integration/GitHub Steward verifies PR body includes a Jira mapping section that maps changed files to exact Jira stories.
- [ ] Integration/GitHub Steward verifies product-file changes include product-story keys (not governance-only keys).
- [ ] Explicit policy check: **Never push to `main`.**
- [ ] Explicit policy check: **Never open direct PRs to `main`.**
- [ ] Human role remains approval and oversight; execution stays agent-managed when authenticated.
- [ ] Runtime DB hygiene confirmed: ignored `data/*.db` artifacts are excluded from repo package/handoff zip unless intentionally archived externally.

## Cycle 009 Branch Flow Note

For PR #7 continuity and safe cycle transition:

- Keep all PR #7 fixes on `cycle/008/integration` until PR #7 is merged to `develop`.
- Do not create `cycle/009/integration` while PR #7 is open or blocked.
- After PR #7 merges, Agent D creates the next branch from updated `develop` only:
  - `git fetch origin --prune`
  - `git checkout develop`
  - `git pull --ff-only origin develop`
  - `git checkout -b cycle/009/integration`
- No-main policy remains mandatory throughout transition:
  - never push to `main`;
  - never open direct PRs to `main`.
