# PR Checks and Codecov Protocol

## Policy

Every pull request targeting `develop` must have:

- GitHub Actions checks present and completed.
- Local coverage parity gate passing at >= 90%.
- Codecov patch coverage status present and >= 90%.
- Codecov project coverage status present and >= 90%.

Missing checks are blockers. Pending checks are blockers. Failing checks are blockers.

A local coverage pass is necessary but not sufficient for merge readiness.

## Coverage Signal Definitions

- Local coverage gate: result of the local pytest coverage run with `--cov-fail-under=90`.
- Codecov patch status: diff-focused check context (`codecov/patch`) that validates changed lines.
- Codecov project status: repository/project-wide check context (`codecov/project`) that validates aggregate coverage posture.

All three signals must align before declaring merge readiness.

## Required Local Parity Commands

Run from repository root before push:

```bash
git status --short
git log --oneline --decorate -12
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle006.db
python run.py phase2-smoke
```

The parity run is incomplete if any command is skipped.

## GitHub Check Requirements

PR checks must show:

- CI workflow run(s) posted by GitHub Actions.
- Required CI jobs in `success` state.
- Codecov project status check in `success` state at or above 90%.
- Codecov patch status check in `success` state at or above 90%.

If Codecov statuses are absent, treat as blocked even when local coverage passes.

If Codecov project status is missing, the PR remains blocked unless PM grants a documented temporary exception in cycle governance artifacts.

## Steward Verification Steps

1. Push the branch.
2. Inspect PR checks (`gh pr view <number> --json statusCheckRollup` or GitHub UI).
3. Confirm GitHub Actions checks are present and completed.
4. Confirm Codecov project and patch checks are present and pass 90% threshold.
5. Record status in the cycle report as `PASS`, `BLOCKED`, or `UNKNOWN`.

## Merge Gate

A PR is merge-ready only when all are true:

- No unresolved required review threads.
- All required GitHub checks are green.
- Codecov project >= 90%.
- Codecov patch >= 90%.
- PR targets `develop`.
- `main` remains untouched by cycle work.
