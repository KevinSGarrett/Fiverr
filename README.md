# Fiverr Research System

## Overview

The Fiverr Research System is a local-first Python project for researching Fiverr niches,
keyword opportunities, and competitor positioning. The repository is
[https://github.com/KevinSGarrett/Fiverr](https://github.com/KevinSGarrett/Fiverr), and the
expected local workspace is `C:\Fiverr\Fiverr`.

Current implementation status is **Cycle 001 + Cycle 002 foundation scaffolding**. Core contracts,
validation, and operator workflow docs are in place, while end-to-end collection, scoring,
recommendation generation, and final dashboard/report UX remain future-cycle work.


## Current Build Status (Updated 2026-06-09)

> **Two-score model (corrected 2026-06-09):**
> - Internal Engineering Build Progress: ~67%
> - End-to-End Production-Grade Readiness: ~48-50% (range 46-52%)
> - These are NOT the same number. Do not conflate them.

### Latest Completed Cycle
**C074 — TierD-2 Live Collection Pilot + Wave 11 S8.3 Playbook Scaffold**
- TierD-2 infrastructure: collect-live, live-validate, PilotLogger
- Wave 11 S8.3: generate_playbook, 5-section playbook, Jinja2 PDF template
- All TierD-2 conditions A-J enforced in code
- User action required: python run.py live-validate --niche python_automation

### Completed Waves
- Wave 0-8: Foundation, data, scoring, analysis, recs, dashboard, pricing — **COMPLETE**
- Wave 9: Pricing Strategy Engine (S6.1-S6.8) — **COMPLETE** (C062-C065)
- Wave 10: Niche Discovery Engine (S7.1-S7.9) — **COMPLETE** (C066-C073, SCRUM-22 CLOSED)

### In Progress
- Wave 11: Gig Creation Playbook — **IN PROGRESS**
  - S8.3 Seller Setup Playbook Generator: **DONE** (C074)
  - S8.1 Gig Visual Analysis: **To Do** (C075)
  - S8.2 Seller Profile Optimization: **To Do** (C076)

### Key New Commands (C074)
`ash
# Controlled live collection pilot (TierD-2 approved, 500 credit limit)
python run.py collect-live --niche python_automation --budget 100

# Full end-to-end live validation pipeline
python run.py live-validate --niche python_automation

# Generate seller setup playbook
python run.py playbook python_automation
`


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

### PerimeterX Bypass (ScrapFly)

Fiverr can return PerimeterX challenge pages that block headless browser collection.
You can optionally route collection transport through ScrapFly for managed bypass:

1. Add `SCRAPFLY_API_KEY` to `.env`.
2. Set `collection.scrapfly.enabled: true` in `config.yaml`.
3. Run `python run.py collect-only`.

This is optional. When disabled, the system keeps the existing Playwright fallback behavior.
For full setup and architecture details, see `docs/collection/SCRAPFLY_INTEGRATION.md`.

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
- Steward agents should update an existing cycle PR instead of creating duplicates when one already exists.

Governance references for PR stewardship:

- `docs/CODEX_REVIEW_DISPOSITION.md`
- `docs/PR_CHECKS_AND_CODECOV.md`
- `docs/BRANCH_PROTECTION_AND_REQUIRED_CHECKS.md`

## Runtime Artifact Hygiene

- Runtime database files (for example, `data/*.db`) are local execution artifacts and remain outside tracked handoff contents.
- Do not include runtime DB files in repository handoff zip packages by default.
- If archival is required, export DB artifacts intentionally to an external archive location instead of bundling them in repo package outputs.

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
