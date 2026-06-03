# CYCLE 061 -- AGENT C PROMPT
# Role: Integration verifier (after B AND E, before F)
# Stage: 3 (after BOTH B and E -- NEVER after F)
# Base SHA: 9687fb6f38ebca8b01cefa845630ea4f2b609c07
# Branch: cycle/061/integration

====================================================================
STAGE CONTEXT (CRITICAL -- read before any other step)
====================================================================

C runs AFTER both Agent B and Agent E.
C runs BEFORE Agent F.
C NEVER waits for Agent F.
C's prerequisite: BOTH B and E must have signaled ready.

If only B has signaled (E not yet done): WAIT for E before starting verification.
If only E has signaled (B not yet done): WAIT for B before starting verification.

C's scope:
  - Verify B's implementation (TC-1, DL-207, dashboard wiring)
  - Verify E's report (no src/ files)
  - Run full regression pack
  - Run golden parity
  - Issue GO/NO-GO verdict for Agent F

====================================================================
PROJECT CONTEXT
====================================================================

Working dir: C:\Fiverr\Fiverr | Python: py -3.12
Jira: eae77257-a572-4e19-b746-8b184ba2d01f | Connector auth only

====================================================================
PREFLIGHT
====================================================================

Task 1 (LARGE): Preflight checks.
  1a. git pull origin cycle/061/integration -- get latest B and E commits
  1b. git log --oneline -10 -- confirm B commit and E commit are both present
  1c. Read docs/cycle_reports/CYCLE_061_AGENT_B.md -- confirm B signals ready
  1d. Read docs/cycle_reports/CYCLE_061_AGENT_E.md -- confirm E signals ready
  1e. py -3.12 run.py config-check -- niches=9
  Record all outputs. If B or E is not ready: do NOT proceed with verification.

====================================================================
PART 1: TC-1 SECTION 11.3 PRAGMA CHECK (BLOCKING)
====================================================================

Task 2 (XXLARGE): sec11.3 PRAGMA cross-check -- IMMEDIATE NO-GO if columns missing.
  2a. Run PRAGMA on foundation_gate_ci.db:
      py -3.12 -c "
      from sqlalchemy import create_engine, inspect
      e = create_engine('sqlite:///data/foundation_gate_ci.db')
      cols = sorted([c['name'] for c in inspect(e).get_columns('external_signals')])
      required = {'raw_value', 'relevance_score', 'trend_direction'}
      missing = required - set(cols)
      print('external_signals columns:', cols)
      print('TC-1 STATUS:', 'PASS' if not missing else f'FAIL -- missing: {missing}')
      "
  2b. If ANY of raw_value/relevance_score/trend_direction is absent: IMMEDIATE NO-GO.
      Comment on B's Jira story: "C PRAGMA FAIL -- raw_value/relevance_score/trend_direction missing from external_signals. B must apply migration_11 and re-push."
      Do NOT proceed with further verification until B fixes this.
  2c. If all 3 present: record "TC-1 PRAGMA PASS" in C report.
  Record: full column list and PASS/FAIL status.

Task 3 (LARGE): Verify sec11.2 parity table is in B report.
  3a. Read docs/cycle_reports/CYCLE_061_AGENT_B.md.
  3b. Confirm the parity table is present with ALL YES rows for raw_value, relevance_score, trend_direction.
  3c. If parity table missing or has NO rows: document as a process gap (NOT a blocking failure for C).

====================================================================
PART 2: DL-207 URL VERIFICATION
====================================================================

