# AGENT REVIEW PROTOCOL
# Step-by-step review process for each agent type

---

## Universal Review Steps (all agents)

1. **Verify file existence** — Check every file in the agent's FILES CREATED table
2. **Run lint** — ruff check on all agent directories
3. **Run type check** — mypy on all agent directories
4. **Run tests** — pytest on all agent test files
5. **Spec compliance** — Compare implementation against referenced spec doc
6. **DOD verification** — Check each DOD criterion from the prompt
7. **Score confidence** — Apply CONFIDENCE_SCORING.md rubric

---

## Agent A (Infrastructure) — Additional Checks
- Database models: verify all 28 tables from SCHEMA.md are represented
- Config system: verify all niche profiles load correctly
- CLI: verify all commands are registered and --help works
- Migrations: verify init_db creates all tables without errors
- Cross-agent impact: other agents import from Agent A's code — verify imports work

## Agent B (Collection) — Additional Checks
- Playwright: verify browser launch and page navigation
- Selectors: verify CSS selectors match current Fiverr page structure
- Pacing: verify delays and rate limiting per PACING_MODEL.md
- Checkpoints: verify checkpoint save/resume works
- Retry logic: verify retry with exponential backoff

## Agent C (Analysis/Scoring) — Additional Checks
- Score formulas: verify math matches spec exactly (spot-check with sample data)
- LLM prompts: verify Jinja2 templates render correctly
- Weights: verify scoring weight profiles match SCORING_SYSTEM.md
- Clustering: verify output format matches KEYWORD_CLUSTERING.md
- Null handling: verify graceful handling of missing/null data

## Agent D (Dashboard) — Additional Checks
- Streamlit pages: verify pages render without errors
- Charts: verify data visualization renders with sample data
- Export: verify PDF/XLSX/JSON exports produce valid files
- Navigation: verify sidebar navigation works
- Responsive: verify layout adapts to different widths
