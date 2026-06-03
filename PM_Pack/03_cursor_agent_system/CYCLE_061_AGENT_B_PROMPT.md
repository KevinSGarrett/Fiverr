# CYCLE 061 -- AGENT B PROMPT
# Role: Implementer (src/ + tests/ + migrations)
# Base SHA: 9687fb6f38ebca8b01cefa845630ea4f2b609c07
# Branch: cycle/061/integration | Stage 2 (parallel with E, after A)
# Strategy: C:\Fiverr\Fiverr\PM_Pack\ref\AGENT_EXECUTION_STRATEGY.md

====================================================================
PARALLEL EXECUTION NOTICE (sec12.1) -- READ THIS FIRST
====================================================================

YOU ARE RUNNING IN PARALLEL WITH AGENT E.
Agent E is committing docs/cycle_reports/CYCLE_061_AGENT_E.md to this branch simultaneously.
When you run git log, you WILL see Agent E commits. This is EXPECTED and CORRECT.
DO NOT halt. DO NOT alarm. DO NOT stop work.
Verify YOUR OWN zone only: git show --name-only <YOUR_OWN_SHA>
NEVER use git diff origin/develop..HEAD for zone compliance.

====================================================================
STAGE AND CONTEXT
====================================================================

Stage 2 -- parallel with E, after A, before C/F/D.
B is the ONLY agent that writes src/ files this cycle.

Working dir: C:\Fiverr\Fiverr | Python: py -3.12
Jira: eae77257-a572-4e19-b746-8b184ba2d01f | Connector auth (never paste tokens)

9 niche_ids: prd_ai_saas, support_kb_readiness, gumloop_lindy_workflow, mcp_ai_agent,
  python_automation, ai_tool_llm_integration, ai_agent_development,
  workflow_automation, python_web_scraping

STARTING STATE (develop @ 9687fb6f38ebca8b01cefa845630ea4f2b609c07):
  Suite: 4022 passed | Coverage: 95.58% | Floor: 90%
  Golden: kw=110 = 62.7/1.0/CONDITIONAL_GO
  Toggles: scrapfly=false, external_signals_enabled=false, llm_relevance_enabled=false
  External_signals DB columns (PRAGMA): 13 columns; missing raw_value, relevance_score, trend_direction

====================================================================
CYCLE 061 B MISSION
====================================================================

B delivers ALL src/ changes this cycle:
  1. TC-1 ExternalSignal schema: add raw_value, relevance_score, trend_direction + migration_11
  2. DL-207 URL fix: all live Fiverr URL paths use urllib.parse.quote(text, safe='')
  3. Dashboard live-data: replace build_dashboard_demo_data() in all 9 pages with real SQLAlchemy
  P1: Enable external_signals_enabled after TC-1 PRAGMA verified (config.yaml change)

Execution evidence discipline (mandatory in B report):
  - Capture BEFORE/AFTER grep output for build_dashboard_demo_data references.
  - Capture migration_11 registration diff in run_srdi_r8_migrations.py.
  - Capture PRAGMA output after migration_11 apply() with full sorted column list.
  - Capture URL-format test output proving %20 encoding for space-separated keywords.
  - Capture final git show --name-only <B_SHA> for zone proof.

====================================================================
PART 1: PREFLIGHT
====================================================================

Task 1 (LARGE): Preflight and state verification.
  1a. git pull origin cycle/061/integration
  1b. git log --oneline -5 -- A commit must be HEAD
  1c. Read docs/cycle_reports/CYCLE_061_AGENT_A.md for spec findings and handoff
  1d. py -3.12 run.py config-check -- must pass with niches=9
  1e. py -3.12 -m pytest -q tests/unit/test_monitors.py --no-header -- must pass

====================================================================
PART 2: TC-1 EXTERNALSIGNAL SCHEMA
====================================================================

