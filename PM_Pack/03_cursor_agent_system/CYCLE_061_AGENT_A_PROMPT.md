# CYCLE 061 â€” AGENT A PROMPT
# Role: Planner, Jira scaffolder, handoff package author
# Cycle: Post-SRDI Production Hardening (Wave M)
# Branch to create: cycle/061/integration FROM develop
# Base SHA: 09bb6db360462b4d6477571e6109dbc94a647b02
# Strategy doc: C:\Fiverr\Fiverr\PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md
# Full project plan: C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\ (all 14 tracks)

====================================================================
TASK 0 (FIRST -- before any other action): SHA RESOLUTION
====================================================================

BEFORE reading the hydration header or doing anything else:
Run the SHA resolver script:
  C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\SHA_RESOLVER_SCRIPT.ps1
  Parameters: -CycleNum "061" -PlaceholderPRNum "69"
After: Select-String '\[C0\d\d_SQUASH_SHA\]' in all 6 prompts -> must show zero matches.
Record the result. Only then proceed.

====================================================================
STAGE ORDER (definitive -- sec12.2)
====================================================================

Stage 1: Agent A (YOU -- solo, no other agent starts until you push and PR is open)
Stage 2: Agent B + Agent E (PARALLEL -- both simultaneously)
Stage 3: Agent C (after BOTH B AND E complete -- NEVER after F)
Stage 4: Agent F (after Agent C issues GO verdict)
Stage 5: Agent D (after ALL of A, B, E, C, F complete)

====================================================================
PROJECT CONTEXT
====================================================================

Working dir: C:\Fiverr\Fiverr
Python: C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe (use py -3.12)
Jira: kevinsgarrett.atlassian.net | Project: SCRUM | Cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
  Done transition id: 41 | Connector auth only (NEVER paste tokens)
GitHub: KevinSGarrett/Fiverr | Connector auth only
Git via Invoke-Exe ProcessStartInfo (never call operator -- returns empty on this machine)

9 niche_ids (canonical):
  prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent, python_automation,
  ai_tool_llm_integration, ai_agent_development, workflow_automation, python_web_scraping

VERIFIED STARTING STATE (develop @ 09bb6db):
  Suite: 4022 passed | Coverage: 95.58% | Pack: 41 names (sec7 v2.4)
  Golden: kw=110 = 62.7/1.0/CONDITIONAL_GO | kw=96 = 35.8 | kw=3 = 56.66
  Toggles: scrapfly=false, external_signals_enabled=false, llm_relevance_enabled=false
  SRDI: ALL R1-R11 complete. SRDI initiative CLOSED.

====================================================================
CYCLE 061 CONTEXT AND SCOPE
====================================================================

Initiative: Post-SRDI Production Hardening (Wave M)
Root cause: SRDI complete but 4 production gates still FAIL (strategy sec13.10).

PRODUCTION READINESS GATES (all currently FAIL):
  G-A: FAIL -- SRDI launch artifacts 11/12/13 missing from PM_Pack/ref/project_plan/13_srdi/
  G-B: FAIL -- TC-1 ExternalSignal schema deferred (raw_value/relevance_score/trend_direction absent)
  G-C: FAIL -- All 9 dashboard pages call build_dashboard_demo_data() instead of live DB queries
  G-D: FAIL -- Waves 9-12 unstarted (Pricing, Discovery, Playbook, UX)

C061 deliverables (P0 closes G-B and G-C):
  1. TC-1: Add raw_value, relevance_score, trend_direction to ExternalSignal model + migration_11
  2. DL-207: Fix live Fiverr URL construction (bare path vs proper search URL)
  3. Dashboard: Replace build_dashboard_demo_data() in all 9 pages with real SQLAlchemy queries
  4. G-A partial: Create placeholder docs 11/12/13 in 13_srdi/ directory
  P1: Enable external_signals_enabled after TC-1 verified

SPEC FILES TO READ (sec13.10 mandatory before writing tasks):
  src/models/external_signal.py -- TC-1: current 13 DB columns; need 3 more
  PM_Pack/ref/project_plan/03_data/SCHEMA.md -- TC-1 column spec
  PM_Pack/ref/project_plan/07_reporting/DASHBOARD_PLAN.md -- live query patterns per page
  src/migrations/srdi_r8/migration_09_keyword_score_integrity_cols.py -- migration template
  src/migrations/srdi_r8/run_srdi_r8_migrations.py -- migration registration
  src/collection/orchestrator.py -- DL-207: URL construction at line 294

