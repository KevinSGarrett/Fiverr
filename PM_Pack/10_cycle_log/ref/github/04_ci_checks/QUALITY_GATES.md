# Quality Gates
# Fiverr Research System — Gate Definitions & Thresholds

---

## Overview

Quality gates are pass/fail thresholds that a PR or release must clear before proceeding. Gates are enforced by CI and cannot be bypassed without an override label + justification.

---

## Gate 1: Code Linting (Ruff)

| Metric | Threshold | Enforcement |
|---|---|---|
| Lint errors | 0 | CI fails on any Ruff error |
| Format violations | 0 | CI fails if `ruff format --check` finds diffs |

### Ruff Configuration (pyproject.toml)
```toml
[tool.ruff]
target-version = "py311"
line-length = 120
src = ["src", "tests"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort (import sorting)
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "B",      # flake8-bugbear
    "SIM",    # flake8-simplify
    "TCH",    # flake8-type-checking
    "RUF",    # ruff-specific rules
]
ignore = [
    "E501",   # line length handled by formatter
]

[tool.ruff.lint.isort]
known-first-party = ["src"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

---

## Gate 2: Type Checking (Mypy)

| Metric | Threshold | Enforcement |
|---|---|---|
| Type errors | 0 | CI fails on any Mypy error |
| Missing annotations | 0 in src/ | Strict mode requires all annotations |

### Mypy Configuration (pyproject.toml)
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
warn_redundant_casts = true
warn_unused_ignores = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[[tool.mypy.overrides]]
module = [
    "playwright.*",
    "streamlit.*",
    "apscheduler.*",
]
ignore_missing_imports = true
```

---

## Gate 3: Test Coverage (Pytest)

| Metric | Threshold | Enforcement |
|---|---|---|
| Overall coverage | ≥ 80% | CI fails below threshold |
| New code coverage | ≥ 80% | Measured by diff coverage |
| Test pass rate | 100% | All tests must pass |
| Test execution time | < 5 minutes | Warning if exceeded, fail at 10 min |

### Pytest Configuration (pyproject.toml)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=xml:coverage.xml",
    "--cov-fail-under=80",
]
markers = [
    "slow: marks tests as slow (deselect with '-m not slow')",
    "integration: marks integration tests",
    "performance: marks performance benchmarks",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]
```

### Coverage Exceptions
These modules have reduced coverage requirements (documented here):

| Module | Min Coverage | Reason |
|---|---|---|
| `src/collection/workflows/` | 60% | Heavy external dependency (Playwright/Fiverr) |
| `src/dashboard/` | 50% | Streamlit UI testing is limited |
| `src/playbook/pdf_export.py` | 50% | WeasyPrint rendering hard to test |
| All others | 80% | Standard threshold |

---

## Gate 4: PR Validation

| Metric | Threshold | Enforcement |
|---|---|---|
| Title format | Matches convention | CI fails |
| Description length | ≥ 50 chars content | CI fails |
| Required labels | type + priority + scope + risk | CI fails if missing |
| PR size | ≤ 1000 lines (without override) | CI fails for XXL |
| Conversations | All resolved | Branch protection |

---

## Gate 5: Security Scan

| Metric | Threshold | Enforcement |
|---|---|---|
| Hardcoded secrets | 0 | CI fails on detection |
| Known vulnerabilities | 0 critical/high | Advisory warning (non-blocking in v1) |
| Dependency audit | No known CVEs | Advisory warning |

---

## Gate 6: Release Gate (develop → main only)

Additional gates applied only to release PRs:

| Metric | Threshold | Enforcement |
|---|---|---|
| All CI gates above | Pass | Required |
| Integration tests | Pass | Run full integration suite |
| No open P1/P2 issues for the epic | 0 | Manual verification |
| Changelog updated | Yes | PR description lists all stories |
| Version tag prepared | Yes | PR description includes version number |

---

## Gate Summary Matrix

| Gate | Feature PR → develop | Release PR → main |
|---|---|---|
| Ruff lint | ✅ Required | ✅ Required |
| Mypy type-check | ✅ Required | ✅ Required |
| Pytest ≥80% coverage | ✅ Required | ✅ Required |
| PR title/description | ✅ Required | ✅ Required |
| Required labels | ✅ Required | ✅ Required |
| Size limit | ✅ Required | ✅ Required |
| Security scan | ⚠️ Advisory | ✅ Required |
| Integration tests | ❌ Not run | ✅ Required |
| Changelog check | ❌ Not required | ✅ Required |

---

## Override Policy

Any gate can be overridden with the appropriate override label, but:

1. The override label must be applied by the human operator (not an AI agent)
2. A justification must be written in the PR description under `## Override Justification`
3. A follow-up issue must be created to address the underlying problem
4. The override is logged in the project changelog

| Override Label | What It Bypasses |
|---|---|
| `override:emergency` | All branch protection rules |
| `override:large-pr` | Size XXL blocking |
| `override:skip-tests` | Test coverage gate (CI-only changes) |