Task 4 (LARGE): Verify DL-207 URL construction fix.
  4a. Run URL test:
      py -3.12 -c "
      from urllib.parse import quote
      kws = ['python automation script', 'AI agent development', 'PRD template fiverr']
      for kw in kws:
          enc = quote(kw.strip(), safe='')
          url = f'https://www.fiverr.com/search/gigs?query={enc}'
          assert ' ' not in url, f'UNENCODED SPACE in URL: {url}'
          assert 'search/gigs' in url, f'WRONG URL FORMAT: {url}'
          print(f'PASS: {url}')
      print('DL-207 URL: ALL PASS')
      "
  4b. Run DL-207-specific tests:
      py -3.12 -m pytest -q tests/unit/test_collection_orchestrator.py -k "url_encodes or url_format or bare_path" --no-header
      Record results.

====================================================================
PART 3: DASHBOARD DEMO-DATA CHECK (BLOCKING)
====================================================================

Task 5 (XXLARGE): Verify all 9 pages removed build_dashboard_demo_data -- BLOCKING.
  5a. Run:
      Get-ChildItem src\dashboard\pages\ | ForEach-Object {
          $match = Get-Content $_.FullName | Select-String "build_dashboard_demo_data"
          if($match){ Write-Host "DEMO_DATA_STILL_PRESENT: $($_.Name)" }
      }
  5b. If ANY page still has the import: IMMEDIATE NO-GO.
      Comment on B's Jira story: "C FAIL -- dashboard page [name] still imports build_dashboard_demo_data. B must complete live-data wiring."
      Do NOT issue GO until all 9 pages are clean.
  5c. If all clean: record "DASHBOARD DEMO-DATA CHECK PASS" in C report.

Task 6 (LARGE): Verify dashboard pages import cleanly.
  6a. For each of the 9 dashboard pages:
      py -3.12 -c "from src.dashboard.pages.opportunities import render_opportunities_page; print('OK')"
      (repeat for each page)
  6b. Any ImportError = document as gap in C report. Route to B for fix.

====================================================================
PART 4: AGENT E ZONE CHECK
====================================================================

Task 7 (LARGE): Verify E committed only the E report.
  7a. Find E's commit SHA from git log --oneline.
  7b. git show --name-only <E_SHA>
      Must contain ONLY: docs/cycle_reports/CYCLE_061_AGENT_E.md
  7c. If ANY src/ file in E's commit: ZONE VIOLATION. Document and stop merge path until investigated.

====================================================================
PART 5: REGRESSION PACK
====================================================================

Task 8 (XXLARGE): Run full 41-name regression pack.
  py -3.12 -m pytest -q -k "test_extract_price_text OR test_parse_gig_detail OR test_parse_seller_profile_from_html_keeps_zero OR test_seller_profile_fetcher OR test_gig_detail_fetcher_does_not_overwrite OR test_seller_profile_live_markup OR test_scoring_fallback_queries_scope OR test_scoring_fallback_queries_recover OR test_demand_uses_search_result OR test_competition_score_session OR test_scoring_uses_card_urls OR test_confidence_modifier_uses OR test_weakness_multi_row_fallback OR test_fiverr_search_url OR test_unconstrained_search_result OR test_eligibility_ghost OR test_demand_qualified OR test_sponsored_gigs OR test_zombie_gigs OR test_organic_trc OR test_niche_profile OR test_opportunity_qualified OR test_price_outlier OR test_llm_relevance_only OR test_llm_ghost OR test_ghost_discovery OR test_feedback_excludes OR test_low_specificity OR test_autocomplete_emerging OR test_reddit_qualified OR test_trends_platform OR test_external_signal_quality_not OR test_external_signal_quality_blended OR test_confidence_context_handles OR test_ghost_market_excluded OR test_all_non_ghost_tags OR test_empty_run_returns OR test_ghost_filter_handles OR test_llm_alert_counts OR test_stealth_sponsored OR test_first_recommendation_quality" --no-header
  Expected: 88+ passed. Zero failures.
  If any failure: document failing test name + error. Route to B. Issue NO-GO.

Task 9 (LARGE): Run new C061 tests (TC-1, DL-207, dashboard).
  py -3.12 -m pytest -q tests/unit/ -k "raw_value OR relevance_score OR trend_direction OR url_encodes OR bare_path OR empty_db" --no-header
  Record: count of new tests passing.

