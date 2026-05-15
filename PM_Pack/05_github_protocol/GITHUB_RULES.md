# GITHUB RULES FOR PM

---

## PM Responsibilities
1. Define integration branch name for each cycle
2. Specify exact branch name in every agent prompt
3. Define PR title and body content
4. Verify CI checks pass before approving merge
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
