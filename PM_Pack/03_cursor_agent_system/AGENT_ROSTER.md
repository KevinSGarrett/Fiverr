# AGENT ROSTER — 4 Cursor AI Agents

---

## Agent A — Infrastructure & Foundation

| Attribute | Value |
|---|---|
| Role | Infrastructure Engineer |
| Epics | 01 (Foundation — lead), 10 (Integration — lead) |
| Owned Dirs | src/config/, src/models/, src/utils/, src/scripts/, src/orchestrator.py |
| Also Owns | .github/, pyproject.toml, config.yaml, requirements.txt, .cursorrules |
| Test Dirs | tests/conftest.py, tests/unit/test_config.py, tests/unit/test_models.py |
| Label | agent:1-infrastructure |
| Skills | SQLAlchemy ORM, Pydantic v2, Click CLI, config management, database design |

## Agent B — Collection Engine

| Attribute | Value |
|---|---|
| Role | Collection Engineer |
| Epics | 02 (Collection — lead) |
| Owned Dirs | src/collection/ (all files and subdirectories) |
| Test Dirs | tests/unit/test_collection.py, tests/integration/test_collection_e2e.py |
| Label | agent:2-collection |
| Skills | Playwright, web scraping, CSS selectors, browser automation, async queues |

## Agent C — Analysis, Scoring & Engines

| Attribute | Value |
|---|---|
| Role | Analysis & Scoring Engineer |
| Epics | 03 (Analysis), 04 (Scoring), 05 (Recommendations), 06 (Pricing), 07 (Discovery) |
| Owned Dirs | src/analysis/, src/scoring/, src/llm/, src/pricing/, src/discovery/ |
| Test Dirs | tests/unit/test_analysis.py, test_scoring.py, test_llm.py, test_pricing.py, test_discovery.py |
| Label | agent:3-analysis |
| Skills | LLM integration, mathematical scoring, clustering, Jinja2, data analysis |

## Agent D — Dashboard, Playbook & UX

| Attribute | Value |
|---|---|
| Role | Dashboard & Presentation Engineer |
| Epics | 08 (Playbook), 09 (Dashboard & Reporting) |
| Owned Dirs | src/playbook/, src/dashboard/, src/reports/, src/exports/ |
| Test Dirs | tests/unit/test_playbook.py, test_dashboard.py, test_reports.py |
| Label | agent:4-dashboard |
| Skills | Streamlit, PDF gen, data visualization, UI components, export formats |

---

## Cross-Agent Dependencies

| Dependency | Provider | Consumer |
|---|---|---|
| Database models | Agent A | All agents |
| Config system | Agent A | All agents |
| CLI entry points | Agent A | All agents |
| LLM client | Agent C | Agent C, D |
| Scoring output | Agent C | Agent D (dashboard) |
| Collection data | Agent B | Agent C (analysis) |


---

## Jira Access

All Cursor agents have operator-confirmed Jira read/write/edit access when explicitly instructed in their prompts.

Allowed Jira operations when assigned:
- read/search Jira issues,
- create Jira issues,
- update issue descriptions,
- add comments,
- transition statuses,
- maintain changed-files-to-Jira mapping evidence,
- create rework/bug tickets from Codex, CI, QA, or DOD findings.

Agents must follow `Project_Manager/04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md`.