====================================================================
PART 6: GOLDEN PARITY AND LINT
====================================================================

Task 10 (LARGE): Golden parity (G-005).
  py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override analysis.external_signals_enabled=false
  Must show: kw=110 = 62.7/1.0/CONDITIONAL_GO | kw=96 = 35.8 | kw=3 = 56.66
  If kw=110 changes: NO-GO. Investigate before issuing GO to F.

Task 11 (LARGE): Ruff and mypy.
  py -3.12 -m ruff check . -- PASS
  py -3.12 -m mypy src -- PASS
  Either failure: route to B, issue NO-GO.

Task 12 (LARGE): Config gate.
  Get-Content config.yaml | Select-String "scrapfly"
  collection.scrapfly.enabled must be false in committed config.
  If true: CONFIG GATE VIOLATION. Route to B. NO-GO.

====================================================================
PART 7: C REPORT AND SIGNAL
====================================================================

Task 13 (LARGE): Create CYCLE_061_AGENT_C.md.
  Contents:
  ## Preflight (B ready + E ready)
  ## TC-1 sec11.3 PRAGMA (full output, PASS/FAIL)
  ## DL-207 URL (test outputs, PASS/FAIL)
  ## Dashboard Demo-Data (all 9 pages clean or gaps documented)
  ## Dashboard Import Smoke (all 9 pages import OK or errors)
  ## E Zone Check (E SHA, files committed -- only E report)
  ## Regression Pack (count, any failures)
  ## New C061 Tests (count)
  ## Golden Parity (kw=110 value, PASS/FAIL)
  ## Ruff + Mypy (PASS/FAIL)
  ## Config Gate (scrapfly.enabled, PASS/FAIL)
  ## GO/NO-GO Verdict (one of: GO / NO-GO: [reason])
  ## Signal to F: "C issues [GO/NO-GO]. F may [proceed/wait for B fix]."

Task 14 (LARGE): Issue GO/NO-GO verdict.
  GO criteria (ALL must be true):
    [ ] TC-1 PRAGMA: all 3 columns present
    [ ] Dashboard: zero build_dashboard_demo_data imports
    [ ] Regression pack: 88+ passed, 0 failed
    [ ] Golden: kw=110 = 62.7/1.0/CONDITIONAL_GO
    [ ] Ruff: PASS | Mypy: PASS
    [ ] Config gate: scrapfly.enabled=false
    [ ] E zone: only E report in E's commit

  If ALL pass: GO. F may proceed.
  If ANY fail: NO-GO. Document which item failed. Route fix to B. Signal F to wait.

Task 15 (LARGE): Commit and push C report.
  git add docs/cycle_reports/CYCLE_061_AGENT_C.md
  git commit -m "docs(cycle061): Agent C integration -- TC-1 PRAGMA, DL-207, dashboard check, regression pack"
  git push origin cycle/061/integration
  Record C commit SHA.

====================================================================
ADDITIONAL TASKS 16-25
====================================================================

Task 16 (LARGE): Verify B sec11.2 parity table completeness.
  In B report: every existing ExternalSignal ORM column must map to a migration or CREATE TABLE.
  If B report shows any "NO" row: document as gap even if C's verification passed.

Task 17 (LARGE): Verify no accidentally-tracked artifacts.
  git diff --name-only origin/develop..HEAD -- data/ *.db *.log *.xml
  Must show empty. Any tracked DB, coverage, or log file = hygiene issue. Document.

Task 18 (LARGE): Check DL-207 fix in orchestrator specifically.
  py -3.12 -c "
  import importlib.util, inspect
  spec = importlib.util.spec_from_file_location('orch', 'src/collection/orchestrator.py')
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  src = inspect.getsource(m)
  has_quote = 'quote(' in src
  has_search_gigs = 'search/gigs' in src
  print(f'has_quote={has_quote}, has_search_gigs={has_search_gigs}')
  "
  Both should be True.

