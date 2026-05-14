# Pull Request Template

## Summary

- Describe the problem and why this change is needed.
- Describe the implementation approach and expected impact.

## Jira Keys

- Primary:
- Related:

## Changed Areas

- [ ] `src/config`
- [ ] `src/scripts`
- [ ] `src/collection`
- [ ] `src/analysis`
- [ ] `src/reporting`
- [ ] `docs`
- [ ] `.github`
- [ ] Other:

## Validation Commands

Paste exact command outputs (or links) for all applicable checks:

- `python -m ruff check .`
- `python -m mypy src`
- `python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90`
- `python run.py config-check`
- `python run.py foundation-gate --database-url sqlite:///data/foundation_gate_ci.db`
- `python run.py phase2-smoke`

## Codecov Status

- Project coverage (target >=90%):
- Patch coverage (target >=90%):
- Codecov check links:

## Codex Review Disposition

|Thread/Comment|File|Disposition|Fix Commit/Test|Resolution Status|
|---|---|---|---|---|
|||||Open/Resolved|

## Branch Policy

- Cycle PR target branch: `develop`
- Head branch format: `cycle/###/integration`
- Direct pushes to `main`: forbidden

## Merge Readiness Checklist

- [ ] All Codex review comments have explicit replies.
- [ ] All Codex review threads are resolved.
- [ ] GitHub Actions checks are green.
- [ ] Codecov project coverage is >=90%.
- [ ] Codecov patch coverage is >=90%.
- [ ] PR targets `develop` for cycle integration work.
- [ ] No direct push to `main` was used.
- [ ] No runtime artifacts (db/cache/temp reports) are included.