Task 2 (XXXLARGE): Implement TC-1 ExternalSignal additions.
  2a. Read src/models/external_signal.py in full. Confirm ABSENT: raw_value, relevance_score, trend_direction.
  2b. Add 3 Mapped columns to ExternalSignal class (after existing columns, before properties):
        # TC-1 COLUMNS (C061)
        raw_value: Mapped[float | None] = mapped_column(Float, nullable=True)
        # raw unprocessed value from data source before normalization
        relevance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
        # R7 qualifier score 0.0-1.0; None = not scored
        trend_direction: Mapped[str | None] = mapped_column(String(16), nullable=True)
        # RISING / STABLE / FALLING / UNKNOWN / None
  2c. Update write_external_signal() to accept raw_value=None, relevance_score=None, trend_direction=None
      and store them on the row.
  2d. Read src/migrations/srdi_r8/migration_09_keyword_score_integrity_cols.py for _add_column() pattern.
  2e. Create src/migrations/srdi_r8/migration_11_external_signal_tc1_cols.py:
      Content:
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
  2f. Register in run_srdi_r8_migrations.py: import apply_m11; call apply_m11(engine) after apply_m10.
  2g. Apply on foundation_gate_ci.db:
      py -3.12 -c "from src.migrations.srdi_r8.run_srdi_r8_migrations import run_all; from sqlalchemy import create_engine; run_all(create_engine('sqlite:///data/foundation_gate_ci.db'))"
  2h. PRAGMA verification -- BLOCKING:
      py -3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine('sqlite:///data/foundation_gate_ci.db'); cols=sorted([c['name'] for c in inspect(e).get_columns('external_signals')]); assert 'raw_value' in cols and 'relevance_score' in cols and 'trend_direction' in cols; print('TC-1 PRAGMA PASS')"
      If assertion fails: migration did not apply. Fix before proceeding.
  Record parity table (all YES) and PRAGMA output in B report.

Task 3 (LARGE): sec11.2 parity table -- include in B report (BLOCKING before commit).
  | raw_value | Float | migration_11 | ADD COLUMN raw_value REAL | YES |
  | relevance_score | Float | migration_11 | ADD COLUMN relevance_score REAL | YES |
  | trend_direction | String | migration_11 | ADD COLUMN trend_direction VARCHAR(16) | YES |
  All other existing ExternalSignal ORM columns must also be YES.

Task 4 (LARGE): TC-1 tests.
  test_external_signal_raw_value_persists: save ExternalSignal(raw_value=0.75); reload; assert == 0.75
  test_external_signal_relevance_score_defaults_none: create without relevance_score; assert None
  test_external_signal_trend_direction_stores_rising: create with trend_direction="RISING"; assert == "RISING"
  Run: py -3.12 -m pytest -q tests/unit/ -k "raw_value or relevance_score or trend_direction" --no-header

====================================================================
PART 3: DL-207 URL FIX
====================================================================

Task 5 (XXLARGE): Trace and fix URL construction bug.
  5a. Line 294 in orchestrator.py already uses quote() correctly. The bug is in a DIFFERENT path.
  5b. git grep -rn "fiverr.com" src/ --include="*.py" -- find all URL construction paths.
  5c. For each path: check if quote() is used. Any path producing "https://www.fiverr.com/Python automation script" (bare, no search/gigs? prefix) is the bug.
  5d. Fix: replace with f"https://www.fiverr.com/search/gigs?query={quote(keyword_text.strip(), safe='')}"
  5e. Verify: py -3.12 -c "from urllib.parse import quote; t='python automation script'; url=f'https://www.fiverr.com/search/gigs?query={quote(t,safe=\"\")}'; assert 'query=python%20automation%20script' in url; print('DL-207 OK')"
  Record: exact file/line of bug; fix applied.

Task 6 (LARGE): DL-207 tests.
  test_collection_url_encodes_spaces_correctly: build URL for "python automation script"; assert "query=python%20automation%20script" in url
  test_collection_url_starts_with_search_gigs: assert url.startswith("https://www.fiverr.com/search/gigs")
  test_collection_url_never_bare_path: assert "fiverr.com/python" not in url (bare path form)

====================================================================
PART 4: DASHBOARD LIVE-DATA WIRING (9 pages)
====================================================================

Task 7 (LARGE): Check existing dashboard infrastructure.
  7a. Get-ChildItem src\dashboard\*.py | Select Name -- list all dashboard modules
  7b. git grep -rn "SessionLocal\|get_db\|sessionmaker" src/ --include="*.py"
  7c. If no session factory: create src/dashboard/db_helpers.py:
      from contextlib import contextmanager; import os
      from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; from sqlalchemy.pool import StaticPool
      def _get_db_url(): return os.environ.get("DATABASE_URL", "sqlite:///data/fiverr_research.db")
      @contextmanager
      def get_db_session():
          e=create_engine(_get_db_url(), connect_args={"check_same_thread":False}, poolclass=StaticPool)
          S=sessionmaker(bind=e); db=S()
          try: yield db
          finally: db.close()

