# Decision Log
# Fiverr Research System

**Last Updated:** Post-Wave 20 Import + Niche Expansion + Category Verification

---

## DL-001 — Language: Python as Core Runtime
| Field | Value |
|---|---|
| Decision | Python 3.11+ is the primary language for all automation, collection, analysis, scoring, and reporting pipelines. |
| Wave Decided | 0 |

## DL-002 — Browser Automation: Playwright with Full Authenticated Session Support
| Field | Value |
|---|---|
| Decision | Playwright (Python bindings) for all browser-based collection. Full authenticated sessions using the user's own Fiverr account via persistent browser context. Authenticated mode is the default. All browsing at natural human rate with human-event simulation. |
| Wave Decided | 0 Rev 3 |

## DL-003 — Primary Database: SQLite → PostgreSQL
| Field | Value |
|---|---|
| Decision | SQLite for v1. PostgreSQL for v2+. SQLAlchemy abstraction makes migration low-friction. |
| Wave Decided | 0 |

## DL-004 — ORM / Schema: SQLAlchemy 2.0 + Pydantic v2
| Field | Value |
|---|---|
| Decision | SQLAlchemy Core + ORM for database models. Pydantic v2 for validation schemas. |
| Wave Decided | 0 |

## DL-005 — Job Scheduling: APScheduler v1, Celery + Redis v2
| Field | Value |
|---|---|
| Decision | APScheduler for v1 in-process scheduling. Celery + Redis for v2 distributed queuing. |
| Wave Decided | 0 |

## DL-006 — Dashboard: Streamlit v1, React + FastAPI v2
| Field | Value |
|---|---|
| Decision | Streamlit for v1 analytics dashboard. React + FastAPI for polished v2 local web application. |
| Wave Decided | 0 |

## DL-007 — LLM Integration: Multi-Model OpenAI Strategy
| Field | Value |
|---|---|
| Decision | OpenAI API integrated across every pipeline stage where it adds value. Different models per stage: gpt-4o for strategic/nuanced tasks, gpt-4o-mini for high-volume tasks, text-embedding-3-small for embeddings. Ollama as offline alternative. |
| Wave Decided | 0 Rev 3 |

## DL-008 — Automation Model: Natural-Rate Human-Paced
| Field | Value |
|---|---|
| Decision | All collection pipelines operate with configurable pacing delays, randomized inter-request intervals, human-event simulation (scroll, hover, read delays, randomized click timing), checkpoint-based resumability. |
| Wave Decided | 0 Rev 3 |

## DL-009 — Data Freshness: TTL-Based Staleness Tracking
| Field | Value |
|---|---|
| Decision | Every collected record stores collected_at and ttl_hours. Stale records re-queued automatically. LLM cache TTL matches source data TTL. |
| Wave Decided | 0 |

## DL-010 — Scoring: Weighted Composite with Confidence Modifier
| Field | Value |
|---|---|
| Decision | Final Recommendation Score = weighted composite of 10 sub-scores × Confidence Modifier (0.0–1.0). All weights configurable in config.yaml. Named scoring profiles supported. |
| Wave Decided | 0 |

## DL-011 — LLM Model Assignment: Full Stage-by-Stage Table

| Stage | Task | Model |
|---|---|---|
| Stage 1 | Niche expansion brainstorm | gpt-4o-mini |
| Stage 2 | Keyword expansion, variants, intent classification | gpt-4o-mini |
| Stage 2 | Semantic keyword embeddings | text-embedding-3-small |
| Stage 6 | Reddit demand intent parsing | gpt-4o-mini |
| Stage 7 | Gig title quality scoring | gpt-4o-mini |
| Stage 7 | Description quality + weakness detection | gpt-4o |
| Stage 7 | Thumbnail, FAQ assessment | gpt-4o-mini |
| Stage 8 | Seller bio authority parsing | gpt-4o-mini |
| Stage 8 | Competitor cluster synthesis + weakness IDs | gpt-4o |
| Stage 9 | Cluster theme labeling | gpt-4o-mini |
| Stage 9 | Cluster opportunity narrative | gpt-4o |
| Stage 13 | Gig title variants, package structure, description draft, differentiation, red flags, viability | gpt-4o |
| Stage 13 | Tag sets, FAQ entries, buyer persona, thumbnail direction, upsell structure | gpt-4o-mini |
| Stage 14 | Score explanations, competitor landscape summaries | gpt-4o |
| Stage 14 | Trend, saturation narratives | gpt-4o-mini |
| Stage 15 | Run summary | gpt-4o-mini |

