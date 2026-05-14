# Cycle Branch Checklist

Use this checklist every cycle to prevent branch/push/PR ambiguity.

- [ ] I am on the cycle branch (example: `cycle/002/integration`).
- [ ] I ran `git status` and confirmed expected changes only.
- [ ] I ran `git log --oneline -8` and verified recent agent commits.
- [ ] Each agent committed only their owned files.
- [ ] Validation checks ran on this branch (`ruff`, `mypy`, `pytest`).
- [ ] I pushed the cycle branch with:
      `git push -u origin cycle/002/integration`
- [ ] I opened a PR with base branch `develop`.
- [ ] The PR head branch is `cycle/002/integration`.
- [ ] I confirmed: **Do not push to main.**
- [ ] I confirmed: **Do not open direct PRs to main.**