Task 8 (XXXLARGE): Wire Page 1 Opportunities.
  8a. Read src/dashboard/pages/opportunities.py in full.
  8b. Remove: from src.dashboard.sample_data import build_dashboard_demo_data
  8c. Add: from src.dashboard.db_helpers import get_db_session
  8d. Replace data = build_dashboard_demo_data() with:
      with get_db_session() as db:
          from src.models.keyword_score import KeywordScore
          from src.models.keyword import Keyword
          scores = db.query(KeywordScore).join(Keyword).order_by(KeywordScore.final_score.desc().nullslast()).limit(50).all()
          if not scores: st.info("No scored keywords yet. Run: py -3.12 run.py run --mode score-only"); return
          records = [{"keyword_text": getattr(getattr(s,"keyword_ref",None),"keyword_text",str(s.keyword_id)), "final_score": s.final_score or 0.0, "tag": s.tag or "UNSCORED"} for s in scores]
  8e. Feed records into build_opportunities_payload(records=records). Keep rendering logic.

Task 9 (XXLARGE): Wire Pages 2-6 (Keywords, Competitors, Recommendations, Run History, LLM Costs).
  For each: remove build_dashboard_demo_data import; add get_db_session import; replace demo query with real DB query.
  Pattern per page:
    Page 2 Keywords: db.query(Keyword).join(KeywordScore, isouter=True).order_by(KeywordScore.final_score.desc().nullslast()).all()
    Page 3 Competitors: check for CompetitorProfile model; if missing render st.info("Requires live run")
    Page 4 Recommendations: check for Recommendation model; live query or empty-DB guard
    Page 5 Run History: check for RunLog model; live query or empty-DB guard
    Page 6 LLM Costs: check for cost tracking in RunLog; live query or placeholder
  Empty-DB guard for ALL pages: if not records: st.info("No data yet. Run collection first."); return

Task 10 (LARGE): Wire Pages 7-9 (Discovery, Playbook, Pricing -- placeholder or live).
  Discovery: try import DiscoveryOutcome; if available live query; if not: st.info("Requires live collection run.")
  Playbook: st.info("Gig Creation Playbook coming in Wave 11 (future cycle).")
  Pricing: st.info("Pricing Strategy Engine coming in Wave 9 (future cycle).")

Task 11 (LARGE): Verify demo-data removal.
  Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content $_.FullName | Select-String "build_dashboard_demo_data" }
  Must return empty. Any match = fix immediately.
  Check sample_data.py references: git grep -rn "sample_data" src/ --include="*.py"
  If other modules outside pages/ reference it: KEEP sample_data.py (do NOT delete).

Task 12 (XLARGE): Update test_dashboard_pages.py.
  12a. Current tests use sample_data mock. After C061 they must test empty-DB mode.
  12b. Add fixture:
       @pytest.fixture
       def empty_db_session():
           from sqlalchemy import create_engine; from sqlalchemy.orm import sessionmaker; from sqlalchemy.pool import StaticPool
           from src.models.base import Base
           e=create_engine("sqlite:///:memory:", connect_args={"check_same_thread":False}, poolclass=StaticPool)
           Base.metadata.create_all(e); S=sessionmaker(bind=e); db=S(); yield db; db.close()
  12c. Add test for each of the 9 pages:
       def test_<page>_renders_empty_db_gracefully(empty_db_session, mocker):
           mocker.patch("src.dashboard.db_helpers.get_db_session").__enter__ = lambda s: (yield empty_db_session)
           mocker.patch("streamlit.title"); mocker.patch("streamlit.info"); mocker.patch("streamlit.subheader")
           from src.dashboard.pages.<page> import render_<page>_page
           render_<page>_page()  # must NOT raise; st.info should be called

====================================================================
PART 5: P1 TOGGLE + GATE VERIFICATION
====================================================================

