# AGENT ROSTER — 4 Cursor AI Agents
# Updated: Cycle 019

---

## Agent A — Infrastructure & Foundation

| Attribute | Value |
|---|---|
| Role | Infrastructure Engineer |
| Epics | 01 (Foundation — lead), 10 (Integration — lead) |
| Owned Dirs | src/config/, src/models/, src/utils/, src/scripts/, src/orchestrator.py, src/recommendations/ |
| Also Owns | .github/, pyproject.toml, config.yaml, requirements.txt, .cursorrules |
| Test Dirs | tests/conftest.py, tests/unit/test_config.py, tests/unit/test_models.py, tests/unit/test_utils.py, tests/unit/test_utils_new.py |
| Label | agent:1-infrastructure |
| Skills | SQLAlchemy ORM, Pydantic v2, Click CLI, config management, database design |
| Jira scope | scope:epic01, scope:epic10 |

**Cycle 019 additions to Agent A scope:**
- `src/recommendations/` — E05 scaffold (contracts.py, orchestrator.py, __init__.py)
- `src/utils/datetime.py`, `validation.py`, `hashing.py`, `export.py` — new utility modules
- `src/models/associations.py`, `visual.py`, `discovery_cycle.py`, `auto_promotion.py`, `order.py`
- All `.github/` workflow and config files

---

## Agent B — Collection Engine

| Attribute | Value |
|---|---|
| Role | Collection Engineer |
| Epics | 02 (Collection — lead) |
| Owned Dirs | src/collection/ (all files and subdirectories including workflows/) |
| Test Dirs | tests/unit/test_collection.py, tests/unit/test_collection_pacing.py, tests/unit/test_proxy.py, tests/integration/test_collection_e2e.py |
| Label | agent:2-collection |
| Skills | Playwright, web scraping, CSS selectors, browser automation, async queues |
| Jira scope | scope:epic02 |

**Cycle 019 additions to Agent B scope:**
- `src/collection/workflows/` — 8 workflow class files (keyword_expansion, fiverr_search, gig_detail, seller_profile, google_trends, reddit_signals, autocomplete, auto_promotion)
- `src/collection/selectors.py` — VISUAL selector group added

---

## Agent C — Analysis, Scoring & Engines

| Attribute | Value |
|---|---|
| Role | Analysis & Scoring Engineer |
| Epics | 03 (Analysis), 04 (Scoring), 05 (Recommendations), 06 (Pricing), 07 (Discovery) |
| Owned Dirs | src/analysis/, src/scoring/, src/llm/, src/pricing/, src/discovery/ |
| Test Dirs | tests/unit/test_analysis.py, test_scoring.py, test_llm.py, test_template_renderer.py |
| Label | agent:3-analysis |
| Skills | LLM integration, mathematical scoring, clustering, Jinja2, data analysis |
| Jira scope | scope:epic03, scope:epic04, scope:epic05, scope:epic06, scope:epic07 |

**Cycle 019 additions to Agent C scope:**
- `src/llm/prompts/` — 13 E05 spec-named Jinja2 templates added (gig_titles.j2, tag_sets.j2, package_structure.j2, description_outline.j2, faq_entries.j2, differentiation_angle.j2, buyer_persona.j2, thumbnail_direction.j2, upsell_structure.j2, red_flags.j2, niche_viability.j2, pricing_strategy.j2, profile_optimization.j2)
- Template naming decision: use spec-named templates for E05 recommendation engine; do NOT rename or delete the 19 operational templates. See DL-026.

---

## Agent D — Dashboard, Playbook & UX

| Attribute | Value |
|---|---|
| Role | Dashboard & Presentation Engineer |
| Epics | 08 (Playbook), 09 (Dashboard & Reporting) |
| Owned Dirs | src/playbook/, src/dashboard/ (all files including pages/), src/reports/, src/exports/ |
| Test Dirs | tests/unit/test_playbook.py, test_dashboard.py, test_dashboard_queries.py, test_reports.py |
| Label | agent:4-dashboard |
| Skills | Streamlit, PDF gen, data visualization, UI components, export formats |
| Jira scope | scope:epic08, scope:epic09 |

**Cycle 019 additions to Agent D scope:**
- `src/dashboard/pages/` — 9 page stub files (opportunities.py, keywords.py, competitors.py, recommendations.py, pricing.py, discovery.py, playbook.py, run_history.py, llm_costs.py)
- `src/dashboard/_pages_legacy.py` — renamed from pages.py (legacy re-export)

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
| Recommendations scaffold | Agent A | Agent C (E05 impl) |
| Dashboard pages/ dir | Agent A | Agent D |

---

## Jira Access

All Cursor agents have operator-confirmed Jira read/write/edit access when explicitly instructed in their prompts.

**Allowed Jira operations when assigned:**
- Read/search Jira issues
- Create Jira issues
- Update issue descriptions
- Add comments (must follow JIRA_COMMENT_PROTOCOL.md format)
- Transition statuses
- Maintain changed-files-to-Jira mapping evidence
- Create rework/bug tickets from CI/QA/DOD findings

**Label format:** Always use numeric agent labels:
- `agent:1-infrastructure` (NOT agent:A)
- `agent:2-collection` (NOT agent:B)
- `agent:3-analysis` (NOT agent:C)
- `agent:4-dashboard` (NOT agent:D)

Agents must follow `04_jira_protocol/CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md`.

---

## .cursorrules Reference

The `.cursorrules` file at repo root is the primary architecture contract for all agents. Key rules:
- Line length: 100 characters (NOT 120 — see DL-029)
- All functions must have type annotations
- All new modules get dedicated test files in tests/unit/
- New models go in their own file (existing consolidated files are accepted per DL-025)
- Use src/collection/workflows/ for new workflow classes
- Use spec-named templates (Set 2) for E05 recommendation engine (see DL-026)
