# Cycle Branch Checklist

Use this checklist every cycle to prevent branch/push/PR ambiguity.

- [ ] Agent D (or PM-assigned steward agent) is on the cycle branch (example: `cycle/003/integration`).
- [ ] Steward agent ran `git status` and confirmed expected changes only.
- [ ] Steward agent ran `git log --oneline -8` and verified recent agent commits.
- [ ] Each agent committed only owned files.
- [ ] Steward agent ran validation checks on the cycle branch (`ruff`, `mypy`, `pytest`).
- [ ] Steward agent pushed the cycle branch:
      `git push -u origin cycle/003/integration`
- [ ] Steward agent opened/updated a PR with base branch `develop`.
- [ ] PR head branch is `cycle/003/integration`.
- [ ] Explicit policy check: **Never push to `main`.**
- [ ] Explicit policy check: **Never open direct PRs to `main`.**
- [ ] Human role remains approval and oversight; execution stays agent-managed when authenticated.
