# Fiverr Research System

## Overview

The Fiverr Research System is a local-first Python project for researching Fiverr niches,
keyword opportunities, and competitor positioning. The repository is
[https://github.com/KevinSGarrett/Fiverr](https://github.com/KevinSGarrett/Fiverr), and the
expected local workspace is `C:\Fiverr\Fiverr`.

Current implementation status is **Cycle 001 + Cycle 002 foundation scaffolding**. Core contracts,
validation, and operator workflow docs are in place, while end-to-end collection, scoring,
recommendation generation, and final dashboard/report UX remain future-cycle work.

## Prerequisites

- Python 3.11+
- `pip` available in your shell
- Git clone at `C:\Fiverr\Fiverr`
- Optional virtual environment tooling (`venv`)

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
3. Review `config.yaml` defaults before running workflows.

`.env` is never committed. Browser/session artifacts are local runtime files and are git-ignored
(for example: `playwright/.auth/`, `storage_state.json`, `*.session`, `data/sessions/`).

## Running

Cycle 002 provides import-safe scaffolding and validation contracts. It does not provide a fully
implemented production dashboard or end-to-end automated research execution.

Use these command patterns from the repo root:

```bash
python run.py config-check --config-path config.yaml
python run.py init-db
python run.py smoke --config-path config.yaml
```

## Current Foundation Commands

```bash
python run.py config-check --config-path config.yaml
python run.py init-db
python run.py smoke --config-path config.yaml
python -m pytest
python -m ruff check src tests README.md
python -m mypy src
```

## Architecture

Current foundation modules:

- `src/config`: Configuration loading and validation models
- `src/models`: Data model and database foundations
- `src/collection`: Collection contracts and safety-first scaffolding
- `src/llm`: LLM client/cache/template scaffolding
- `src/dashboard`: Import-safe dashboard shell contracts
- `src/reports`: Report template and run-summary contracts
- `src/exports`: Export request/manifest contracts and path validation
- `src/playbook`: Seed payload guidance and validation helpers

## Safety and Data Handling

- Collection workflows are currently safe scaffolding and contract layers.
- Do not perform purchase/order/account-mutating marketplace actions.
- Keep secrets in `.env` and never commit credentials.
- Treat session/browser files as local runtime artifacts.

## Testing

Standard checks:

```bash
python -m ruff check src tests README.md
python -m mypy src
python -m pytest
```

Targeted dashboard/report/playbook checks:

```bash
python -m pytest tests/unit/test_dashboard.py tests/unit/test_reports.py tests/unit/test_playbook.py -q
```

## Branching and Release Workflow

- Agents commit locally to cycle branches (for example: `cycle/002/integration`).
- Agent D (or PM-assigned steward agent) performs final branch checks, push, and PR prep.
- Human operator/PM provides review and approval oversight.
- Pull requests target `develop`.
- `main` is release-only and receives changes through release process only.
- Do not push directly to `main`.

## Known Current Limitations

- Collection, scoring, and recommendations are not production-complete and remain staged as safe
  scaffolding contracts.
- Dashboard pages are shell-level metadata and navigation contracts, not a finished UX.
- Reporting/export structures define interfaces and validation, not final artifact generation.

## Troubleshooting

- **`ModuleNotFoundError` during tests**: confirm `pip install -e .` in your active environment.
- **Playwright not available**: rerun `playwright install chromium`.
- **Type-check issues**: run `python -m mypy src` and fix reported annotations/imports.
- **Lint issues**: run `python -m ruff check src tests README.md` and fix reported issues.