Task 19 (LARGE): Check for any B zone violations (comprehensive).
  base_sha = Invoke-Exe git 'merge-base origin/develop HEAD'
  Invoke-Exe git 'log --oneline $base_sha..HEAD'
  For EACH commit SHA in the list: git show --name-only <SHA>
  Verify: each B commit touches only src/ or docs/cycle_reports/CYCLE_061_AGENT_B.md.
  Any PM_Pack/ or tests/ in B commit: zone violation. Document.

Task 20 (LARGE): Verify foundation-gate and phase2-smoke.
  py -3.12 run.py foundation-gate -- PASS
  py -3.12 run.py phase2-smoke -- PASS
  Either failure: document and route to B. If these fail, issue NO-GO.

Task 21 (LARGE): Run targeted TC-1 model tests.
  py -3.12 -m pytest -q tests/unit/ -k "external_signal" --no-header
  All external_signal tests must pass. Record count.

Task 22 (LARGE): Update Jira control task.
  Comment: "C complete. SHA: <C_SHA>. TC-1 PRAGMA: PASS/FAIL. Dashboard: PASS/FAIL.
  Regression: 88+ passed. Golden: 62.7. Verdict: GO/NO-GO.
  F may proceed after this GO / F must wait for B fix."

Task 23 (LARGE): Verify no src/ changes from C.
  git show --name-only <C_SHA>
  Must contain ONLY: docs/cycle_reports/CYCLE_061_AGENT_C.md

Task 24 (LARGE): Document any carry-forward items for D's attention.
  If any item was borderline (not GO but not hard-blocking):
    Document in C report under "D Attention Items"
    Example: "DL-207 URL format not verified from live logs -- E report says inconclusive"
    D must independently verify these items.

Task 25 (LARGE): Final C checklist.
  [ ] TC-1 PRAGMA PASS (all 3 columns confirmed)
  [ ] Dashboard PASS (zero build_dashboard_demo_data imports)
  [ ] E zone PASS (only E report in E's commit)
  [ ] Regression pack 88+ PASS
  [ ] Golden 62.7/1.0/CONDITIONAL_GO PASS
  [ ] Ruff + mypy PASS
  [ ] Config gate scrapfly.enabled=false PASS
  [ ] Foundation-gate + phase2-smoke PASS
  [ ] GO/NO-GO verdict documented with reasoning
  [ ] CYCLE_061_AGENT_C.md committed
  [ ] Signal: "C issues [GO/NO-GO]. F may [proceed/wait]."

====================================================================
HARD GATE RULES (verbatim)
====================================================================

G-001: Enforced CI + codecov/project >=90%.
G-004: ONE --cov=src by D only. C does NOT run --cov=src.
G-005: Golden PASS. kw=110 = 62.7/1.0/CONDITIONAL_GO.
CONFIG: scrapfly.enabled=false confirmed.
sec11.3 PRAGMA: BLOCKING. If TC-1 columns missing: NO-GO immediately.

END OF PROMPT

====================================================================
ADDITIONAL TASKS 11-25 (C expansion to meet 425-line floor)
====================================================================

Task 11 (LARGE): Verify B sec11.2 parity table is complete.
  11a. Open docs/cycle_reports/CYCLE_061_AGENT_B.md.
  11b. Locate the "sec11.2 parity table" section.
  11c. Verify every ExternalSignal ORM column maps to either:
       - The original CREATE TABLE (for pre-existing columns)
       - migration_11 (for raw_value, relevance_score, trend_direction)
  11d. All "Present?" cells must be YES.
  11e. If any cell is NO or missing: record as defect in C report. Do NOT issue GO.

Task 12 (LARGE): Verify B zone coverage (comprehensive commit audit).
  12a. Get base SHA: Invoke-Exe git 'merge-base origin/develop HEAD'
  12b. List all commits in cycle range: Invoke-Exe git 'log --oneline <base_sha>..HEAD'
  12c. For EACH commit SHA: Invoke-Exe git 'show --name-only <SHA>'
  12d. Categorize:
       - B commits: must touch only src/ + tests/ + docs/cycle_reports/CYCLE_061_AGENT_B.md
       - E commits: must touch only docs/cycle_reports/CYCLE_061_AGENT_E.md
       - A commits: docs/ + PM_Pack/ only (no src/)
       - Any violation: document in C report
  12e. Record every SHA and its file list in C report.

Task 13 (LARGE): Run dashboard empty-DB tests if B added them.
  13a. py -3.12 -m pytest -q tests/unit/test_dashboard_pages.py --no-header
  13b. If test file doesn't exist: record "F will add dashboard tests (C's verification was page imports only)."
  13c. If test file exists: must pass. Record count.

