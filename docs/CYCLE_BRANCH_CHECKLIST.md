# Cycle Branch Checklist

Use this checklist every cycle to prevent branch/push/PR ambiguity.

- [ ] Agent D (or PM-assigned steward agent) is on the cycle branch (example: `cycle/010/integration`).
- [ ] Steward agent ran `git status` and confirmed expected changes only.
- [ ] Steward agent ran `git log --oneline -8` and verified recent agent commits.
- [ ] Each agent committed only owned files.
- [ ] Steward agent ran full local parity checks on the cycle branch:
      `python -m ruff check .`
      `python -m mypy src`
      `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
      `python run.py config-check`
      `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle010.db`
      `python run.py phase2-smoke`
- [ ] Steward agent pushed the cycle branch:
      `git push -u origin cycle/010/integration`
- [ ] Steward agent opened/updated a PR with base branch `develop`.
- [ ] PR head branch is the active cycle branch (example: `cycle/010/integration`).
- [ ] Integration/GitHub Steward verifies PR body includes a Jira mapping section that maps changed files to exact Jira stories.
- [ ] Integration/GitHub Steward verifies product-file changes include product-story keys (not governance-only keys).
- [ ] Explicit policy check: **Never push to `main`.**
- [ ] Explicit policy check: **Never open direct PRs to `main`.**
- [ ] Human role remains approval and oversight; execution stays agent-managed when authenticated.
- [ ] Runtime DB hygiene confirmed: ignored `data/*.db` artifacts are excluded from repo package/handoff zip unless intentionally archived externally.
- [ ] Local parity artifact cleanup completed after validation (`coverage.xml`, temporary `data/*.db`, and temporary artifacts).

## Prompt task-volume standard

- Normal cycle prompts should assign **10-20 substantive tasks** per Cursor agent.
- Preferred target is **12-16 tasks** for balanced throughput.
- Fewer tasks are allowed only for hotfix or narrow repair cycles with a written `TASK-COUNT WAIVER`.
- Task volume can mix implementation, tests, docs, Jira operations, validation, and reporting; each task does not need to be large.

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

## Cycle 010 steward handoff checklist

- [ ] Agent D runs final full local parity validation and records outcomes in steward report.
- [ ] Agent D verifies no overlapping owned-file conflicts remain across agent commits.
- [ ] Agent D verifies Jira operations were completed or explicitly logged as blocked in cycle reports.
- [ ] Agent D pushes `cycle/010/integration` and creates/updates the PR into `develop`.
- [ ] Agent D addresses Codex review comments with explicit disposition evidence before merge recommendation.
- [ ] No direct pushes or merges to `main` at any point in cycle execution.
