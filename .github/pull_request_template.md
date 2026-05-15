# Pull Request Template

## Summary

- Describe the problem and why this change is needed.
- Describe the implementation approach and expected impact.

## Jira Keys

- Primary:
- Related:
- Board audit artifacts:
  - `docs/jira/BOARD_AC_DOD_AUDIT_CYCLE_012.md`
  - `docs/jira/ACTIVE_STORY_DOD_LEDGER.md`

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

## Board-First Jira Audit Summary

- Issue-type and status summary for all touched keys:
- Active stories touched this PR:
- AC/DoD bullets advanced:
- AC/DoD bullets not advanced (and why):
- Missing AC/DoD coverage follow-ups created:

## Codecov Status

- Project coverage (target >=90%):
- Patch coverage (target >=90%):
- Codecov check links:

## Codex Review Disposition

|Thread/Comment|File|Disposition|Fix Commit/Test|Resolution Status|
|---|---|---|---|---|
|||||Open/Resolved|

## Local-Discrepancy Reconciliation

- Compare local archive vs PR head performed: Yes/No
- Reconciliation result (committed vs intentionally excluded):
- Evidence comment link:

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
- [ ] Board-first Jira audit summary is complete.
- [ ] AC/DoD progress for all touched keys is included.
- [ ] No runtime artifacts (db/cache/temp reports) are included.