Task 13 (LARGE): P1 -- Enable external_signals_enabled (ONLY after TC-1 PRAGMA verified).
  Prerequisite: migration_11 applied, PRAGMA confirms all 3 TC-1 columns.
  Edit config.yaml: external_signals_enabled: false -> external_signals_enabled: true
  Run full regression pack. If any failure: revert toggle, document, leave false.
  If all pass: keep enabled: true.

Task 14 (LARGE): Full gate verification.
  py -3.12 -m ruff check . -- PASS
  py -3.12 -m mypy src -- PASS
  py -3.12 run.py foundation-gate -- PASS
  py -3.12 run.py phase2-smoke -- PASS

Task 15 (LARGE): Full 41-name regression pack.
  Run all 41 tests by exact name (see pack below). Must show 88+ passed, 0 failed.

Task 16 (LARGE): Golden parity final check.
  py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override analysis.external_signals_enabled=false
  kw=110 = 62.7/1.0/CONDITIONAL_GO. kw=96=35.8. Baseline DB mtime unchanged.

Task 17 (LARGE): Zone verification.
  For EACH B commit: git show --name-only <SHA>
  Must ONLY contain src/, tests/, docs/cycle_reports/CYCLE_061_AGENT_B.md
  NO PM_Pack/, NO config.yaml outside B's P1 toggle change.

Task 18 (LARGE): Commit all B deliverables.
  git add src/ tests/ docs/cycle_reports/CYCLE_061_AGENT_B.md
  git commit -m "feat(hardening): C061 TC-1 ExternalSignal schema + DL-207 URL fix + dashboard live-data wiring"
  git push origin cycle/061/integration

Task 19 (LARGE): Create CYCLE_061_AGENT_B.md report.
  Sections: TC-1 (parity table ALL YES, PRAGMA output) | DL-207 (file/line of bug, fix, tests)
  Dashboard (each of 9 pages: query used, empty-DB guard confirmed) | P1 (enabled or not + reason)
  Zone check (own SHAs, file list) | Gates (ruff, mypy, regression pack count, golden)
  New regressions (REG-41+ if any) | Signal: "B complete at SHA <SHA>. C may start after E signals."

Task 20 (LARGE): Jira transitions.
  TC-1 story -> Done: "TC-1 done. migration_11 applied. PRAGMA verified all 3 columns."
  DL-207 story -> Done: "URL encoding fixed. test_collection_url_encodes_spaces_correctly PASS."
  Dashboard story -> Done: "All 9 pages wired. No demo-data. Empty-DB graceful."
  P1 story -> Done if enabled, or comment: "Not enabled this cycle -- TC-1 verification failed."

Task 21 (LARGE): Verify migration on fresh DB.
  Create test DB: data/migration_test_061.db
  Apply migrations; verify PRAGMA shows all 3 TC-1 columns; delete test DB.

Task 22 (LARGE): Dashboard import smoke tests (9 pages).
  py -3.12 -c "from src.dashboard.pages.opportunities import render_opportunities_page; print('OK')"
  (same for all 9 pages) -- any ImportError = fix before commit.

Task 23 (LARGE): Check ExternalSignal scoring integration.
  git grep -rn ".raw_value\|.relevance_score\|.trend_direction" src/ --include="*.py"
  If scoring modules already access these: verify they work after TC-1 adds the columns.
  Document findings under "TC-1 Downstream Scoring Impact" in B report.

Task 24 (LARGE): Regression pack run with DL-207 fix.
  After fixing URL construction: run test_collection_orchestrator.py tests.
  Must include new URL tests. Must not break existing tests.

Task 25 (LARGE): Final B checklist before signaling C.
  [ ] TC-1: 3 Mapped columns in ORM + migration_11 registered + PRAGMA PASS
  [ ] sec11.2 parity table ALL YES in B report
  [ ] DL-207: bug found and fixed; 3 new URL tests pass
  [ ] Dashboard: 9 pages use real queries; build_dashboard_demo_data absent
  [ ] Empty-DB: all 9 pages render gracefully (st.info)
  [ ] test_dashboard_pages.py: 9 empty-DB tests pass
  [ ] P1 external_signals: documented decision
  [ ] ruff + mypy + foundation-gate + phase2-smoke: PASS
  [ ] 41-name pack: 88+ passed
  [ ] Golden: 62.7/1.0/CONDITIONAL_GO
  [ ] Zone: only src/ + tests/ + B report in B commits
  [ ] CYCLE_061_AGENT_B.md committed and pushed
  [ ] Jira stories Done

