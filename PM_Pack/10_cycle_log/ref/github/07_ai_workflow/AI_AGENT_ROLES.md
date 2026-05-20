# AI AGENT ROLES AND DIRECTORY OWNERSHIP
# Updated: Cycle 019

---

## Agent Ownership Map

### Agent A — Infrastructure & Foundation
**Label:** `agent:1-infrastructure`
**Epics:** E01, E10

Owned directories and files:
- `src/config/` — all configuration modules
- `src/models/` — all DB models (30 tables across multiple files)
- `src/utils/` — datetime.py, validation.py, hashing.py, export.py (all 4 new modules)
- `src/scripts/` — init_db.py and maintenance scripts
- `src/orchestrator.py` — pipeline orchestrator and CLI modes
- `src/recommendations/` — E05 scaffold (contracts.py, orchestrator.py, __init__.py)
- `.github/` — all workflow and config files
- `pyproject.toml`, `config.yaml`, `requirements.txt`, `.cursorrules`
- `tests/unit/test_config.py`, `test_models.py`, `test_utils.py`, `test_utils_new.py`

### Agent B — Collection Engine
**Label:** `agent:2-collection`
**Epics:** E02

Owned directories:
- `src/collection/` — ALL files and subdirectories
  - `src/collection/workflows/` — 8 workflow class files
  - `src/collection/selectors.py` — includes VISUAL selector group
- `tests/unit/test_collection.py`, `test_collection_pacing.py`, `test_proxy.py`
- `tests/integration/test_collection_e2e.py`

### Agent C — Analysis, Scoring & Engines
**Label:** `agent:3-analysis`
**Epics:** E03, E04, E05, E06, E07

Owned directories:
- `src/analysis/` — analysis engine modules
- `src/scoring/` — all 11 score calculators
- `src/llm/` — LLM client, cache, and ALL Jinja2 templates (both sets)
- `src/pricing/` — pricing intelligence
- `src/discovery/` — discovery engine
- `tests/unit/test_analysis.py`, `test_scoring.py`, `test_llm.py`, `test_template_renderer.py`

**Template note:** Agent C owns ALL templates in src/llm/prompts/. Both the 19 operational templates and the 13 E05 spec-named templates are Agent C's responsibility. See DL-026.

### Agent D — Dashboard, Playbook & UX
**Label:** `agent:4-dashboard`
**Epics:** E08, E09

Owned directories:
- `src/dashboard/` — ALL files including pages/ subdirectory
  - `src/dashboard/pages/` — 9 page stub files awaiting E09 implementation
  - `src/dashboard/_pages_legacy.py` — legacy re-export
- `src/playbook/` — playbook generator
- `src/reports/` — report generation
- `src/exports/` — export formatters
- `tests/unit/test_dashboard.py`, `test_dashboard_queries.py`, `test_playbook.py`, `test_reports.py`

---

## Cross-Agent Rules

1. No agent modifies files owned by another agent without explicit PM instruction
2. If an agent needs data from another agent's module, it imports — it does not modify
3. Agent A's models are the foundation — all other agents depend on them
4. Agent B's collection data is the input to Agent C's analysis
5. Agent C's scoring output is the input to Agent D's dashboard

---

## Jira Ownership by Agent

| Agent | Default Jira Keys |
|---|---|
| Agent A | E01 stories, E10 stories, CI/GitHub governance tickets |
| Agent B | E02 stories, collection-related bugs |
| Agent C | E03, E04, E05, E06, E07 stories |
| Agent D | E08, E09 stories, dashboard/export bugs |
| PM | Governance tickets (SCRUM-440, SCRUM-441, SCRUM-442) |
