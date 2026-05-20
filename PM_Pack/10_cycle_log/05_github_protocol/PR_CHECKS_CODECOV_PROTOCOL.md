# PR CHECKS AND CODECOV PROTOCOL
# Updated: Cycle 019

---

## Deployed Workflows (Current — as of Cycle 019)

All 5 workflows are deployed and active in .github/workflows/:

| Workflow | File | Trigger | Purpose |
|---|---|---|---|
| CI | ci.yml | PR to develop/main, push to develop/main/cycle/* | Ruff + Mypy + Pytest + Codecov |
| PR Checks | pr-checks.yml | PR to develop/main | Title validation + size check |
| Security | security.yml | PR to develop, push to develop | Secret scan + dependency audit |
| Stale | stale.yml | Schedule (daily) | Auto-stale PRs/issues after 30 days |
| Release | release.yml | Push to main with version tag | Create GitHub release |

---

## Required Checks Before Merge (ALL must pass)

1. **Lint** — `python -m ruff check .` — zero errors
2. **Type-check** — `python -m mypy src` — zero errors
3. **Tests** — `python -m pytest -q --cov=src --cov-report=xml --cov-fail-under=90` — all passing
4. **Codecov project** — >=90% overall coverage
5. **Codecov patch** — >=90% patch coverage
6. **PR title valid** — ≤72 chars, conventional commits format, ASCII only
7. **PR size** — ≤1000 lines OR override:large-pr label present
8. **Secret scan** — no secrets in src/ files
9. **Dependency audit** — no known vulnerabilities

---

## PR Title Validation Rules (enforced by pr-checks.yml)

Pattern: `^(feat|fix|refactor|test|docs|chore|style|perf|ci|build|release|hotfix|revert)(\([a-z0-9-]+\))?: .+$`

Rules:
- Maximum 72 characters total
- Must match the regex above
- No em-dash (—) — use hyphen (-) only
- No trailing period
- Valid: `feat(cycle-020): E02 collection engine [Claude AI]`
- Invalid: `feat(cycle-020): E02 collection engine — core pipeline [Claude AI]` (em-dash, >72 chars)

---

## PR Size Policy (enforced by pr-checks.yml)

- Warning: >300 lines
- Block: >1000 lines — CI fails unless override:large-pr label is present
- Override: Add `override:large-pr` label to the PR BEFORE CI runs
- PM authorization required for override — agents cannot self-authorize

---

## Codecov Configuration

- Codecov project: https://app.codecov.io/gh/KevinSGarrett/Fiverr
- codecov.yml in repo root sets patch and project thresholds
- Coverage reports uploaded automatically from ci.yml on every PR
- If Codecov is pending or missing: wait — do not merge

---

## Local Validation Commands (run before pushing)

```bash
cd C:\Fiverr\Fiverr
python -m ruff check .
python -m mypy src
python -m pytest -q --tb=short
python -m pytest --cov=src --cov-report=term --cov-fail-under=90
```

---

## CI Failure Diagnosis

| Check | Common Cause | Fix |
|---|---|---|
| Ruff | Formatting, unused imports | `python -m ruff check --fix .` |
| Mypy | Missing type annotations | Add type hints to new functions |
| Pytest | Broken import, fixture error | Check stacktrace; add missing dependency |
| PR title | Too long, wrong format, em-dash | Shorten and fix format |
| PR size | Too many lines | Add override:large-pr or split PR |
| Secret scan | Test file has fake key in src/ | Move to tests/; exclude tests/ from scan |
| Dependency audit | Known CVE in requirements | Upgrade affected package |
