# CYCLE 061 -- AGENT F PROMPT
# Role: Coverage expansion (tests/ only, after C GO verdict)
# Stage: 4 (after C GO verdict, before D)
# Base SHA: 9687fb6f38ebca8b01cefa845630ea4f2b609c07
# Branch: cycle/061/integration

====================================================================
STAGE CONTEXT
====================================================================

F runs AFTER Agent C issues a GO verdict.
F's prerequisite: C must have issued GO.
If C issued NO-GO: F WAITS. Do not start until B fixes the issue and C re-runs.
F commits ONLY: test files + docs/cycle_reports/CYCLE_061_AGENT_F.md
F NEVER modifies: src/ (not even one line)

====================================================================
PROJECT CONTEXT
====================================================================

Working dir: C:\Fiverr\Fiverr | Python: py -3.12
Jira: eae77257-a572-4e19-b746-8b184ba2d01f | Connector auth only

====================================================================
F ZONE RULE (HARD)
====================================================================

F modifies ONLY:
  - tests/ (new test files or extensions to existing ones)
  - docs/cycle_reports/CYCLE_061_AGENT_F.md

PROHIBITED:
  - src/ files (zero exceptions)
  - config.yaml
  - PM_Pack/
  - Any file outside tests/ or F report

If a test requires a src/ change: F documents the gap and routes to B.
F NEVER changes src/ to make a test pass.

====================================================================
PREFLIGHT
====================================================================

Task 1 (LARGE): Preflight checks.
  1a. git pull origin cycle/061/integration
  1b. Read docs/cycle_reports/CYCLE_061_AGENT_C.md -- confirm GO verdict
  1c. If C issued NO-GO: STOP. Contact PM. Do not proceed.
  1d. py -3.12 run.py config-check -- niches=9
  1e. py -3.12 -m pytest -q tests/unit/ --no-header -- confirm current passing count

====================================================================
COVERAGE TARGETS
====================================================================