**Wave Decided:** 0 Rev 3

## DL-012 — Fiverr Session: Authenticated via Playwright storage_state()
| Field | Value |
|---|---|
| Decision | User's own Fiverr account for all authenticated collection. Playwright persistent context saves/restores session cookies. First run headed (user logs in manually), subsequent runs headless. Auto-refresh on session expiry. |
| Wave Decided | 0 Rev 3 |

## DL-013 — LLM Caching: SQLite Prompt-Hash Cache
| Field | Value |
|---|---|
| Decision | All LLM calls cached in SQLite llm_cache table. Key = SHA-256(model + temperature + prompt). TTL matches source data TTL. Estimated 60–80% cost reduction on re-runs. |
| Wave Decided | 0 Rev 3 |

## DL-014 — LLM Structured Output: JSON Mode + Pydantic + Self-Correction
| Field | Value |
|---|---|
| Decision | All LLM calls returning structured data use OpenAI JSON mode. Responses parsed into typed Pydantic models. On parse failure: self-correction retry once, then null + confidence decrement. |
| Wave Decided | 0 Rev 3 |

## DL-015 — LLM Cost Monitoring and Alerting
| Field | Value |
|---|---|
| Decision | Token usage logged per call in llm_usage_logs table. Daily and monthly spend tracked. Configurable alert threshold in config.yaml. Dashboard LLM cost view included. |
| Wave Decided | 0 Rev 3 |

---

## DL-016 — Niche Set: Locked from Waves 1–20 (Tier 1 — 4 Niches)
| Field | Value |
|---|---|
| Decision | The four Tier 1 niches are locked from 20 waves of prior manual research and must not be redesigned. PRD is the primary launch and research target. Support-KB, Gumloop/Lindy, and MCP are gated per Wave 20 sequencing rules. |
| Niches | PRD / AI SaaS MVP Roadmap (Slot 1), Support-KB Readiness (Slot 2), Gumloop/Lindy Workflow (Slot 3), MCP Server Integration (Slot 4) |
| Source | Fiverr_Master_Cumulative_Rehydration_Waves_01_20_2026-05-06.md + Cumulative Workbook |
| Wave Decided | 0 — Niche Import |

## DL-017 — Seed Keywords: Imported from Wave 3–20 Research (Tier 1)
| Field | Value |
|---|---|
| Decision | Tier 1 seed keywords initialized from Wave 3–10 market count and demand validation research. Used as default seeds in config.yaml. |
| PRD seeds | "product requirements document", "AI SaaS PRD", "MVP PRD", "technical roadmap AI", "SaaS roadmap", "AI product roadmap" |
| Support-KB seeds | "support knowledge base AI", "chatbot handoff document", "help center AI readiness", "support KB audit" |
| Gumloop/Lindy seeds | "Gumloop workflow", "Lindy AI automation", "AI workflow automation", "no-code AI workflow" |
| MCP seeds | "MCP server integration", "AI agent integration", "model context protocol", "MCP tool integration" |
| Wave Decided | 0 — Niche Import |

## DL-018 — Niche Gating Logic: Research Depth by Priority
| Field | Value |
|---|---|
| Decision | PRD (Slot 1): full collection depth every run. Support-KB (Slot 2): keyword + search only until PRD signal established. Gumloop/Lindy (Slot 3): keyword + search only until sandbox proof gate. MCP (Slot 4): feasibility research mode. All Tier 2 niches: standard depth on every run. Config key: collection.niche_depth (full / standard / keyword_only / feasibility) |
| Wave Decided | 0 — Niche Import |

## DL-019 — Revenue Model: Imported from Wave 19–20
| Field | Value |
|---|---|
| Decision | Wave 19–20 delayed-AOV ramp model is the authoritative financial framework. Month 1–3 AOV is $95–$175 (trust-building). Month 6+ AOV rises to $300+ as proof/trust accumulates. Premium AOV ($700–$1,250) post-trust custom offers only. |
| Target Net | $30,000 after Fiverr 20% share |
| Required Gross | $37,500 |
| Base Model Gross | $40,560 |
| Base Orders | 74 |
| Weighted Gross AOV | $548 |
| Monthly Gates | Month 4: $1,720 | Month 6: $4,770 | Month 9: $17,795 | Month 10: $25,045 | Month 12: $37,500+ |
| Wave Decided | 0 — Niche Import |