Task 14 (LARGE): Verify config.yaml external_signals toggle state.
  14a. py -3.12 -c "import yaml; cfg=yaml.safe_load(open('config.yaml')); ext=cfg.get('analysis',{}).get('external_signals_enabled',False); print(f'external_signals_enabled={ext}')"
  14b. If ext=true AND TC-1 columns are PRESENT: acceptable (B enabled P1 correctly).
  14c. If ext=true AND TC-1 columns are ABSENT: PROBLEM. Toggle enabled without migration. Route to B.
  14d. If ext=false: acceptable (P1 was not completed this cycle or B chose to defer).
  Record: toggle state and whether it is consistent with TC-1 PRAGMA.

Task 15 (LARGE): Full suite run (not --cov, that is D only).
  py -3.12 -m pytest -q tests/unit/ --no-header 2>&1 | Select-Object -Last 10
  Must show all passing. Zero failures. Record total count.
  Note: C does NOT run --cov=src (G-004: only D runs coverage).

Task 16 (LARGE): Verify orchestrator imports are not broken by B's changes.
  py -3.12 -c "from src.collection.orchestrator import Orchestrator; print('Orchestrator import: OK')" 2>&1
  Any ImportError = B's changes broke orchestrator import. Route to B. NO-GO.

Task 17 (LARGE): Verify migration_11 is registered in run_srdi_r8_migrations.py.
  py -3.12 -c "
  with open('src/migrations/srdi_r8/run_srdi_r8_migrations.py') as f: txt = f.read()
  if 'migration_11' in txt: print('migration_11 REGISTERED: YES')
  else: print('migration_11 REGISTERED: NO -- missing from run_srdi_r8_migrations.py')
  "
  If NO: sec11 violation. B must register migration_11. Issue NO-GO.

