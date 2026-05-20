# CI PIPELINE
# Updated: Cycle 019

---

## Deployed Workflows

### ci.yml — Main CI Pipeline
**Triggers:** PR to develop/main | Push to develop, main, cycle/**/integration

**Jobs:**
1. Lint — `python -m ruff check .` — must pass with zero errors
2. Type-check — `python -m mypy src` — must pass with zero errors
3. Test — `python -m pytest -q --cov=src --cov-report=xml --cov-fail-under=90`
4. Playwright install — `playwright install chromium` (for AC-1.1.3)
5. Codecov upload — uploads coverage.xml to Codecov
6. Foundation gate — `python run.py foundation-gate` (smoke test)

**Coverage gates:**
- Local: `--cov-fail-under=90`
- Codecov project: >=90%
- Codecov patch: >=90%

### pr-checks.yml — PR Validation
**Triggers:** PR to develop/main

**Jobs:**
1. Validate PR Title — regex match + ≤72 chars + no em-dash + no trailing period
2. Check PR Size — block if >1000 lines (skipped if override:large-pr label present)

### security.yml — Security Scanning
**Triggers:** PR to develop | Push to develop

**Jobs:**
1. Secret Scan — searches src/ for API keys, hardcoded passwords, connection strings (tests/ excluded)
2. Dependency Audit — `pip-audit -r requirements.txt` for known CVEs

### stale.yml — Stale Management
**Triggers:** Daily schedule

- Issues: marked stale after 30 days, closed after 7 more days
- PRs: marked stale after 30 days, closed after 7 more days
- Exempt: issues/PRs with `status:blocked` label

### release.yml — Release Automation
**Triggers:** Push to main with version tag (v*)

- Creates GitHub release automatically
- Generates release notes from commit messages
- Attaches coverage report artifact

---

## Required Status Checks for Merge

develop branch protection requires ALL of these to pass:
- Lint, Typecheck, Tests, and Gates (ci.yml)
- Validate PR (pr-checks.yml)
- Secret Scan (security.yml)
- codecov/project
- codecov/patch

---

## Current Test Stats (Cycle 019 baseline)

| Metric | Value |
|---|---|
| Total tests | 710 |
| Pass rate | 100% |
| Coverage | >=93.6% |
| Source files | 136 |
| Ruff | 0 errors |
| Mypy | 0 errors |
