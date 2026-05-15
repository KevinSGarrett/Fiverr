# AI Agent Roles
# Fiverr Research System — 4 Cursor Agents + ChatGPT PM

---

## Team Structure

```
┌─────────────────────────────────┐
│   ChatGPT — Project Manager     │
│   Creates issues, coordinates   │
│   Reviews progress, decisions   │
└──────────────┬──────────────────┘
               │ assigns tasks via GitHub Issues
    ┌──────────┼──────────┬──────────────┐
    ▼          ▼          ▼              ▼
┌────────┐ ┌────────┐ ┌────────┐  ┌────────┐
│Agent 1 │ │Agent 2 │ │Agent 3 │  │Agent 4 │
│Infra   │ │Collect │ │Analyze │  │Dashbrd │
└────────┘ └────────┘ └────────┘  └────────┘
```

---

## ChatGPT — Project Manager

### Responsibilities
| Area | Tasks |
|---|---|
| Planning | Break epics into stories, create GitHub issues for each story |
| Assignment | Assign issues to agents via `agent:*` labels |
| Coordination | Sequence dependent stories, manage cross-agent handoffs |
| Review | Review PR descriptions, flag architecture concerns |
| Decisions | Make design decisions when agents are blocked |
| Progress | Track epic completion, update epic tracker issues |
| Quality | Verify spec compliance by reviewing PR descriptions against project-pack docs |

### Workflow
```
1. PM creates epic tracker issue (using epic.yml template)
2. PM breaks epic into story issues (using task.yml template)
3. PM assigns each story to an agent (agent label)
4. PM sets priority and dependencies in issue body
5. Agents work, create PRs, link PRs to issues
6. PM monitors PRs for blocking issues or questions
7. PM marks story issues complete when PRs merge
8. PM updates epic tracker checklist
9. PM creates release PR when all stories done
```

### PM Communication Format
PM communicates via GitHub issue comments:
```markdown
@agent-3 Story S4.1 is ready to start. Dependencies:
- ✅ #12 Database models (merged)
- ✅ #18 Config system (merged)

Spec: project-pack/05_scoring/DEMAND_SCORE.md
Branch: feature/epic04/S4.1-demand-score
Priority: P3

Please confirm when starting.
```

---

## Agent 1 — Infrastructure & Foundation

### Primary Epics
- **Epic 01** — Foundation & Infrastructure (sole owner)
- **Epic 10** — Integration, Testing & Launch (lead)
- Cross-cutting: CI/CD, dependencies, configuration

### Owned Directories
```
src/config/
src/models/
src/utils/
src/scripts/
src/llm/ (initial setup, then handoff to Agent 3)
.github/
tests/conftest.py
```

### Key Skills
- SQLAlchemy ORM modeling
- Pydantic configuration
- CLI design (Click/Typer)
- GitHub Actions workflows
- Python project tooling (pyproject.toml, Ruff, Mypy)

### Branch Pattern
```
feature/epic01/S1.X-description
chore/ci/description
chore/deps/description
feature/epic10/S10.X-description
```

---

## Agent 2 — Collection Engine

### Primary Epics
- **Epic 02** — Collection Engine (sole owner)

### Owned Directories
```
src/collection/
src/collection/workflows/
data/seeds/
data/browser_profile/
```

### Key Skills
- Playwright browser automation
- CSS selector engineering
- Rate limiting and pacing
- Checkpoint/resume logic
- Proxy management
- Web scraping patterns

### Branch Pattern
```
feature/epic02/S2.X-description
fix/epic02/description
```

### Special Considerations
- Most fragile code (depends on Fiverr's DOM structure)
- Highest risk of external breakage (site changes)
- Requires most frequent selector updates post-launch
- Should include screenshot captures for debugging

---

## Agent 3 — Analysis, Scoring & Recommendations

### Primary Epics
- **Epic 03** — Analysis Engine
- **Epic 04** — Scoring Engine
- **Epic 05** — Recommendation Engine
- **Epic 06** — Pricing Engine
- **Epic 07** — Discovery Engine

### Owned Directories
```
src/analysis/
src/scoring/
src/llm/prompts/ (after initial setup by Agent 1)
src/llm/template_renderer.py
src/pricing/
src/discovery/
```

### Key Skills
- Mathematical scoring models
- LLM prompt engineering (Jinja2)
- Statistical analysis (KDE, clustering)
- OpenAI API integration
- Algorithm design

### Branch Pattern
```
feature/epic03/S3.X-description
feature/epic04/S4.X-description
feature/epic05/S5.X-description
feature/epic06/S6.X-description
feature/epic07/S7.X-description
```

### Special Considerations
- Highest volume of PRs (5 epics)
- Must follow scoring specs exactly (formulas, weights, thresholds)
- LLM prompts need careful testing (output quality varies)
- Should not start until Agent 1 completes Epic 01 foundation

---

## Agent 4 — Dashboard, Playbook & UX

### Primary Epics
- **Epic 08** — Playbook Engine
- **Epic 09** — Dashboard & Reporting

### Owned Directories
```
src/playbook/
src/dashboard/
src/dashboard/pages/
src/reports/
src/exports/
docs/
```

### Key Skills
- Streamlit application development
- Data visualization
- PDF generation (WeasyPrint)
- UI/UX design
- Export format handling

### Branch Pattern
```
feature/epic08/S8.X-description
feature/epic09/S9.X-description
```

### Special Considerations
- Can start playbook work (Epic 08) after scoring is available
- Dashboard depends on most other modules (queries, components, data)
- Should create mock data fixtures for development until real data exists
- Design system must be consistent across all pages

---

## Agent Parallelism Matrix

Shows which agents can work simultaneously:

| Phase | Agent 1 | Agent 2 | Agent 3 | Agent 4 |
|---|---|---|---|---|
| Phase 1 (Epic 01) | **Active** | Waiting | Waiting | Waiting |
| Phase 2 (Epic 02-03) | CI/deps support | **Active** (E02) | **Active** (E03) | Start mock fixtures |
| Phase 3 (Epic 04-06) | Support | Selector updates | **Active** (E04-06) | **Active** (E08) |
| Phase 4 (Epic 07-09) | Support | Support | **Active** (E07) | **Active** (E09) |
| Phase 5 (Epic 10) | **Lead** | Testing support | Testing support | Testing support |