Task 18 (LARGE): Check for common dashboard wiring anti-patterns.
  18a. Search for any hardcoded demo-data calls in dashboard:
       git grep -rn "DEMO\|demo_data\|fake_data\|placeholder_data" src/dashboard/ --include="*.py"
  18b. Search for any remaining references to non-DB data patterns:
       git grep -rn "pd.DataFrame\(\[{" src/dashboard/pages/ --include="*.py" | head -5
       (Some fixture-style DataFrames are OK if they're the fallback, but pure hardcoded demo lists are not)
  18c. Document findings in C report.

Task 19 (LARGE): Verify new tests from B exist and are named correctly.
  19a. py -3.12 -m pytest --collect-only -q tests/unit/ 2>&1 | Select-String "test_external_signal_raw_value\|test_collection_url_encodes\|test_dashboard" | head -20
  19b. Expect to see: test_external_signal_raw_value_persists, test_collection_url_encodes_spaces_correctly.
  19c. If tests are absent: record as gap for F to fill.

Task 20 (LARGE): Regression delta check (new tests vs. old failing tests).
  20a. Record baseline: 4022 tests at C060 start.
  20b. Current total: py -3.12 -m pytest --collect-only -q 2>&1 | tail -5
  20c. Delta: new tests count = current - 4022. Document in C report.
  20d. If delta < 5: B may not have added enough tests for C061 scope. Document.

Task 21 (LARGE): Confirm single worktree.
  git worktree list
  Must show exactly one worktree at C:\Fiverr\Fiverr.
  Multiple worktrees = unexpected state. Document.

Task 22 (LARGE): Check .env is not tracked.
  git diff --name-only HEAD~1..HEAD -- .env
  Must return empty. If .env appears in any commit: security issue. IMMEDIATE NO-GO.

Task 23 (LARGE): Verify data directory is not polluted.
  git diff --name-only origin/develop..HEAD -- data/
  Must return empty. Any .db or .json in data/ committed to branch = hygiene issue.

Task 24 (LARGE): Confirm Jira stories moved to correct status.
  24a. Via Atlassian connector: search for SCRUM stories created by A for C061.
  24b. TC-1 story, DL-207 story, dashboard story should be "Done" after B's work.
  24c. If still "In Progress": record as Jira hygiene gap.

Task 25 (LARGE): Final C checklist before issuing verdict.
  [ ] TC-1 sec11.3 PRAGMA: all 3 columns present
  [ ] sec11.2 parity table: all YES in B report
  [ ] migration_11 registered in run_srdi_r8_migrations.py
  [ ] Dashboard: zero build_dashboard_demo_data imports in all 9 pages
  [ ] Dashboard pages: all import cleanly
  [ ] E zone: only E report in E's commit
  [ ] Regression pack: 88+ passed, 0 failed
  [ ] New C061 tests: present (TC-1 + DL-207 + dashboard)
  [ ] Golden: kw=110 = 62.7/1.0/CONDITIONAL_GO
  [ ] Ruff + mypy: PASS
  [ ] Config gate: scrapfly.enabled=false
  [ ] external_signals_enabled toggle: consistent with TC-1 PRAGMA
  [ ] Foundation-gate + phase2-smoke: PASS
  [ ] B zone: only src/ + tests/ + B report in B commits
  [ ] Single worktree, no .env tracked, no data/ in branch
  [ ] GO/NO-GO verdict documented with each criterion
  [ ] CYCLE_061_AGENT_C.md committed

====================================================================
REGRESSION PACK (sec7 v2.4 -- 41 names -- run ALL by exact name)
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
test_fiverr_search_url_always_includes_category_filter_for_production_niches
test_unconstrained_search_result_applies_demand_confidence_deduction
test_eligibility_ghost_hard_block_even_when_forced
test_demand_qualified_trc_when_rsv_below_080
test_sponsored_gigs_never_included_in_competition_top10
test_zombie_gigs_never_used_in_feasibility_review_barrier
test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent
test_niche_profile_excludes_contaminated_keywords
test_opportunity_qualified_by_relevance
test_price_outlier_excluded_from_competition_and_profitability
test_llm_relevance_only_triggers_in_ambiguous_band
test_llm_ghost_verdict_blocks_recommendation
test_ghost_discovery_recorded_as_invalid_not_miss
test_feedback_excludes_contaminated_outcomes
test_low_specificity_hypothesis_rejected
test_autocomplete_emerging_keyword_gets_neutral_not_zero_score
test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low
test_trends_platform_qualifier_applied_before_demand_score_calculation
test_external_signal_quality_not_blended_without_signal_context
test_external_signal_quality_blended_when_signal_context_present
test_confidence_context_handles_naive_external_signal_timestamp
test_ghost_market_excluded_from_opportunities_by_default
test_all_non_ghost_tags_render_correctly
test_empty_run_returns_no_alerts
test_ghost_filter_handles_null_and_legacy_rows
test_llm_alert_counts_actual_stage_7_5_executions
test_stealth_sponsored_monitor_fires_on_fixture
test_first_recommendation_quality_gate_blocks_missing_rsv