====================================================================
B KNOWN FAILURE MODES (guard against these explicitly)
====================================================================

1. TC-1 migration not applied before model is committed.
   Guard: PRAGMA check BEFORE committing model changes. "Tests pass" is not proof.

2. Dashboard page still imports build_dashboard_demo_data after wiring.
   Guard: Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content | Select-String "build_dashboard_demo_data" }
   Expected: EMPTY. Any match = fix first.

3. Empty-DB crash on any page.
   Guard: every page has try/except + empty-results guard before any dataframe render.

4. migration_11 not registered in run_srdi_r8_migrations.py.
   Guard: grep for "migration_11" in run_srdi_r8_migrations.py -- must appear.

5. Zone violation -- B commits tests/ outside its scope.
   Guard: git show --name-only <OWN_SHA> shows only src/ + B report.

6. P1 toggle enabled without PRAGMA verification.
   Guard: confirm all 3 TC-1 columns in PRAGMA BEFORE editing config.yaml.

7. sample_data.py deleted when other modules still use it.
   Guard: git grep "sample_data" src/ -- if any match outside pages/*.py, DO NOT delete.

====================================================================
ACCUMULATED REGRESSION PACK (sec7 v2.4 -- 41 names -- RUN ALL)
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
HARD GATE RULES (verbatim)
====================================================================

G-001: Enforced = Lint/Typecheck/Tests/Gates CI + codecov/project >=90%.
G-002: Codex x2 by D. B must ensure code is correct so D can resolve threads.
G-004: ONE --cov=src by D only.
G-005: Golden PASS. kw=110 = 62.7/1.0/CONDITIONAL_GO. Baseline UNTOUCHED.
CONFIG: scrapfly.enabled=false always. external_signals_enabled may be true P1 after TC-1 PRAGMA.
sec11 PARITY: migration_11 required. ALL parity rows YES. PRAGMA is the proof, not tests.



====================================================================
INLINE CODE TEMPLATES FOR B (mandatory reference material)
====================================================================

## TC-1: Complete ExternalSignal model changes

Add to ExternalSignal class in src/models/external_signal.py AFTER existing mapped columns
and BEFORE the backward-compat property definitions:

    # === TC-1 COLUMNS (C061 Post-SRDI Hardening) ===
    raw_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="Original unprocessed signal value from data source before normalization. "
                "None means raw value was not captured or not applicable."
    )
    relevance_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        comment="R7 qualifier score 0.0-1.0 applied to this signal for demand scoring. "
                "1.0=fully qualified, 0.0=fully disqualified, None=not yet scored."
    )
    trend_direction: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        comment="Derived trend direction: RISING|STABLE|FALLING|UNKNOWN. "
                "Max 16 chars. None=direction not yet derived."
    )

Updated write_external_signal() signature with TC-1 fields:

    def write_external_signal(
        keyword_id: int,
        signal_type: str,
        signal_value: float | None,
        signal_json: dict[str, Any] | None,
        run_id: str | None,
        collection_method: str | None,
        db: Any,
        *,
        raw_value: float | None = None,
        relevance_score: float | None = None,
        trend_direction: str | None = None,
    ) -> ExternalSignal | None:
        ...  # existing query/create logic
        row.signal_value = signal_value
        row.signal_json = signal_json
        row.collection_method = collection_method
        row.collected_at = utc_now()
        # TC-1 fields
        row.raw_value = raw_value
        row.relevance_score = relevance_score
        row.trend_direction = trend_direction
        db.add(row); db.commit(); db.refresh(row)
        return row

## migration_11 complete file (copy verbatim)

    # src/migrations/srdi_r8/migration_11_external_signal_tc1_cols.py
    """C061 TC-1: add raw_value, relevance_score, trend_direction to external_signals."""
    from sqlalchemy import Engine

    def _add_column(connection, table_name: str, ddl: str) -> None:
        """Add a column idempotently -- ignores 'duplicate column' errors."""
        try:
            connection.exec_driver_sql(
                f"ALTER TABLE {table_name} ADD COLUMN {ddl}"
            )
        except Exception:
            return  # Column already exists

    def apply(engine: Engine) -> None:
        with engine.begin() as connection:
            _add_column(connection, "external_signals", "raw_value REAL")
            _add_column(connection, "external_signals", "relevance_score REAL")
            _add_column(connection, "external_signals", "trend_direction VARCHAR(16)")

run_srdi_r8_migrations.py addition (insert after the existing apply_m10 call):

    from src.migrations.srdi_r8.migration_11_external_signal_tc1_cols import apply as apply_m11
    ...
    apply_m10(engine)  # existing
    apply_m11(engine)  # TC-1 addition

## sec11.2 parity table (complete, fill in for B report)

| Column | ORM Type | Nullable | Migration File | DDL | Present? |
|--------|----------|----------|----------------|-----|----------|
| id | int | No | original CREATE | INTEGER PRIMARY KEY | YES |
| keyword_id | int | No | original CREATE | INTEGER NOT NULL | YES |
| signal_type | str | No | original CREATE | VARCHAR(64) NOT NULL | YES |
| signal_value | float or None | Yes | original CREATE | REAL | YES |
| signal_json | dict or None | Yes | original CREATE | JSON | YES |
| source_url | str or None | Yes | original CREATE | VARCHAR(1024) | YES |
| collected_at | datetime | No | original CREATE | DATETIME | YES |
| ttl_hours | int | No | original CREATE | INTEGER | YES |
| is_stale | bool | No | original CREATE | BOOLEAN | YES |
| run_id | str or None | Yes | migration_10 | VARCHAR(64) | YES |
| collection_method | str or None | Yes | original or migration | VARCHAR(64) | YES |
| error_message | str or None | Yes | original or migration | VARCHAR(2048) | YES |
| created_at | datetime | No | TimestampMixin | DATETIME | YES |
| updated_at | datetime | No | TimestampMixin | DATETIME | YES |
| raw_value | float or None | Yes | migration_11 | REAL | YES (after apply) |
| relevance_score | float or None | Yes | migration_11 | REAL | YES (after apply) |
| trend_direction | str or None | Yes | migration_11 | VARCHAR(16) | YES (after apply) |

PRAGMA verification command (run after migration_11 apply):

    py -3.12 -c "
    from sqlalchemy import create_engine, inspect
    e = create_engine('sqlite:///data/foundation_gate_ci.db')
    cols = sorted([c['name'] for c in inspect(e).get_columns('external_signals')])
    required = {'raw_value', 'relevance_score', 'trend_direction'}
    missing = required - set(cols)
    if missing: raise AssertionError(f'TC-1 COLUMNS MISSING: {missing}')
    print('TC-1 PRAGMA PASS. Columns:', cols)
    "

## db_helpers.py complete implementation

    # src/dashboard/db_helpers.py
    """Database session utilities for dashboard live-data wiring (C061)."""
    from __future__ import annotations
    import os
    from contextlib import contextmanager
    from typing import Generator
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session, sessionmaker
    from sqlalchemy.pool import StaticPool

    _DEFAULT_URL = "sqlite:///data/fiverr_research.db"

    def _get_database_url() -> str:
        return os.environ.get("DATABASE_URL", _DEFAULT_URL)

    @contextmanager
    def get_db_session() -> Generator[Session, None, None]:
        """Yield a SQLAlchemy session for dashboard queries. Handles cleanup."""
        url = _get_database_url()
        kwargs = {"check_same_thread": False} if "sqlite" in url else {}
        engine = create_engine(
            url,
            connect_args=kwargs,
            poolclass=StaticPool if "sqlite" in url else None,
        )
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        try:
            yield db
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

## Page 1 Opportunities -- full implementation

    # src/dashboard/pages/opportunities.py (post C061 live-data wiring)
    """Page 1: Opportunities -- dashboard landing page."""
    from __future__ import annotations
    import streamlit as st
    from src.dashboard.opportunities import build_opportunities_payload
    from src.dashboard.db_helpers import get_db_session

    def render_opportunities_page() -> None:
        st.title("Opportunities")
        with get_db_session() as db:
            try:
                from src.models.keyword_score import KeywordScore
                from src.models.keyword import Keyword
                scores = (
                    db.query(KeywordScore)
                    .join(Keyword, Keyword.id == KeywordScore.keyword_id)
                    .filter(KeywordScore.final_score.isnot(None))
                    .order_by(KeywordScore.final_score.desc())
                    .limit(50)
                    .all()
                )
            except Exception as exc:
                st.error(f"Database error: {exc}")
                return
            if not scores:
                st.info(
                    "No scored keywords yet. "
                    "Run: py -3.12 run.py run --mode score-only"
                )
                return
            records = []
            for s in scores:
                kw_ref = getattr(s, "keyword_ref", None)
                kw_text = getattr(kw_ref, "keyword_text", None) or str(s.keyword_id)
                records.append({
                    "keyword_text": kw_text,
                    "final_score": s.final_score or 0.0,
                    "tag": s.tag or "UNSCORED",
                    "confidence_modifier": s.confidence_modifier or 1.0,
                })
        payload = build_opportunities_payload(records=records)
        st.subheader(payload.get("title", "Opportunities"))
        st.write(payload.get("state", {}).get("message", ""))
        rows = payload.get("table", {}).get("rows", [])
        if rows:
            st.dataframe(rows, use_container_width=True, hide_index=True)
        warnings = payload.get("warning_summary", {}).get("warnings", [])
        if warnings:
            st.warning(" | ".join(warnings))
        else:
            st.success("Opportunity data loaded successfully.")

    if __name__ == "__main__":
        render_opportunities_page()

## Empty-DB test fixture (add to tests/unit/conftest.py or test_dashboard_pages.py)

    import pytest
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    @pytest.fixture
    def empty_db_engine():
        """In-memory SQLite with all tables created, zero rows."""
        from src.models.base import Base
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def empty_db_session(empty_db_engine):
        """Yield a session against the empty in-memory DB."""
        SessionLocal = sessionmaker(bind=empty_db_engine)
        db = SessionLocal()
        yield db
        db.close()

    @pytest.fixture
    def mock_st(mocker):
        """Mock all streamlit calls to prevent rendering errors."""
        for attr in ["title", "subheader", "info", "error", "warning", "success",
                     "dataframe", "write", "caption", "expander", "columns"]:
            mocker.patch(f"streamlit.{attr}")
        return mocker

Example empty-DB test for Page 1:

    def test_opportunities_renders_empty_db_gracefully(empty_db_session, mock_st, mocker):
        """Page renders without crash when DB has no scored keywords."""
        import streamlit as st
        # Patch get_db_session to yield the empty in-memory session
        from unittest.mock import MagicMock
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=empty_db_session)
        ctx.__exit__ = MagicMock(return_value=False)
        mocker.patch("src.dashboard.db_helpers.get_db_session", return_value=ctx)
        from src.dashboard.pages.opportunities import render_opportunities_page
        render_opportunities_page()  # must NOT raise
        st.info.assert_called()      # must call st.info with "No scored keywords" message

====================================================================
ADDITIONAL TASKS 26-30
====================================================================

Task 26 (LARGE): Run full test suite after all changes.
  py -3.12 -m pytest -q --no-header 2>&1 | Tee-Object -FilePath test_output.txt
  Record: total passed, failed, warnings. Must be >=4022 passed (existing) + new tests. 0 failures.

Task 27 (LARGE): Verify dashboard pages import cleanly.
  For each of the 9 pages run: py -3.12 -c "from src.dashboard.pages.<page> import render_<page>_page; print('<page> OK')"
  Any ImportError = fix before committing.

Task 28 (LARGE): Document any missing models found during dashboard wiring.
  For each page where the backing model doesn't exist yet:
    - Record in B report under "Missing Models (C062+ scope)"
    - Render placeholder: st.info("Feature requires [model]. Coming in future cycle.")
    - Never crash. Never import non-existent model without try/except.

Task 29 (LARGE): Verify baseline DB integrity after all changes.
  py -3.12 -c "import os; mtime=os.path.getmtime('data/cycle037_live.db'); print(f'mtime={mtime}'); assert abs(mtime-1780279258.7) < 1.0"
  If assertion fails: STOP. Surface to PM. Do NOT merge.

Task 30 (LARGE): Final signal preparation.
  Record B SHA: git rev-parse HEAD
  Confirm B report is committed: git log --oneline -3
  Confirm no untracked src/ changes: git status --short (must be clean)
  Post signal: "B complete. SHA: <SHA>. C may proceed after E also signals ready."

END OF PROMPT
