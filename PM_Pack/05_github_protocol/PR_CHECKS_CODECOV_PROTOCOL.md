# PR CHECKS AND CODECOV PROTOCOL
# Added: Cycle 005 — Permanent PM/GitHub Governance Rule

## Purpose

The Fiverr Research System must not rely only on local validation claims. Every PR must run GitHub Actions checks and Codecov coverage reporting before it can merge.

## Required PR Checks

Every PR into `develop` must run and pass these checks:

1. `python -m ruff check .`
2. `python -m mypy src`
3. `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
4. `python run.py config-check`
5. `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`
6. `python run.py phase2-smoke`
7. Codecov upload and Codecov project/patch coverage status.
8. Codex review threads fully dispositioned and resolved.

## Codecov Coverage Gate

Coverage is a blocker.

- Minimum project coverage: `90%`.
- Minimum patch coverage: `90%`.
- The local pytest coverage command must use `--cov-fail-under=90`.
- `coverage.xml` must be uploaded to Codecov from GitHub Actions.
- If Codecov status is pending, missing, failing, or unavailable, the PR must not merge.

## GitHub Actions Workflow Requirements

The repository must contain `.github/workflows/ci.yml` with:

- Trigger: `pull_request` targeting `develop` and `main`.
- Trigger: `push` to `develop`, `main`, and `cycle/**/integration` branches.
- Python version: `3.11` initially. Add `3.12` once dependencies are stable.
- Install command: `python -m pip install --upgrade pip && python -m pip install -e ".[dev]"`.
- Lint/type/test commands listed above.
- Codecov upload using `codecov/codecov-action`.
- Artifact upload for `coverage.xml` even if Codecov upload fails, so review evidence remains available.

## Required Branch Protection Strategy

`develop` must be the integration branch and should be protected with required status checks:

- CI / lint
- CI / type-check
- CI / tests-coverage
- CI / smoke-gates
- Codecov project coverage
- Codecov patch coverage

`main` must be release-only and protected with the same checks plus PM release approval.

If the Cursor/GitHub Steward agent cannot configure branch protection through `gh` or GitHub UI permissions, it must report this as a blocker and provide the exact settings for Kevin/PM to apply.

## Default Branch Policy

The repository default branch must not be a cycle branch. It should be `develop` during active development unless Kevin chooses `main` after the first stable release. Cycle 005 live GitHub review found the default branch set to `cycle/002/integration`; that is incorrect and must be corrected.

## Required PR Template

The repository must contain a PR template requiring:

- Summary.
- Jira keys.
- Codex disposition table.
- Validation commands.
- Codecov result link/status.
- Confirmation that no direct `main` push occurred.
- Confirmation that all Codex threads are resolved or formally dispositioned.

## Merge Blockers

A PR is blocked if any of the following are true:

- No GitHub Actions workflow ran for the PR head SHA.
- Any required workflow job failed, was cancelled, or is pending beyond expected runtime.
- Codecov report is missing or below 90%.
- Any Codex thread remains unresolved.
- Any Codex thread was resolved without a disposition reply.
- The PR branch is not based on the latest `develop`.
- The repo working tree used for push contains generated runtime DBs, caches, secrets, browser sessions, or local-only artifacts.
- The PR attempts to target `main` outside of an approved release cycle.

## Integration/GitHub Steward Checklist

The final steward agent must run:

```bash
git fetch --all --prune
git status --short
git log --oneline --decorate -12
git merge-base --is-ancestor origin/develop HEAD
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci_local.db
python run.py phase2-smoke
```

Then verify on GitHub:

- PR exists and targets `develop`.
- GitHub Actions checks are present and passing.
- Codecov statuses are present and passing.
- Codex review threads are resolved after disposition.
- No PR is merged until all required gates pass.


## Cycle 006 Update — Project Status Visibility

The project coverage gate must be visible as a GitHub/Codecov status, not only as local pytest output. If the PR only shows `codecov/patch`, the steward must investigate why project status is absent. Until project status is visible and successful, merge readiness is `BLOCKED` unless PM/operator grants a documented temporary exception.

Required steward evidence:

- CI check name and conclusion.
- Codecov patch status name, target, and conclusion.
- Codecov project status name, target, and conclusion.
- Local coverage command output with `--cov-fail-under=90`.
- Explanation for any missing status and whether it is a hard blocker.