F must improve coverage for the 3 C061 deliverables:
  src/models/external_signal.py: target >=85%
  src/collection/orchestrator.py: target >=88%
  src/dashboard/pages/*.py (each page): target >=75%

C's pre-F coverage baseline: read from C report (C must have run the suite).
F tracks: coverage delta between C's baseline and D's final run.

====================================================================
PART 1: TC-1 EXTERNALSIGNAL COVERAGE
====================================================================

Task 2 (XXLARGE): Write tests for TC-1 ExternalSignal columns.
  Create or extend: tests/unit/test_external_signal_integrity.py

  test_external_signal_raw_value_column_nullable:
    Arrange: create ExternalSignal without raw_value
    Assert: raw_value is None (column accepts NULL)
    Assert: ExternalSignal persists without error to in-memory DB

  test_external_signal_raw_value_stored_and_retrieved:
    Arrange: create ExternalSignal(raw_value=0.75)
    Act: save to in-memory DB; reload via query
    Assert: retrieved.raw_value == 0.75

  test_external_signal_raw_value_zero_stored:
    Arrange: create ExternalSignal(raw_value=0.0)
    Assert: raw_value == 0.0 (not None -- 0.0 is valid)

  test_external_signal_relevance_score_defaults_none:
    Arrange: create ExternalSignal without relevance_score
    Assert: relevance_score is None

  test_external_signal_relevance_score_full_range:
    Parametrize: [0.0, 0.5, 1.0]
    For each value: create ExternalSignal(relevance_score=v); assert == v

  test_external_signal_trend_direction_rising:
    Arrange: ExternalSignal(trend_direction="RISING")
    Assert: trend_direction == "RISING"

  test_external_signal_trend_direction_stable:
    Arrange: ExternalSignal(trend_direction="STABLE")
    Assert: trend_direction == "STABLE"

  test_external_signal_trend_direction_falling:
    Arrange: ExternalSignal(trend_direction="FALLING")
    Assert: trend_direction == "FALLING"

  test_external_signal_trend_direction_unknown:
    Arrange: ExternalSignal(trend_direction="UNKNOWN")
    Assert: trend_direction == "UNKNOWN"

  test_external_signal_trend_direction_none:
    Arrange: ExternalSignal without trend_direction
    Assert: trend_direction is None

  test_external_signal_write_helper_accepts_tc1_fields:
    Arrange: call write_external_signal(..., raw_value=0.8, relevance_score=0.9, trend_direction="RISING")
    Assert: returned ExternalSignal.raw_value == 0.8
    Assert: returned ExternalSignal.relevance_score == 0.9
    Assert: returned ExternalSignal.trend_direction == "RISING"

  test_external_signal_backward_compat_aliases_unchanged:
    Arrange: ExternalSignal(signal_value=0.5, signal_json={"key": "val"}, collection_method="test")
    Assert: normalized_value == 0.5 (alias to signal_value)
    Assert: raw_value_json == {"key": "val"} (alias to signal_json)
    Assert: source_name == "test" (alias to collection_method)

Task 3 (LARGE): Run TC-1 tests.
  py -3.12 -m pytest -q tests/unit/test_external_signal_integrity.py --no-header
  All must pass. Zero failures. Record count.

====================================================================
PART 2: DL-207 URL COVERAGE
====================================================================

Task 4 (XXLARGE): Write tests for DL-207 URL fix.
  Create or extend: tests/unit/test_collection_orchestrator.py

  test_collection_url_encodes_single_spaces:
    Arrange: keyword = "python automation script"
    Act: build URL using the fixed path
    Assert: "query=python%20automation%20script" in url OR "query=python+automation+script" in url
    Assert: " " not in url (no raw spaces in URL)

  test_collection_url_starts_with_correct_base:
    Assert: url.startswith("https://www.fiverr.com/search/gigs")
    Assert: "?query=" in url

  test_collection_url_never_bare_path_form:
    Arrange: keyword = "AI agent development"
    Act: build URL
    Assert: "fiverr.com/AI" not in url (no bare path)
    Assert: "fiverr.com/agent" not in url

  test_collection_url_handles_special_characters:
    Arrange: keyword = "C++ programming & automation"
    Act: build URL
    Assert: " " not in url
    Assert: "&" not in url (encoded as %26) OR "+" in url
    Assert: url.startswith("https://www.fiverr.com/search/gigs")

  test_collection_url_handles_empty_keyword:
    Arrange: keyword = ""
    Act: build URL
    # Should either raise ValueError or produce valid empty-query URL
    # Document the behavior -- not a hard assert

  test_collection_url_handles_url_already_encoded:
    # Edge case: keyword with %20 already in it
    Arrange: keyword = "python%20script"
    Act: build URL
    # Should not double-encode (%2520)
    Assert: "%2520" not in url

Task 5 (LARGE): Run DL-207 tests.
  py -3.12 -m pytest -q tests/unit/test_collection_orchestrator.py -k "url" --no-header
  All must pass. Record count.

====================================================================
PART 3: DASHBOARD COVERAGE
====================================================================

Task 6 (XXXLARGE): Write empty-DB tests for all 9 dashboard pages.
  File: tests/unit/test_dashboard_pages.py (update or create)

  Add fixture if not present:
    @pytest.fixture
    def empty_db_engine():
        from sqlalchemy import create_engine; from sqlalchemy.pool import StaticPool
        from src.models.base import Base
        e = create_engine("sqlite:///:memory:", connect_args={"check_same_thread":False}, poolclass=StaticPool)
        Base.metadata.create_all(e)
        return e

    @pytest.fixture
    def empty_db_session(empty_db_engine):
        from sqlalchemy.orm import sessionmaker
        S = sessionmaker(bind=empty_db_engine)
        db = S(); yield db; db.close()

    @pytest.fixture
    def mock_db_context(empty_db_session, mocker):
        from unittest.mock import MagicMock
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=empty_db_session)
        ctx.__exit__ = MagicMock(return_value=False)
        mocker.patch("src.dashboard.db_helpers.get_db_session", return_value=ctx)
        return ctx

  Tests (one per page, by exact name -- F must write ALL 9):
    test_dashboard_opportunities_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_opportunities_page(); assert st.info called
    test_dashboard_keywords_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_keywords_page(); assert st.info called
    test_dashboard_competitors_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_competitors_page(); assert st.info called or placeholder rendered
    test_dashboard_recommendations_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_recommendations_page(); assert st.info called
    test_dashboard_run_history_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_run_history_page(); assert st.info called
    test_dashboard_llm_costs_renders_empty_db_gracefully:
      mock_streamlit; inject empty DB; call render_llm_costs_page(); assert st.info called
    test_dashboard_discovery_renders_empty_db_gracefully:
      mock_streamlit; call render_discovery_page(); assert renders without crash
    test_dashboard_playbook_renders_empty_db_gracefully:
      mock_streamlit; call render_playbook_page(); assert renders without crash (placeholder expected)
    test_dashboard_pricing_renders_empty_db_gracefully:
      mock_streamlit; call render_pricing_page(); assert renders without crash (placeholder expected)

  Mock pattern for streamlit in tests:
    mocker.patch("streamlit.title")
    mocker.patch("streamlit.subheader")
    mocker.patch("streamlit.info")
    mocker.patch("streamlit.error")
    mocker.patch("streamlit.warning")
    mocker.patch("streamlit.success")
    mocker.patch("streamlit.dataframe")
    mocker.patch("streamlit.write")
    mocker.patch("streamlit.columns", return_value=[MagicMock(), MagicMock()])

Task 7 (LARGE): Run dashboard empty-DB tests.
  py -3.12 -m pytest -q tests/unit/test_dashboard_pages.py --no-header
  All 9 empty-DB tests must pass. Record count.

====================================================================
PART 4: REGRESSION PACK AND COVERAGE CHECK
====================================================================

Task 8 (LARGE): Run full 41-name regression pack after F's tests added.
  py -3.12 -m pytest -q -k "test_extract_price_text OR test_parse_gig_detail OR test_parse_seller_profile_from_html_keeps_zero OR test_seller_profile_fetcher OR test_gig_detail_fetcher_does_not_overwrite OR test_seller_profile_live_markup OR test_scoring_fallback_queries_scope OR test_scoring_fallback_queries_recover OR test_demand_uses_search_result OR test_competition_score_session OR test_scoring_uses_card_urls OR test_confidence_modifier_uses OR test_weakness_multi_row_fallback OR test_fiverr_search_url OR test_unconstrained_search_result OR test_eligibility_ghost OR test_demand_qualified OR test_sponsored_gigs OR test_zombie_gigs OR test_organic_trc OR test_niche_profile OR test_opportunity_qualified OR test_price_outlier OR test_llm_relevance_only OR test_llm_ghost OR test_ghost_discovery OR test_feedback_excludes OR test_low_specificity OR test_autocomplete_emerging OR test_reddit_qualified OR test_trends_platform OR test_external_signal_quality_not OR test_external_signal_quality_blended OR test_confidence_context_handles OR test_ghost_market_excluded OR test_all_non_ghost_tags OR test_empty_run_returns OR test_ghost_filter_handles OR test_llm_alert_counts OR test_stealth_sponsored OR test_first_recommendation_quality" --no-header
  Expected: 88+ passed. New tests on top. Zero failures.

Task 9 (LARGE): Coverage measurement (F runs partial coverage -- D runs the full --cov=src).
  py -3.12 -m pytest -q --cov=src/models/external_signal --cov=src/collection/orchestrator --cov=src/dashboard/pages --cov-report=term-missing --no-header 2>&1 | tail -20
  Record coverage % for each module. This is F's contribution to coverage -- D will run the full suite.
  Note: F does NOT run --cov=src (that is G-004 exclusively for D).

Task 10 (LARGE): Identify remaining coverage gaps and document for D.
  10a. From coverage output: which lines are NOT covered in TC-1 model changes?
  10b. Which URL-path branches in orchestrator are not exercised?
  10c. Which dashboard page branches (with-data path) are not covered?
  10d. Document all gaps in F report under "Coverage Gaps for D."
  10e. F does NOT need to achieve 100% -- D will review the final numbers.

====================================================================
PART 5: NEW REGRESSIONS
====================================================================

Task 11 (LARGE): Determine which new tests should join the sec7 regression pack.
  11a. List all new test names F added this cycle.
  11b. For EACH new test: is it a regression-worthy test? (Would failure signal a real regression?)
  11c. Candidates for REG-41+:
       - test_external_signal_raw_value_stored_and_retrieved (TC-1)
       - test_external_signal_relevance_score_full_range (TC-1)
       - test_collection_url_encodes_single_spaces (DL-207)
       - test_collection_url_never_bare_path_form (DL-207)
       - test_dashboard_opportunities_renders_empty_db_gracefully
  11d. Record proposed REG-41 through REG-N in F report.
  11e. D will officially add these to sec7 pack if all pass.

====================================================================
PART 6: F REPORT AND SIGNAL
====================================================================

Task 12 (LARGE): Create CYCLE_061_AGENT_F.md.
  Contents:
  ## Preflight (C GO confirmed)
  ## TC-1 Tests (list all test names, pass/fail count)
  ## DL-207 Tests (list all test names, pass/fail count)
  ## Dashboard Tests (list all 9 test names, pass/fail count)
  ## Regression Pack (88+ passed, any new tests)
  ## Partial Coverage (external_signal %, orchestrator %, dashboard pages %)
  ## Coverage Gaps for D (uncovered lines)
  ## New Regression Candidates (REG-41+)
  ## Zone Verification (only tests/ + F report in F commits)
  ## Signal: "F complete. D may proceed."

Task 13 (LARGE): Zone verification.
  git show --name-only <F_SHA>
  Must contain ONLY: tests/ files + docs/cycle_reports/CYCLE_061_AGENT_F.md
  Zero src/ files.

Task 14 (LARGE): Commit and push F deliverables.
  git add tests/ docs/cycle_reports/CYCLE_061_AGENT_F.md
  git commit -m "test(hardening): C061 F coverage -- TC-1 ExternalSignal tests, DL-207 URL tests, dashboard empty-DB tests"
  git push origin cycle/061/integration
  Record F commit SHA.

Task 15 (LARGE): Jira -- comment on relevant stories.
  TC-1 story: "F added N TC-1 tests. Coverage delta: +X%."
  DL-207 story: "F added N URL encoding tests. All pass."
  Dashboard story: "F added 9 empty-DB tests. All pass."

Task 16 (LARGE): Final test count verification.
  py -3.12 -m pytest --collect-only -q 2>&1 | tail -5
  Record total test count. Delta from C060 baseline (4022): must be positive.

Task 17 (LARGE): Check for any test naming collisions.
  py -3.12 -m pytest --collect-only -q 2>&1 | Select-String "ERROR\|collision\|duplicate" | head -10
  Expected: empty. Any collision = naming issue. Fix before committing.

Task 18 (LARGE): Verify test files are in the correct test directory.
  Get-ChildItem tests/unit/ | Select Name | Sort-Object
  New test files must be in tests/unit/. Not in src/ or project root.

Task 19 (LARGE): Run mypy on test files (optional but good practice).
  py -3.12 -m mypy tests/unit/test_external_signal_integrity.py tests/unit/test_collection_orchestrator.py tests/unit/test_dashboard_pages.py --ignore-missing-imports 2>&1 | tail -5
  Record output. Any errors: fix before committing.

Task 20 (LARGE): Update Jira control task.
  Comment: "F complete. SHA: <F_SHA>. Tests added: TC-1 (N), DL-207 (N), dashboard empty-DB (9).
  Total new tests: N. Regression pack: 88+ passed. D may proceed."

Task 21 (LARGE): Verify no src/ files were accidentally staged.
  git diff --cached --name-only | Select-String "^src/"
  Must return empty. Any src/ file staged = zone violation. Unstage immediately.

Task 22 (LARGE): Run full unit suite one final time before signaling D.
  py -3.12 -m pytest -q tests/unit/ --no-header
  Must pass. Record count. No failures.

Task 23 (LARGE): Document test architecture decisions.
  For each new test file: document in F report:
  - Why these test names were chosen
  - What behavior each test validates
  - Which C061 deliverable each test covers (TC-1, DL-207, or dashboard)
  - Whether it's a regression candidate (sec7 pack)

Task 24 (LARGE): Verify F's tests are independent (no inter-test dependencies).
  24a. Run tests in random order: py -3.12 -m pytest -q tests/unit/test_external_signal_integrity.py -p no:randomly --no-header
  24b. Run in reverse: py -3.12 -m pytest -q tests/unit/test_external_signal_integrity.py --reversed --no-header
  24c. Both must produce same results. Any order-dependent failure = test design issue.

Task 25 (LARGE): Final F checklist.
  [ ] TC-1 tests: 12 tests (raw_value, relevance_score, trend_direction variants)
  [ ] DL-207 tests: 6 tests (encoding, base URL, bare path, special chars, edge cases)
  [ ] Dashboard tests: 9 tests (one per page, empty-DB graceful)
  [ ] Total new tests: >=27
  [ ] All tests pass: zero failures
  [ ] Regression pack: 88+ passed including new tests
  [ ] Partial coverage measured (external_signal, orchestrator, dashboard pages)
  [ ] Coverage gaps documented for D
  [ ] REG-41+ candidates listed
  [ ] Zone: only tests/ + F report in F commits
  [ ] No src/ in F's commits
  [ ] CYCLE_061_AGENT_F.md committed
  [ ] Signal: "F complete. D may proceed."

====================================================================
HARD GATE RULES (verbatim)
====================================================================

G-001: Enforced CI + codecov/project >=90%.
G-004: ONE --cov=src by D only. F runs partial coverage on specific modules only.
G-005: Golden PASS. kw=110 = 62.7/1.0/CONDITIONAL_GO.
sec7: New regressions added by F are candidates for REG-41+; D officially adds them.

====================================================================
ACCUMULATED REGRESSION PACK (sec7 v2.4 -- 41 names)
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

END OF PROMPT

====================================================================
INLINE TEST TEMPLATES FOR F (mandatory content)
====================================================================

## test_external_signal_integrity.py complete skeleton

    # tests/unit/test_external_signal_integrity.py
    """TC-1 tests: raw_value, relevance_score, trend_direction on ExternalSignal."""
    import pytest
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from src.models.base import Base
    from src.models.external_signal import ExternalSignal, write_external_signal

    @pytest.fixture
    def db_session():
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        db = Session()
        yield db
        db.close()


    def test_external_signal_raw_value_stored_and_retrieved(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="google_trends", raw_value=0.75)
        db_session.add(row); db_session.commit(); db_session.refresh(row)
        reloaded = db_session.query(ExternalSignal).filter_by(id=row.id).first()
        assert reloaded.raw_value == 0.75


    def test_external_signal_raw_value_zero_stored(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="google_trends", raw_value=0.0)
        db_session.add(row); db_session.commit(); db_session.refresh(row)
        assert row.raw_value == 0.0  # 0.0 is valid, not None


    def test_external_signal_raw_value_column_nullable(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="google_trends")
        db_session.add(row); db_session.commit()
        assert row.raw_value is None


    def test_external_signal_relevance_score_defaults_none(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="reddit_demand")
        db_session.add(row); db_session.commit()
        assert row.relevance_score is None


    @pytest.mark.parametrize("score", [0.0, 0.25, 0.5, 0.75, 1.0])
    def test_external_signal_relevance_score_full_range(db_session, score):
        row = ExternalSignal(keyword_id=1, signal_type="reddit_demand", relevance_score=score)
        db_session.add(row); db_session.commit(); db_session.refresh(row)
        assert row.relevance_score == score


    @pytest.mark.parametrize("direction", ["RISING", "STABLE", "FALLING", "UNKNOWN"])
    def test_external_signal_trend_direction_valid_values(db_session, direction):
        row = ExternalSignal(keyword_id=1, signal_type="google_trends", trend_direction=direction)
        db_session.add(row); db_session.commit(); db_session.refresh(row)
        assert row.trend_direction == direction


    def test_external_signal_trend_direction_none(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="google_trends")
        db_session.add(row); db_session.commit()
        assert row.trend_direction is None


    def test_external_signal_write_helper_accepts_tc1_fields(db_session):
        result = write_external_signal(
            keyword_id=1, signal_type="google_trends", signal_value=0.6,
            signal_json=None, run_id="run_001", collection_method="api",
            db=db_session,
            raw_value=0.8, relevance_score=0.9, trend_direction="RISING",
        )
        assert result is not None
        assert result.raw_value == 0.8
        assert result.relevance_score == 0.9
        assert result.trend_direction == "RISING"


    def test_external_signal_backward_compat_normalized_value(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="test", signal_value=0.5)
        db_session.add(row); db_session.commit()
        assert row.normalized_value == 0.5  # alias to signal_value


    def test_external_signal_backward_compat_raw_value_json(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="test", signal_json={"k": "v"})
        db_session.add(row); db_session.commit()
        assert row.raw_value_json == {"k": "v"}  # alias to signal_json


    def test_external_signal_backward_compat_source_name(db_session):
        row = ExternalSignal(keyword_id=1, signal_type="test", collection_method="scrape")
        db_session.add(row); db_session.commit()
        assert row.source_name == "scrape"  # alias to collection_method


## test_collection_orchestrator.py URL test skeleton

    # Tests to add to tests/unit/test_collection_orchestrator.py
    from urllib.parse import quote, unquote

    def test_collection_url_encodes_spaces_correctly():
        """DL-207: URL construction must encode spaces."""
        from src.collection.orchestrator import build_fiverr_search_url
        url = build_fiverr_search_url("python automation script")
        assert " " not in url, f"Unencoded space in URL: {url}"
        assert "python" in url.lower()
        assert "script" in url.lower()

    def test_collection_url_format_is_search_gigs():
        """DL-207: URL must use /search/gigs?query= format."""
        from src.collection.orchestrator import build_fiverr_search_url
        url = build_fiverr_search_url("AI agent development")
        assert url.startswith("https://www.fiverr.com/search/gigs"), f"Wrong format: {url}"
        assert "?query=" in url, f"Missing ?query= in URL: {url}"

    def test_collection_url_never_bare_path():
        """DL-207: URL must not be a bare path like /Python automation."""
        from src.collection.orchestrator import build_fiverr_search_url
        url = build_fiverr_search_url("Python automation script")
        assert "fiverr.com/Python" not in url, f"Bare path detected: {url}"
        assert "fiverr.com/automation" not in url, f"Bare path detected: {url}"

====================================================================
TASKS 26-32 (additional substantive tasks)
====================================================================

Task 26 (LARGE): Verify all 12 TC-1 tests pass together as a suite.
  py -3.12 -m pytest -q tests/unit/test_external_signal_integrity.py -v --no-header
  Record each test name and PASS/FAIL. All must pass.

Task 27 (LARGE): Verify all DL-207 URL tests pass.
  py -3.12 -m pytest -q tests/unit/test_collection_orchestrator.py -k "url" -v --no-header
  Record each test name and PASS/FAIL. All must pass.

Task 28 (LARGE): Verify all 9 dashboard empty-DB tests pass.
  py -3.12 -m pytest -q tests/unit/test_dashboard_pages.py -v --no-header
  Record each test name and PASS/FAIL. All 9 must pass.

Task 29 (LARGE): Count new tests and confirm delta.
  py -3.12 -m pytest --collect-only -q tests/unit/test_external_signal_integrity.py tests/unit/test_collection_orchestrator.py tests/unit/test_dashboard_pages.py 2>&1 | tail -5
  Expected new tests: 12 (TC-1) + 6 (DL-207 URL) + 9 (dashboard) = 27 minimum.
  If fewer: F missed some tests. Add missing ones.

Task 30 (LARGE): Update sec7 proposal in F report.
  Current pack: 41 tests (REG-1 through REG-40).
  Proposed additions for D to evaluate:
    REG-41: test_external_signal_raw_value_stored_and_retrieved
    REG-42: test_external_signal_relevance_score_full_range (parametrized -- track as single entry)
    REG-43: test_collection_url_encodes_spaces_correctly
    REG-44: test_collection_url_never_bare_path
    REG-45: test_dashboard_opportunities_renders_empty_db_gracefully
  D decides final numbering. F proposes.

Task 31 (LARGE): Run golden parity after adding new tests (confirm no breakage).
  py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override analysis.external_signals_enabled=false
  kw=110 must still be 62.7/1.0/CONDITIONAL_GO.
  Adding tests must not change golden outcomes.

Task 32 (LARGE): Final verification run of all F deliverables.
  py -3.12 -m pytest -q tests/unit/ --no-header 2>&1 | tail -5
  Record final total count. Must include all 41 original + new tests. Zero failures.
