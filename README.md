# Fiverr Research System

## Overview

The Fiverr Research System is a local-first Python project for researching Fiverr niches, keyword opportunities, and competitor positioning. The repository lives at [https://github.com/KevinSGarrett/Fiverr](https://github.com/KevinSGarrett/Fiverr), and this local workspace is expected at `C:\Fiverr`.

Cycle 001 (Phase 1, Epic 01) focuses on foundation scaffolding, onboarding, and importable presentation/reporting placeholders. It does not include a full end-to-end production dashboard or pipeline yet.

## Prerequisites

- Python 3.11+
- `pip` available in your shell
- Local git clone at `C:\Fiverr`
- Optional virtual environment tooling (`venv` or equivalent)

## Installation

```bash
cd C:\Fiverr\Fiverr
python -m venv .venv
.venv\Scripts\activate
pip install -e .
playwright install chromium
```

## Configuration

1. Copy `.env.example` to `.env`.
2. Set real secrets in `.env` only.
3. Review `config.yaml` defaults before running project workflows.

`.env` is never committed. Browser/session artifacts are ignored by git (for example: `playwright/.auth/`, `storage_state.json`, `*.session`, and `data/sessions/`).

## Running

Cycle 001 does not ship a production dashboard runtime yet. It includes importable scaffolding to prepare for later implementation cycles.

For package and environment verification:

```bash
python -c "from src.dashboard.app import create_app_title; from src.exports.placeholders import validate_export_format"
```

## Architecture

Current foundation modules:

- `src/config`: Configuration loading and validation models
- `src/models`: Data model and database foundations
- `src/collection`: Collection contracts and safety helpers
- `src/llm`: LLM client/cache/template scaffolding
- `src/dashboard`: Dashboard presentation entry scaffolding (Cycle 001)
- `src/reports`: Reporting placeholders (Cycle 001)
- `src/exports`: Export format placeholders and validation helper (Cycle 001)
- `src/playbook`: Seed payload shape guidance (Cycle 001)

## Safety/Data Handling

- Research collection is intended for read-only workflows only.
- Do not perform purchase, order, or any account-mutating marketplace actions.
- Keep secrets in `.env` and never commit credentials.
- Treat session/browser files as local runtime artifacts, not source-controlled assets.

## Testing

Use the standard project tooling:

```bash
pytest
ruff check README.md src tests
mypy src
```

For targeted Cycle 001 presentation tests:

```bash
pytest tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py -q
```

## Troubleshooting

- **`ModuleNotFoundError` during tests**: confirm `pip install -e .` succeeded in the active environment.
- **Playwright not available**: rerun `playwright install chromium`.
- **Type-check issues**: run `mypy src` and address reported annotations/import errors.
- **Lint issues**: run `ruff check README.md src tests` and fix style/import ordering.

## Current Build Status

Current state: **Cycle 001 foundation scaffolding**.

Implemented in this cycle:

- onboarding documentation and local setup guidance
- importable dashboard/report/export/playbook placeholder modules
- seed payload shape validation helper for onboarding/playbook workflows

Not yet implemented in this cycle:

- full Streamlit dashboard UX
- production reporting/export orchestration
- complete automated collection-to-recommendation pipeline