## DL-020 — Custom Offer Gates by Trust Stage
| Reviews | Custom Offer Ceiling |
|---|---|
| 0 reviews | $250–$400 |
| 1–4 clean orders | $400–$650 |
| 5+ orders / Level 1 | $650–$900 |
| 10+ reviews | $900–$1,200 |
| 25+ reviews | $1,200–$1,500+ |

**Wave Decided:** 0 — Niche Import

---

## DL-021 — Expanded Portfolio: 5 New Tier 2 Niches Added
| Field | Value |
|---|---|
| Decision | Five additional Tier 2 niches added based on user's Python/AI/automation skill set. All align with verified high-demand Fiverr categories. All run in parallel with standard research depth. After 3 automated runs, the system auto-promotes highest-scoring Tier 2 niches to full depth. |
| Niches Added | Python Automation Scripts (Slot 5), AI Tool / LLM App Integration (Slot 6), AI Agent Development (Slot 7), Workflow Automation n8n/Make/Zapier (Slot 8), Python Web Scraping / Data Scripts (Slot 9) |
| Selection Rationale | See DL-022 |
| Wave Decided | 0 — Niche Expansion |

## DL-022 — Tier 2 Niche Selection Rationale
| Niche | Why Selected | Fiverr Demand Signal | Skill Fit |
|---|---|---|---|
| Python Automation Scripts | Highest volume Python gig type on Fiverr. Short deliveries ($50–$250), recurring buyers, fast portfolio builder. Python is the #1 searched language in programming-tech. | fiverr.com/categories/programming-tech/buy/web-programming-services/python confirms active high-volume market | Direct match |
| AI Tool / LLM App Integration | Fastest-growing AI subcategory on Fiverr (confirmed from live category pages). Strong AOV ($95–$450+). Buyers are businesses integrating OpenAI/Claude/Gemini into their products. | fiverr.com/categories/programming-tech/ai-coding/ai-integrations — confirmed active category | Direct match |
| AI Agent Development | Highest AOV in the entire AI coding category ($125–$550+). Buyers are technical but need implementation help. Confirmed active subcategory with strong demand signals. | fiverr.com/categories/programming-tech/ai-coding/ai-agents-development — confirmed active | Direct match |
| Workflow Automation (n8n/Make/Zapier) | Confirmed high-demand subcategory with avg pricing $120–$140 per project. Blueprint/sandbox scope keeps delivery feasible. Complements the Gumloop/Lindy niche. | fiverr.com/categories/programming-tech/software-development/automations-workflows — confirmed active | Direct match |
| Python Web Scraping / Data Scripts | Huge consistent demand, fast deliveries, easy to scope. Pairs naturally with Python Automation. Common entry point that leads to repeat business and upsells. | Confirmed under fiverr.com/categories/programming-tech/buy/web-programming-services/python | Direct match |
| **Niches NOT selected** | AI mobile app dev (requires mobile expertise), AI consulting (too broad/vague without proof), ML model training (hardware-intensive, hard to scope for freelance), full-stack dev (too generic, oversaturated) | | |

**Wave Decided:** 0 — Niche Expansion

## DL-023 — Fiverr Category Paths: Verified from Live Fiverr URLs
| Field | Value |
|---|---|
| Decision | Category paths for all 9 niches verified via live Fiverr URL research (2026-05-11). These are the paths the collection system targets for category browsing and search result collection. Authenticated in-app service type field verification still recommended when creating gigs. |
| PRD | programming-tech/ai-coding/AI-Technology-Consulting (primary) OR writing-translation/technical-writing (alternative) |
| Support-KB | writing-translation/technical-writing |
| Gumloop/Lindy | programming-tech/software-development/automations-workflows |
| MCP | programming-tech/ai-coding/ai-agents-development (primary) OR programming-tech/ai-coding/ai-integrations (alternative) |
| Python Automation | programming-tech/buy/web-programming-services/python |
| AI Tool / LLM Integration | programming-tech/ai-coding/ai-integrations |
| AI Agent Dev | programming-tech/ai-coding/ai-agents-development |
| Workflow Automation | programming-tech/software-development/automations-workflows |
| Python Web Scraping | programming-tech/buy/web-programming-services/python", "AI assistant development", "agentic AI" |
| Workflow Automation | "n8n automation", "Make automation", "Zapier automation", "workflow automation", "business process automation", "no-code automation workflow" |
| Python Web Scraping | "Python web scraping", "web scraper Python", "data scraping script", "BeautifulSoup scraper", "website data extraction", "Python data scraper" |
| Wave Decided | 0 — Niche Expansion |