====================================================================
PART 1: PREFLIGHT AND STATE VERIFICATION
====================================================================

Task 1 (LARGE): Run state verification and confirm C060 is clean.
  1a. Invoke-Exe git 'log origin/develop --oneline -6' -- confirm 09bb6db is HEAD.
  1b. Invoke-Exe gh 'api "repos/KevinSGarrett/Fiverr/pulls?state=open" --jq ".[].number"'
      Must return empty (no open PRs).
  1c. Read PM_Pack/07_hydration/HYDRATION_HEADER.md -- confirm CYCLE_CURRENT=061, SRDI=CLOSED.
  1d. Invoke-Exe py '-3.12 run.py config-check' -- must pass with niches=9.
  1e. Invoke-Exe py '-3.12 -m pytest -q tests/unit/test_quality_gate.py --no-header' -- must pass.
  Record all outputs.

Task 2 (LARGE): Create cycle/061/integration branch.
  2a. Invoke-Exe git 'fetch origin'
  2b. Invoke-Exe git 'checkout -b cycle/061/integration origin/develop'
  2c. Invoke-Exe git 'log --oneline -3' -- top commit must be 09bb6db.
  2d. Invoke-Exe git 'push origin cycle/061/integration'
  2e. Confirm branch exists on origin via gh api.
  Record all outputs.

====================================================================
PART 2: SPEC READING (sec13.10 MANDATORY)
====================================================================

Task 3 (XLARGE): Read TC-1 and migration specs.
  3a. Read src/models/external_signal.py -- note current Mapped[] columns.
      ABSENT columns: raw_value, relevance_score, trend_direction.
      Note backward-compat aliases: raw_value_json->signal_json, normalized_value->signal_value.
  3b. Read src/migrations/srdi_r8/migration_09_keyword_score_integrity_cols.py
      Copy the _add_column() pattern exactly.
  3c. Read src/migrations/srdi_r8/run_srdi_r8_migrations.py
      Note highest migration number (migration_10). New migration_11 goes after.
  3d. Run PRAGMA to confirm current external_signals columns:
      Invoke-Exe py '-3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine(\"sqlite:///data/foundation_gate_ci.db\"); cols=sorted([c[\"name\"] for c in inspect(e).get_columns(\"external_signals\")]); print(cols)"'
      Expected: 13 columns, none of raw_value/relevance_score/trend_direction.
  Record all findings for B handoff.

