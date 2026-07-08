# Test Suite — Fiverr Research System

## Overview

All tests live under `tests/` and mirror the `src/` directory structure.
Run the full suite from the project root:

```bash
pytest -q                          # fast pass/fail
pytest -v --tb=short               # verbose with short tracebacks
pytest --cov=src --cov-report=term # with coverage
```

---

## Directory Structure

```
tests/
├── conftest.py                  # Shared fixtures (see below)
├── fixtures/
│   ├── analysis/
│   │   └── factories.py         # AnalysisResult / AnalysisRun factory helpers
│   └── dashboard/
│       └── factories.py         # Dashboard payload factory helpers
├── integration/
│   ├── test_collection_e2e.py   # End-to-end collection smoke (fixture-based)
│   └── test_database_init.py    # DB init / schema idempotency tests
└── unit/
    ├── test_analysis.py         # src/analysis/ unit tests
    ├── test_cli.py              # run.py CLI command tests
    ├── test_collection.py       # src/collection/ unit tests
    ├── test_collection_pacing.py# PacingManager delay/jitter tests
    ├── test_config.py           # src/config/ unit tests
    ├── test_dashboard.py        # src/dashboard/ unit tests
    ├── test_dashboard_queries.py# DashboardQueryLayer / query_layer tests
    ├── test_keyword_features.py # Keyword feature extraction tests
    ├── test_llm.py              # src/llm/ unit tests (client, cache, templates)
    ├── test_models.py           # SQLAlchemy ORM model tests
    ├── test_orchestrator.py     # src/orchestrator.py orchestration tests
    ├── test_orchestrator_helpers.py
    ├── test_playbook.py         # src/playbook/ unit tests
    ├── test_proxy.py            # src/collection/proxy.py tests
    ├── test_reports.py          # src/reports/ unit tests
    ├── test_scaffolds.py        # Scaffold / stub smoke tests for E04-E07
    ├── test_seeds.py            # Seed data import tests (data/seeds/)
    ├── test_template_renderer.py# Jinja2 template rendering tests
    └── test_utils.py            # src/utils/ unit tests
```

---

## Shared Fixtures (`tests/conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `db_session` | function | In-memory SQLite session with all tables created |
| `tmp_db_url` | function | Temporary file-based SQLite URL |
| `sample_niche` | function | A `Niche` ORM instance committed to `db_session` |
| `sample_keyword` | function | A `Keyword` instance linked to `sample_niche` |
| `sample_config` | function | Loaded `Config` object from `config.yaml` |
| `tmp_data_dir` | function | Temporary directory for file-based tests |

Usage:

```python
def test_keyword_creation(db_session, sample_niche):
    from src.models.market import Keyword
    kw = Keyword(niche_id=sample_niche.id, keyword="test", normalized_keyword="test")
    db_session.add(kw)
    db_session.commit()
    assert kw.id is not None
```

---

## Factory Helpers

### `tests/fixtures/analysis/factories.py`

```python
from tests.fixtures.analysis.factories import make_analysis_run, make_analysis_result
run = make_analysis_run(db_session, niche_id=1)
result = make_analysis_result(db_session, run_id=run.id)
```

### `tests/fixtures/dashboard/factories.py`

```python
from tests.fixtures.dashboard.factories import make_dashboard_payload
payload = make_dashboard_payload(keyword_count=5)
```

---

## Running Specific Groups

```bash
# Unit tests only
pytest tests/unit/ -q

# Integration tests only
pytest tests/integration/ -q

# Single file
pytest tests/unit/test_models.py -v

# By marker (when markers are added)
pytest -m "not integration" -q

# Coverage for a specific module
pytest --cov=src/utils --cov-report=term tests/unit/test_utils.py
```

---

## Writing New Tests

1. Mirror the source path: `src/scoring/demand.py` → `tests/unit/test_scoring_demand.py`
2. Use fixtures from `conftest.py` — don't create new DB sessions manually
3. Mock external services — never make real HTTP calls in unit tests:
   ```python
   from unittest.mock import patch, MagicMock
   with patch("src.llm.client.openai") as mock_openai:
       mock_openai.chat.completions.create.return_value = MagicMock(...)
   ```
4. Keep tests fast — no `time.sleep()`, use freezegun for time-dependent logic
5. Target ≥ 80% coverage on any new module

---

## Coverage Thresholds

| Threshold | Value | Enforced by |
|-----------|-------|-------------|
| Project overall (pytest gate) | 80% | `ci.yml` (`--cov-fail-under=80`, matches `pyproject.toml`'s `fail_under = 80`) |
| Project overall (Codecov gate) | 90% | Codecov `codecov.yml` |
| Patch (new code) | 90% | Codecov `codecov.yml` |
| New module minimum | 80% | `.cursorrules` testing rules |

---

## AC Reference

These tests directly validate acceptance criteria:

| Test File | AC Items Covered |
|-----------|-----------------|
| `test_config.py` | AC-1.2.1 through AC-1.2.8 |
| `test_models.py` | AC-1.3.1 through AC-1.3.11 |
| `test_cli.py` | AC-1.4.1 through AC-1.4.7 |
| `test_llm.py` | AC-1.5.1 through AC-1.5.8 |
| `test_utils.py` | AC-1.6.1 through AC-1.6.6 |
| `test_seeds.py` | AC-1.7.1 through AC-1.7.5 |
| `test_collection_pacing.py` | AC-2.3.1 through AC-2.3.4 |
| `test_collection.py` | AC-2.4.1 through AC-2.4.6 |
| `test_database_init.py` | AC-1.3.10, AC-10.5.1 |