---

## Future Decision Slots
DL-025 through DL-099 reserved for Wave 1–8 decisions.

---

## DL-025 — Model Consolidation: Multiple Models Per File
| Field | Value |
|---|---|
| Decision | DB models are consolidated into thematic files (market.py, analysis.py, scoring.py, runtime.py, visual.py, etc.) rather than one file per model. |
| Rationale | Reduces file count and import complexity during foundation phase. All models in a group share mixins and related FK relationships. |
| Impact | .cursorrules rule updated: new models go in their own file; existing consolidated model files are an accepted deviation. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted — do not refactor existing files |

## DL-026 — Jinja2 Template Naming: Dual Set
| Field | Value |
|---|---|
| Decision | Two sets of Jinja2 templates coexist in src/llm/prompts/: (1) 19 operational templates for E02/E03/E06/E07; (2) 13 E05 spec-named templates for the recommendation engine. Both sets are kept. |
| Rationale | Operational templates are in active use. The 13 E05 templates use spec-defined filenames called by exact name from the recommendation engine. |
| Impact | Do NOT delete or rename either set. For E05 Story 5.4: use the 13 spec-named templates only. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |

## DL-027 — Collection Module Pattern: Functional with Workflow Wrappers
| Field | Value |
|---|---|
| Decision | Collection engine uses functional modules plus thin workflow wrapper classes in src/collection/workflows/. Spec-name aliases (SessionManager, QueueProcessor) exposed in src/collection/__init__.py. |
| Rationale | Functional approach adopted early. Wrapper classes satisfy spec interface contract. |
| Impact | New collection workflows must be class files in src/collection/workflows/. Existing functional modules remain. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |

## DL-028 — Sub-Task Deferral: 600 Tasks Not in Jira
| Field | Value |
|---|---|
| Decision | 600 granular spec tasks (from ref/todo/EPIC_*.md) are not created as Jira sub-tasks. Only E01's 65 sub-tasks exist. |
| Rationale | Creating 600 Jira issues is operationally expensive. Protocol defers bulk sub-task creation to per-epic wave imports. |
| Impact | PM plans at story level, not task level, until sub-tasks are wave-imported. Create sub-tasks per epic as active development begins. |
| Wave Decided | Protocol design — Cycle 019 |
| Status | Accepted |

## DL-029 — Line Length: 100 Characters
| Field | Value |
|---|---|
| Decision | Line length is 100 characters in pyproject.toml and .cursorrules. The original spec specified 120 — overridden. |
| Rationale | 100 chars is the existing CI-enforced setting. Changing would require reformatting all existing code. |
| Impact | All agents must format at 100 chars. Deployed .cursorrules reflects 100. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |

## DL-030 — PR Template: Operational Cycle Format
| Field | Value |
|---|---|
| Decision | .github/pull_request_template.md retains the operational 91-line cycle-based format rather than the 26-line spec format. |
| Rationale | Cycle-based format includes board audit artifacts, Jira keys, and validation sections essential for ChatGPT PM + Cursor agent workflow. |
| Impact | Spec PR template (ref/github/05_templates/PR_TEMPLATE.md) retained as reference only. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |

## DL-031 — Branch Naming: Cycle Integration Pattern
| Field | Value |
|---|---|
| Decision | Integration branches use cycle/{NNN}/integration. Individual story branches use feature/epic{NN}/SCRUM-{key}-{slug}. |
| Rationale | Cycle integration branch consolidates all agent work for a cycle. This is an operational necessity the spec branch naming doesn't account for. |
| Impact | .cursorrules documents both patterns. ChatGPT PM must specify the correct pattern in every agent prompt. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |

## DL-032 — Commit Scope: Cycle vs Module
| Field | Value |
|---|---|
| Decision | Commits in cycle integration branches use cycle-{NNN} scope. Individual story commits use module scope (models, collection, scoring, etc.). |
| Rationale | Cycle-scoped commits make it easy to find all work in a given cycle in git log. Module-scoped commits preferred for individual story PRs. |
| Impact | PM should instruct agents to use module scope on story branches and cycle scope only on integration branch commits. |
| Wave Decided | Cycle 019 — Audit Remediation |
| Status | Accepted |