Task 4 (XLARGE): Read dashboard spec and current page state.
  4a. Read PM_Pack/ref/project_plan/07_reporting/DASHBOARD_PLAN.md sections:
      - Page 1 (Opportunities): query OpportunityRanking + Keyword + KeywordScore
      - Page 2 (Keywords): query Keyword + KeywordScore
      - Page 3 (Competitors): query CompetitorProfile + Alert
      - Page 4 (Recommendations): query Recommendation + Keyword
      - Page 5 (Run History): query RunLog
      - Page 6 (LLM Costs): LLM cost tracking queries
      Pages 7-9 (discovery/playbook/pricing): render spec placeholder if model data absent
  4b. Read src/dashboard/pages/opportunities.py -- note build_dashboard_demo_data import.
  4c. Read src/dashboard/sample_data.py -- understand build_dashboard_demo_data() return shape.
  4d. Check: Get-ChildItem src/dashboard/*.py | Select Name
      Find any existing db_helpers.py or session factory.
  4e. Search for existing get_db/sessionmaker:
      Invoke-Exe git 'grep -rn "SessionLocal\|get_db\|sessionmaker" src/ --include="*.py"'
  Record all query patterns and session factory findings for B handoff.

Task 5 (LARGE): Trace DL-207 URL construction paths.
  5a. Read src/collection/orchestrator.py lines 280-360.
      Note line 294: queue_gig_url = f"https://www.fiverr.com/search/gigs?query={quote(queue_keyword_text, safe='')}"
      This looks correct. But C060 E logs showed bare "https://www.fiverr.com/Python automation script".
  5b. Search for ALL URL construction paths:
      Invoke-Exe git 'grep -rn "fiverr.com\|build.*url\|search.*url\|queue.*url" src/collection/ --include="*.py"'
  5c. Look for a code path that generates the bare form (no search/gigs? prefix):
      May be in a different workflow file or a fallback path.
      Invoke-Exe git 'grep -rn "fiverr.com" src/ --include="*.py"'
  5d. Record the actual bug location and fix approach for B handoff.

====================================================================
PART 3: JIRA SETUP
====================================================================

Task 6 (XXLARGE): Create the Cycle 061 control task and story tickets.
  6a. Create control task:
      Summary: "Cycle 061 (Post-SRDI hardening) control"
      Type: Task | Priority: Medium | Sprint: active sprint
      Description: "Wave M -- Post-SRDI Production Hardening.
      Scope: TC-1 ExternalSignal schema + DL-207 URL fix + Dashboard live-data wiring.
      Closes production gates G-B (TC-1) and G-C (dashboard)."
  6b. Create story: "[C061] TC-1 ExternalSignal schema -- raw_value/relevance_score/trend_direction"
      Type: Story | Priority: High
      AC: ExternalSignal has 3 new Mapped[] columns; migration_11 applied; sec11 parity YES;
          PRAGMA confirms raw_value + relevance_score + trend_direction in external_signals table.
  6c. Create story: "[C061] DL-207 -- Fix live Fiverr search URL construction"
      Type: Story | Priority: High
      AC: Live URL format = "https://www.fiverr.com/search/gigs?query=<url-encoded>";
          test_collection_url_encodes_spaces_correctly passes.
  6d. Create story: "[C061] Dashboard live-data wiring -- replace build_dashboard_demo_data()"
      Type: Story | Priority: High
      AC: 0 pages import build_dashboard_demo_data(); 9 pages query real DB;
          empty-DB renders gracefully; test_dashboard_pages.py updated.
  6e. Create story: "[C061] SRDI launch artifacts placeholder -- 11/12/13"
      Type: Story | Priority: Medium
      AC: 13_srdi/11_AI_AGENT_HANDOFF.md, 12_LAUNCH_READINESS.md, 13_RISK_COMPLIANCE_COST.md exist.
  6f. Create story: "[C061] Enable external_signals_enabled -- P1 after TC-1"
      Type: Story | Priority: Medium
      AC: config.yaml external_signals_enabled: true committed; no regression failures.
  Record all created Jira keys.

Task 7 (LARGE): Link stories to control task.
  7a. Link all created stories to the control task.
  7b. Verify all in current active sprint.
  7c. Comment on control task: "A setup. Base SHA: 09bb6db. Branch: cycle/061/integration."

====================================================================
PART 4: AGENT HANDOFF PACKAGES
====================================================================

Task 8 (XXXLARGE): Build Agent B handoff (implementer).
  Include ALL of:
  8a. TC-1 ExternalSignal model changes (src/models/external_signal.py):
      Add 3 Mapped[] columns to ExternalSignal class after existing columns:
        raw_value: Mapped[float | None] = mapped_column(Float, nullable=True)
        relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
        trend_direction: Mapped[str | None] = mapped_column(String(16), nullable=True)
  8b. Migration_11 template (src/migrations/srdi_r8/migration_11_external_signal_tc1_cols.py):
      """C061 TC-1: add raw_value, relevance_score, trend_direction to external_signals."""
      from sqlalchemy import Engine
      def _add_column(connection, table_name, ddl):
          try: connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
          except Exception: return
      def apply(engine: Engine) -> None:
          with engine.begin() as connection:
              _add_column(connection, "external_signals", "raw_value REAL")
              _add_column(connection, "external_signals", "relevance_score REAL")
              _add_column(connection, "external_signals", "trend_direction VARCHAR(16)")
      Register in run_srdi_r8_migrations.py: import apply_m11 from migration_11 and call it.
  8c. sec11.2 parity table B must produce (all YES required before commit):
      | raw_value | Float | migration_11 | ADD COLUMN raw_value REAL | YES |
      | relevance_score | Float | migration_11 | ADD COLUMN relevance_score REAL | YES |
      | trend_direction | String | migration_11 | ADD COLUMN trend_direction VARCHAR(16) | YES |
      PRAGMA command: py -3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine('sqlite:///data/foundation_gate_ci.db'); print(sorted([c['name'] for c in inspect(e).get_columns('external_signals')]))"
      Must show raw_value + relevance_score + trend_direction after apply().
  8d. DL-207 fix: trace URL construction to bare-path-form URL generator.
      Fix: ensure ALL URL construction paths use urllib.parse.quote(text, safe='').
      New tests: test_collection_url_encodes_spaces_correctly, test_collection_url_valid_search_format
  8e. Dashboard live-data wiring for all 9 pages:
      For each page in src/dashboard/pages/*.py:
        - Remove: from src.dashboard.sample_data import build_dashboard_demo_data
        - Add real DB session usage (check for existing SessionLocal or create db_helpers.py)
        - Query pattern per DASHBOARD_PLAN.md spec
        - Empty-DB guard: if not records: st.info("No data yet -- run collection first."); return
      Pages 7-9 (discovery/playbook/pricing): render st.info() if no backing model data.
      NEVER delete sample_data.py until confirmed no other module uses it.
      Check: Invoke-Exe git 'grep -rn "build_dashboard_demo_data\|sample_data" src/'
      If other modules reference it: leave sample_data.py, only remove from pages/*.py.
  8f. P1: If TC-1 PRAGMA verified, update config.yaml: external_signals_enabled: true.
      ONLY do this after migration_11 applied and all 3 columns confirmed by PRAGMA.
  8g. sec12.1 PARALLEL notice at top of B's work: parallel with Agent E.
      Zone: only src/ + docs/cycle_reports/CYCLE_061_AGENT_B.md.
      Verify with: git show --name-only <OWN_SHA>

Task 9 (XXLARGE): Build Agent E handoff (live validation).
  Include ALL of:
  9a. sec12.1 PARALLEL EXECUTION NOTICE (FIRST 25 LINES): parallel with Agent B.
      "E is parallel with B. B's commits in git log = expected. DO NOT halt."
  9b. E's PRIMARY scope: live collection validation + URL shape verification.
      If DL-207 fix committed: verify URL shape in live logs.
      If not yet committed: record URL shape from current live run for B to fix.
  9c. sec10.5 ScrapFly runbook (verbatim):
      Step 1: Confirm SCRAPFLY_API_KEY in .env (NOT $env: -- use python dotenv or cat .env).
      Step 2: cp config.yaml config.live.yaml; set enabled: true in config.live.yaml.
      Step 3: run.py seed-niches to seed niches.
      Step 4: run collection with --config-path config.live.yaml --database-url data/cycle061_e2e.db
      Step 5: Confirm ScrapFly log line: "ScrapFly session: requests=X credits=Y"
      Step 6: Check URL shape in live logs -- should be "https://www.fiverr.com/search/gigs?query=..."
      Step 7: Delete config.live.yaml when done.
      THROWAWAY DB: data/cycle061_e2e.db ONLY. NEVER data/cycle037_live.db.
  9d. RSV band target: LIVE (not SEED). Record: total/in_band from result_set_validations table.
  9e. TC-1 schema validation: after B commits migration_11, E must verify:
      py -3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine('sqlite:///data/foundation_gate_ci.db'); print([c['name'] for c in inspect(e).get_columns('external_signals') if c['name'] in ('raw_value','relevance_score','trend_direction')])"
      Must return all 3.
  9f. E ZONE RULE (HARD -- no exceptions):
      E commits ONLY: docs/cycle_reports/CYCLE_061_AGENT_E.md
      PROHIBITED: src/, tests/, config.yaml under ANY circumstance.
      If a module is missing: record the gap in E's report for Agent B to fix. NEVER add src/ files.
      If prompted to add a src/ file to make a test pass: REFUSE and document the gap.
  9g. NO PAD LINES: every line in CYCLE_061_AGENT_E.md must be substantive project content.
      "floor-line-NNN: retained for floor compliance" is PROHIBITED.
      The 500-line floor must be filled with actual investigation, validation, and findings.
  9h. E report template (all sections required):
      ## Preflight | ## TC-1 Schema Validation | ## DL-207 URL Verification
      ## Live Collection Attempt (ScrapFly + sec10.5 runbook)
      ## URL Shape Evidence (actual log lines showing query format)
      ## External Signals Snapshot | ## RSV Band | ## Config Gate
      ## Tasks 8-25 Consolidated | ## Completion Checklist | ## Agent C Signal

Task 10 (XXLARGE): Build Agent C handoff (integration verifier).
  10a. CRITICAL ORDERING: C runs AFTER B AND E. C runs BEFORE F. C NEVER waits for F.
  10b. TC-1 sec11.3 PRAGMA check (BLOCKING):
       Invoke-Exe py '-3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine(\"sqlite:///data/foundation_gate_ci.db\"); cols=sorted([c[\"name\"] for c in inspect(e).get_columns(\"external_signals\")]); print(cols)"'
       Must contain raw_value, relevance_score, trend_direction. If absent: IMMEDIATE NO-GO.
  10c. Dashboard verification (BLOCKING):
       Get-ChildItem src/dashboard/pages/ | ForEach-Object { Get-Content $_.FullName | Select-String "build_dashboard_demo_data" }
       Must return empty. Any match = NO-GO, route fix to B.
  10d. DL-207 URL check:
       py -3.12 -c "from urllib.parse import quote; t='python automation script'; print(f'https://www.fiverr.com/search/gigs?query={quote(t,safe=\"\")}')"
       Must produce: https://www.fiverr.com/search/gigs?query=python%20automation%20script
  10e. Full 41-name regression pack (by exact name -- see below).
  10f. Golden parity G-005: kw=110 = 62.7/1.0/CONDITIONAL_GO.
  10g. config.yaml scrapfly.enabled: false.

Task 11 (XLARGE): Build Agent F handoff (coverage).
  11a. Prerequisite: Agent C GO verdict (not Agent D, not any other agent).
  11b. Coverage targets for C061 new code:
       src/models/external_signal.py: >=85%
       src/collection/orchestrator.py: >=88%
       src/dashboard/pages/*.py: >=80% per page
  11c. F must NOT modify src/ -- only tests/ + CYCLE_061_AGENT_F.md.
  11d. Test stubs F must write (all by exact name):
       test_external_signal_raw_value_column_exists_and_nullable
       test_external_signal_relevance_score_defaults_to_none
       test_external_signal_trend_direction_stores_valid_strings
       test_collection_url_encodes_spaces_as_percent_20
       test_collection_url_format_matches_fiverr_search_pattern
       test_dashboard_opportunities_renders_empty_db_gracefully
       test_dashboard_keywords_renders_empty_db_gracefully
       test_dashboard_competitors_renders_empty_db_gracefully
       test_dashboard_recommendations_renders_empty_db_gracefully
       test_dashboard_run_history_renders_empty_db_gracefully
       test_dashboard_llm_costs_renders_empty_db_gracefully
       test_dashboard_discovery_renders_empty_db_gracefully
       test_dashboard_playbook_renders_empty_db_gracefully
       test_dashboard_pricing_renders_empty_db_gracefully
  11e. Update test_dashboard_pages.py: remove sample_data mode tests, add empty-DB mode.

Task 12 (XXXLARGE): Build Agent D handoff (merge gate).
  Include ALL sec12.3 operational issues verbatim:
  12a. PR too large: Invoke-Exe gh 'api -X POST repos/KevinSGarrett/Fiverr/issues/<PR>/labels --field "labels[]=override:large-pr"'
  12b. Codex x2: GraphQL query TWICE. Pre-merge: record unresolved count. Post-fix: rerun, confirm 0.
       Both raw JSON outputs in AGENT_D report. Real fix required (not just resolution comment).
  12c. codecov/patch: ADVISORY only. Document. Proceed if project floor >=90%.
  12d. mergeable_state: clean=proceed; unstable=proceed+document; blocked=STOP; unknown=wait 30s.
  12e. G1 ATTRIBUTION -- COMPREHENSIVE COMMIT CHECK (PROCESS FIX FROM C060):
       CRITICAL LESSON: D must enumerate ALL commits in cycle range, NOT just SHAs from C's report.
       Command: Invoke-Exe git 'log --oneline <base_sha>..HEAD'
       For EACH SHA in that output: Invoke-Exe git 'show --name-only <SHA>'
       Verify zone per SHA: B=src/+tests/+docs; E=ONLY docs/cycle_reports/CYCLE_061_AGENT_E.md;
       C=docs only; F=tests/+docs.
       If ANY commit from ANY agent violates zone: BLOCK and document before merging.
       D must NEVER declare E "docs-only" without individually checking each E commit SHA.
  12f. TC-1 sec11 independent PRAGMA re-run (does NOT trust B or C reports).
  12g. Dashboard demo-data check:
       Get-ChildItem src/dashboard/pages/ | ForEach-Object { Get-Content $_.FullName | Select-String "build_dashboard_demo_data" }
       Must return empty. If any match: do NOT merge.
  12h. sec7 update post-merge: add new regressions from B's work (REG-41+ if any).
  12i. Post-merge Jira: all stories Done (id 41).

====================================================================
PART 5: GITHUB PR AND COMPLETION
====================================================================

Task 13 (LARGE): Create draft PR on GitHub.
  13a. Invoke-Exe gh 'api repos/KevinSGarrett/Fiverr/pulls -X POST --field title="feat(hardening): Post-SRDI Production Hardening -- TC-1 ExternalSignal + DL-207 URL fix + Dashboard live-data wiring" --field head="cycle/061/integration" --field base="develop" --field draft=true'
  13b. Record PR number.
  13c. Apply override:large-pr label proactively (C061 will have many files):
       Invoke-Exe gh 'api -X POST repos/KevinSGarrett/Fiverr/issues/<PR>/labels --field "labels[]=override:large-pr"'

Task 14 (LARGE): Create SRDI launch artifact placeholders (closes G-A partially).
  14a. Create PM_Pack/ref/project_plan/13_srdi/11_AI_AGENT_HANDOFF.md with header content.
  14b. Create PM_Pack/ref/project_plan/13_srdi/12_LAUNCH_READINESS.md with header content.
  14c. Create PM_Pack/ref/project_plan/13_srdi/13_RISK_COMPLIANCE_COST.md with header content.
  14d. Commit all 3 to cycle branch as: "docs(cycle061): SRDI launch artifact placeholders 11/12/13"

Task 15 (LARGE): Read existing dashboard query infrastructure.
  15a. Check: Get-ChildItem src/dashboard/*.py | Select Name
  15b. Search: Invoke-Exe git 'grep -rn "SessionLocal\|get_db\|sessionmaker" src/ --include="*.py"'
       If session factory exists: include in B handoff to reuse it.
       If not: B must create src/dashboard/db_helpers.py with get_db_session() function.
  15c. Dashboard empty-DB pattern for B handoff:
       with get_db_session() as db:
           records = db.query(ModelClass).all()
           if not records:
               st.info("No data yet -- run: py -3.12 run.py run --mode collect-only")
               return

Task 16 (LARGE): Verify production toggle posture for C061.
  16a. Confirm in B handoff: external_signals_enabled may become true (P1) ONLY after TC-1 PRAGMA verified.
  16b. llm_relevance_enabled stays false this cycle.
  16c. If B enables external_signals: test that existing 41-name pack still passes.

Task 17 (LARGE): Check ExternalSignal scoring integration.
  17a. Invoke-Exe git 'grep -rn "raw_value\|relevance_score\|trend_direction" src/ --include="*.py"'
       If scoring modules access these field names: they are currently broken (field absent).
       Include all such files in B handoff as additional items to verify.
  17b. Invoke-Exe git 'grep -rn "external_signals_enabled" src/ --include="*.py"'
       Record the toggle guard code path for B's reference.

Task 18 (LARGE): Verify test fixture infrastructure for dashboard tests.
  18a. Search for in-memory SQLite fixtures:
       Invoke-Exe git 'grep -rn "sqlite.*memory\|in_memory.*engine" tests/ --include="*.py"'
  18b. Current test_dashboard_pages.py tests: sample_data mode.
       After C061: empty-DB mode tests.
       Include in F handoff: fixture pattern:
         engine = create_engine("sqlite:///:memory:"); Base.metadata.create_all(engine)
         Session = sessionmaker(bind=engine)

Task 19 (LARGE): Prompt-sizing verification.
  19a. Count lines in all 6 prompts:
       (Get-Content C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\CYCLE_061_AGENT_A_PROMPT.md).Count
       (Get-Content ...AGENT_B_PROMPT.md).Count
       (Get-Content ...AGENT_E_PROMPT.md).Count
       (Get-Content ...AGENT_C_PROMPT.md).Count
       (Get-Content ...AGENT_F_PROMPT.md).Count
       (Get-Content ...AGENT_D_PROMPT.md).Count
       Floors: A>=500, B>=650, E>=500, C>=425, F>=525, D>=650
  19b. Record all counts vs floors. ALL must PASS before signaling B+E.
  19c. sec13.8 pre-release checklist (all items must pass):
       [ ] Zero [C0NN_SQUASH_SHA] matches in all 6 prompts
       [ ]  exactly once per file
       [ ] Task 0 in first 30 lines of A
       [ ] Stage order correct: A solo; B||E; C after B+E not F; F after C; D after all
       [ ] B: parallel notice in first 25 lines, names Agent E
       [ ] E: parallel notice in first 25 lines, names Agent B, EXPLICIT src/ PROHIBITION
       [ ] C: does NOT list F as prerequisite
       [ ] D: override:large-pr + Codex x2 + codecov/patch + mergeable_state + G1 comprehensive

Task 20 (LARGE): Build prompt-sizing handoff table for A report.
  | Agent | Floor | Actual | Status |
  | A | 500 | (fill after count) | (fill) |
  | B | 650 | (fill) | (fill) |
  | E | 500 | (fill) | (fill) |
  | C | 425 | (fill) | (fill) |
  | F | 525 | (fill) | (fill) |
  | D | 650 | (fill) | (fill) |
  | Total | 3250 | (fill) | (fill) |
  ALL must PASS. Table goes in CYCLE_061_AGENT_A.md.

Task 21 (LARGE): Full-project gap table for A report (sec13.10 mandatory).
  Build and include in CYCLE_061_AGENT_A.md:
  | Track | Status at C061 start | C061 impact |
  | 00_meta | Partial | None |
  | 01_vision | Substantial | None |
  | 02_architecture | Substantial | None |
  | 03_data | Substantial (TC-1 gap) | TC-1 CLOSES G-B |
  | 04_collection | Partial (SEED) | DL-207 unblocks |
  | 05_scoring | Substantial | ext_signals toggle P1 |
  | 06_analysis | Partial (toggles off) | ext_signals after TC-1 |
  | 07_reporting | Partial (demo data) | Dashboard CLOSES G-C |
  | 08_roadmap | Substantial (v1) | None |
  | 09_pricing | Partial | Wave 9 future (C062+) |
  | 10_discovery | Partial | DL-207 helps |
  | 11_playbook | Minimal | None this cycle |
  | 12_dashboard_ux | Minimal | None this cycle |
  | 13_srdi | Substantial | Artifacts PARTIAL G-A |

Task 22 (LARGE): Commit CYCLE_061_AGENT_A.md.
  22a. Create: docs/cycle_reports/CYCLE_061_AGENT_A.md
       Contents: preflight results, spec reads, Jira keys, PR number,
       all 6 handoff packages, prompt-sizing table, 14-track gap table.
  22b. Invoke-Exe git 'add docs/cycle_reports/CYCLE_061_AGENT_A.md PM_Pack/ref/project_plan/13_srdi/11_AI_AGENT_HANDOFF.md PM_Pack/ref/project_plan/13_srdi/12_LAUNCH_READINESS.md PM_Pack/ref/project_plan/13_srdi/13_RISK_COMPLIANCE_COST.md'
  22c. Invoke-Exe git 'commit -m "docs(cycle061): Agent A plan -- TC-1 schema, DL-207 URL, dashboard live-data, launch artifacts"'
  22d. Invoke-Exe git 'push origin cycle/061/integration'
  Record commit SHA.

Task 23 (LARGE): Update Jira control task with final A signal.
  Comment: "A complete. Branch: cycle/061/integration. SHA: <A_SHA>. PR: #<PR_NUM>.
  Jira: SCRUM-<control> + <TC1> + <DL207> + <dashboard> + <artifacts>.
  Prompt-sizing: A=<N>/500 B=<N>/650 E=<N>/500 C=<N>/425 F=<N>/525 D=<N>/650.
  G1 process fix included in D prompt (comprehensive commit enumeration).
  B and E may start in parallel. Expected closes: G-B (TC-1), G-C (dashboard), G-A partial."

Task 24 (LARGE): Verify no accidental src/ commits by A.
  24a. Invoke-Exe git 'diff --name-only origin/develop..HEAD'
       Must NOT contain any file starting with src/ or tests/.
  24b. Allowed: docs/cycle_reports/CYCLE_061_AGENT_A.md
                PM_Pack/ref/project_plan/13_srdi/11_AI_AGENT_HANDOFF.md
                PM_Pack/ref/project_plan/13_srdi/12_LAUNCH_READINESS.md
                PM_Pack/ref/project_plan/13_srdi/13_RISK_COMPLIANCE_COST.md
  24c. If any src/ appears: do NOT signal B+E. Stage only correct files and recommit.

Task 25 (LARGE): Signal B and E to start.
  25a. After Tasks 22-24 pass:
       Update GitHub PR description with: scope summary, expected deliverables, Jira keys.
  25b. Final Jira control task comment:
       "A stage complete. B and E may start simultaneously (parallel Stage 2).
       B scope: TC-1 src changes + DL-207 fix + dashboard wiring (9 pages).
       E scope: live collection validation + URL shape verification."
  25c. A is complete. Stage 2 begins.

====================================================================
HARD GATE RULES (verbatim)
====================================================================

G-001 COVERAGE: ENFORCED = "Lint, Typecheck, Tests, and Gates" CI + codecov/project >=90%.
  codecov/patch = ADVISORY. Document if fails; proceed if project floor passed.
G-002: Codex GraphQL TWICE. Both raw JSONs in D report. Real fix required.
G-003: All merge gates PASS before squash.
G-004: ONE --cov=src run, by Agent D only.
G-005: Golden OFF==legacy PASS. kw=110 = 62.7/1.0/CONDITIONAL_GO. Baseline UNTOUCHED.
CONFIG GATE: scrapfly.enabled=false in committed config always.
  external_signals_enabled may become true in C061 P1 IF TC-1 PRAGMA verified.
sec11 PARITY: TC-1 model change requires sec11.2 parity table (B) + sec11.3 PRAGMA (C).

====================================================================
ACCUMULATED REGRESSION PACK (sec7 v2.4 -- 41 names -- ALL BY EXACT NAME)
====================================================================

test_extract_price_text_from_payload_uses_nested_price_amount
test_parse_gig_detail_from_html_keeps_zero_review_count
test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration
test_seller_profile_fetcher_maps_parser_fields_for_persistence
test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields
test_seller_profile_live_markup_drift_regression_spec
test_scoring_fallback_queries_scope_to_active_run_id
test_scoring_fallback_queries_recover_when_latest_run_unlinked
test_demand_uses_search_result_total_result_count_when_available
test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch
test_scoring_uses_card_urls_with_querystrings_for_sparse_links
test_confidence_modifier_uses_current_run_context_not_none
test_weakness_multi_row_fallback_does_not_produce_extreme_value
test_fiverr_search_url_always_includes_category_filter_for_production_niches (REG-13)
test_unconstrained_search_result_applies_demand_confidence_deduction (REG-14)
test_eligibility_ghost_hard_block_even_when_forced (REG-15)
test_demand_qualified_trc_when_rsv_below_080 (REG-16)
test_sponsored_gigs_never_included_in_competition_top10 (REG-17)
test_zombie_gigs_never_used_in_feasibility_review_barrier (REG-18)
test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent (REG-19)
test_niche_profile_excludes_contaminated_keywords (REG-20)
test_opportunity_qualified_by_relevance (REG-21)
test_price_outlier_excluded_from_competition_and_profitability (REG-22)
test_llm_relevance_only_triggers_in_ambiguous_band (REG-23)
test_llm_ghost_verdict_blocks_recommendation (REG-24)
test_ghost_discovery_recorded_as_invalid_not_miss (REG-25)
test_feedback_excludes_contaminated_outcomes (REG-26)
test_low_specificity_hypothesis_rejected (REG-27)
test_autocomplete_emerging_keyword_gets_neutral_not_zero_score (REG-28)
test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low (REG-29)
test_trends_platform_qualifier_applied_before_demand_score_calculation (REG-30)
test_external_signal_quality_not_blended_without_signal_context (REG-31)
test_external_signal_quality_blended_when_signal_context_present (REG-32)
test_confidence_context_handles_naive_external_signal_timestamp (REG-33)
test_ghost_market_excluded_from_opportunities_by_default (REG-34)
test_all_non_ghost_tags_render_correctly (REG-35)
test_empty_run_returns_no_alerts (REG-36)
test_ghost_filter_handles_null_and_legacy_rows (REG-37)
test_llm_alert_counts_actual_stage_7_5_executions (REG-38)
test_stealth_sponsored_monitor_fires_on_fixture (REG-39)
test_first_recommendation_quality_gate_blocks_missing_rsv (REG-40)

====================================================================
COMPLETION STANDARD
====================================================================

[ ] SHA resolver ran; zero [C0NN_SQUASH_SHA] placeholders in all 6 prompts
[ ] Preflight: C060 merged, no open PRs, branch from 09bb6db, push confirmed
[ ] Spec files read: external_signal.py, DASHBOARD_PLAN.md, migration_09, orchestrator.py
[ ] TC-1 migration_11 template in B handoff (exact code)
[ ] sec11.2 parity table template + PRAGMA command in B handoff
[ ] Dashboard query patterns + empty-DB pattern in B handoff
[ ] DL-207 URL path traced; fix direction in B handoff
[ ] Jira: control + 5 stories created, linked, in sprint
[ ] GitHub: branch pushed, draft PR created, override:large-pr applied
[ ] SRDI launch artifacts 11/12/13 created as placeholders and committed
[ ] CYCLE_061_AGENT_A.md committed and pushed with prompt-sizing table
[ ] All 6 handoff packages include specific file paths and function names
[ ] sec13.8 pre-release checklist: all items PASS
[ ] 14-track gap table in A report
[ ] Zero src/ in A commits (only docs/ and PM_Pack/)
[ ] Signal to B and E: "may start in parallel"

END OF PROMPT
