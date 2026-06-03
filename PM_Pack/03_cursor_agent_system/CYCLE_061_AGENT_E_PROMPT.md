# CYCLE 061 -- AGENT E PROMPT
# Role: Live validation and URL shape verification
# Base SHA: 9687fb6f38ebca8b01cefa845630ea4f2b609c07
# Branch: cycle/061/integration | Stage 2 (parallel with B, after A)

====================================================================
PARALLEL EXECUTION NOTICE (sec12.1) -- READ THIS FIRST
====================================================================

YOU ARE RUNNING IN PARALLEL WITH AGENT B.
Agent B is simultaneously committing src/ changes to this branch.
When you run git log, you WILL see Agent B commits. This is EXPECTED and CORRECT.
DO NOT halt. DO NOT alarm. DO NOT report Agent B's commits as unexpected.
Verify YOUR OWN zone: git show --name-only <YOUR_OWN_SHA>
Expected: ONLY docs/cycle_reports/CYCLE_061_AGENT_E.md in your commit.

====================================================================
STAGE AND CONTEXT
====================================================================

Stage 2 -- parallel with B, after A, before C.
E commits ONLY: docs/cycle_reports/CYCLE_061_AGENT_E.md
E NEVER modifies: src/, tests/, config.yaml, PM_Pack/, or any other file.

Working dir: C:\Fiverr\Fiverr | Python: py -3.12
Throwaway DB: data/cycle061_e2e.db (NEVER data/cycle037_live.db)

====================================================================
E EXPLICIT ZONE RULE (HARD -- no exceptions)
====================================================================

E may commit ONLY: docs/cycle_reports/CYCLE_061_AGENT_E.md

PROHIBITED under ANY circumstance:
  - src/ files of any kind, even "trivial" ones
  - tests/ files
  - config.yaml
  - PM_Pack/ files
  - Any file other than the E report

If E encounters a missing module or broken import during testing:
  DO NOT add the missing src/ file.
  Record the gap in the E report for Agent B to fix.
  Proceed with what is available.

If the E prompt says "add this to src/": that instruction is WRONG. Record the gap and continue.

NO PAD LINES: CYCLE_061_AGENT_E.md must contain ONLY substantive project content.
"floor-line-NNN: retained for floor compliance" is PROHIBITED.
Fill the 500-line floor with actual findings, commands run, output evidence, and analysis.

====================================================================
CYCLE 061 E MISSION
====================================================================

E's primary tasks this cycle:
  1. Validate TC-1 schema after B's migration (PRAGMA verification)
  2. Verify DL-207 URL shape fix (check live URL format from orchestrator)
  3. Attempt live collection with ScrapFly (SEED fallback if unavailable)
  4. Validate P2-1/P2-2 fixes from C060 still holding
  5. Report URL shape evidence from live logs (confirms/denies DL-207 fix)

====================================================================
PREFLIGHT
====================================================================

Task 1 (LARGE): Preflight checks.
  1a. git pull origin cycle/061/integration -- get B's latest commits
  1b. git log --oneline -8 -- confirm B commits and A commits are present
  1c. Read docs/cycle_reports/CYCLE_061_AGENT_A.md for cycle context
  1d. py -3.12 run.py config-check -- niches=9
  1e. Check .env for SCRAPFLY_API_KEY (prefix scp-, NOT via $env:, read from file):
      py -3.12 -c "from dotenv import load_dotenv; import os; load_dotenv(); key=os.getenv('SCRAPFLY_API_KEY',''); print('KEY_PRESENT:', bool(key), 'PREFIX:', key[:4] if key else 'N/A')"
  Record all outputs.

====================================================================
PART 1: TC-1 SCHEMA VALIDATION
====================================================================

Task 2 (XLARGE): Verify TC-1 schema after B's migration.
  2a. Wait for B to signal migration_11 is applied (check B's Jira comment or git log).
  2b. Run PRAGMA on foundation_gate_ci.db:
      py -3.12 -c "
      from sqlalchemy import create_engine, inspect
      e = create_engine('sqlite:///data/foundation_gate_ci.db')
      cols = sorted([c['name'] for c in inspect(e).get_columns('external_signals')])
      required = {'raw_value', 'relevance_score', 'trend_direction'}
      missing = required - set(cols)
      print('TC-1 COLUMNS:', [c for c in cols if c in required])
      print('MISSING:', missing if missing else 'NONE')
      "
  2c. Record result: TC-1 COLUMNS PRESENT or TC-1 COLUMNS MISSING.
  2d. If missing: record as gap in E report. Do NOT add the migration yourself.
      Note for Agent C: "TC-1 columns not yet in DB -- B migration may need verification."
  2e. If present: confirm ORM can instantiate ExternalSignal with new fields:
      py -3.12 -c "
      from src.models.external_signal import ExternalSignal
      es = ExternalSignal(keyword_id=1, signal_type='test', raw_value=0.5, relevance_score=0.8, trend_direction='RISING')
      print('TC-1 ORM instantiation: OK')
      print('raw_value:', es.raw_value, 'relevance_score:', es.relevance_score, 'trend_direction:', es.trend_direction)
      "

====================================================================
PART 2: DL-207 URL SHAPE VERIFICATION
====================================================================

Task 3 (XXLARGE): Verify DL-207 URL construction fix.
  3a. Check if B has committed the DL-207 fix: git log --oneline | head -10
  3b. Test URL construction directly:
      py -3.12 -c "
      from urllib.parse import quote
      test_keywords = ['python automation script', 'AI agent development', 'PRD template']
      for kw in test_keywords:
          encoded = quote(kw.strip(), safe='')
          url = f'https://www.fiverr.com/search/gigs?query={encoded}'
          assert 'search/gigs' in url, f'Missing search/gigs path: {url}'
          assert ' ' not in url, f'Unencoded space in URL: {url}'
          print(f'OK: {url}')
      print('DL-207 URL construction: PASS')
      "
  3c. Test orchestrator URL builder directly (if the fix is in orchestrator.py):
      py -3.12 -c "
      import sys; sys.path.insert(0,'.')
      # Try importing the fixed URL builder
      try:
          from src.collection.orchestrator import build_fiverr_search_url
          url = build_fiverr_search_url('python automation script')
          print('URL:', url)
          assert 'query=python%20automation%20script' in url or 'query=python+automation+script' in url
          print('DL-207 URL BUILDER: PASS')
      except ImportError:
          # If no standalone function, verify inline in orchestrator
          from src.collection import orchestrator
          import inspect
          src = inspect.getsource(orchestrator)
          if 'quote(' in src and 'search/gigs' in src:
              print('DL-207: quote() and search/gigs both present in orchestrator -- likely fixed')
          else:
              print('DL-207: WARNING -- check URL construction in orchestrator')
      "
  3d. If B has not yet committed DL-207 fix: record current URL construction behavior.
      Document in E report: "DL-207 fix status at time of E execution."

====================================================================
PART 3: SCRAPFLY LIVE VALIDATION (sec10.5 verbatim)
====================================================================

Task 4 (XLARGE): ScrapFly live collection runbook.
  STEP 1: Confirm key is in .env (Task 1e already done). Must have scp- prefix.
  STEP 2: Create throwaway config:
    Copy config.yaml to config.live_e2e.yaml (in .gitignore)
    Set enabled: true under collection.scrapfly in config.live_e2e.yaml
    NEVER commit config.live_e2e.yaml -- it must remain gitignored.
  STEP 3: Create throwaway DB:
    py -3.12 run.py seed-niches --database-url sqlite:///data/cycle061_e2e.db
    py -3.12 run.py run --mode collect-only --config-path config.live_e2e.yaml --database-url sqlite:///data/cycle061_e2e.db --niche-ids python_automation --dry-run false
    Look for ScrapFly log line: "ScrapFly session: requests=X credits=Y"
    That line = ScrapFly transport was used. LIVE data was fetched.
  STEP 4: URL shape capture -- look at logs for actual URLs sent to Fiverr.
    Check for: "https://www.fiverr.com/search/gigs?query=python%20automation" (correct)
    vs. "https://www.fiverr.com/Python automation" (DL-207 bare path form)
  STEP 5: Record RSV band from result_set_validations table:
    py -3.12 -c "
    from sqlalchemy import create_engine, text
    e = create_engine('sqlite:///data/cycle061_e2e.db')
    with e.begin() as conn:
        rows = conn.execute(text('SELECT COUNT(*), MIN(rsv_score), MAX(rsv_score), AVG(rsv_score) FROM result_set_validations')).fetchall()
        print('RSV rows:', rows)
    "
    RSV rows present = LIVE band. RSV rows absent = SEED band (no live collection).
  STEP 6: Delete config.live_e2e.yaml when done.
    Remove-Item config.live_e2e.yaml -Force -EA 0

SEED FALLBACK: If ScrapFly is unavailable (key missing, credits zero, 403):
  Record as "[SEED -- no live signal]" for affected niches.
  DO NOT fabricate counts. DO NOT silently 403-degrade.
  Note: "ScrapFly unavailable for [niche]: key_present=<bool>. RSV band: SEED."

Task 5 (LARGE): sec14.2 -- .env file authoritative source reminder.
  ALWAYS read API keys from .env using python-dotenv, NOT $env: system variable.
  py -3.12 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('DOTENV_LOADED')"
  Confirm the key loads via load_dotenv() before attempting live runs.

====================================================================
PART 4: C060 REGRESSION VALIDATION (P2-1, P2-2)
====================================================================

Task 6 (LARGE): Verify C060 Codex P2 fixes still hold.
  6a. P2-1 (ghost filter in relevance_dashboard.py):
      py -3.12 -m pytest -q tests/unit/ -k "ghost_filter_handles_null" --no-header
      Must pass. If not: record as regression gap for Agent B.
  6b. P2-2 (LLM alert query in alert_generator.py):
      py -3.12 -m pytest -q tests/unit/ -k "llm_alert_counts_actual" --no-header
      Must pass. If not: record as regression gap for Agent B.
  6c. Run targeted regression subset:
      py -3.12 -m pytest -q tests/unit/ -k "ghost or zombie or sponsored or llm_relevance" --no-header
      Record count.

====================================================================
PART 5: EXTERNAL SIGNALS SNAPSHOT
====================================================================

Task 7 (LARGE): Check external signals state in throwaway DB.
  7a. After live run: query external_signals table.
      py -3.12 -c "
      from sqlalchemy import create_engine, text
      e = create_engine('sqlite:///data/cycle061_e2e.db')
      with e.begin() as conn:
          rows = conn.execute(text('SELECT signal_type, COUNT(*) FROM external_signals GROUP BY signal_type')).fetchall()
          print('External signals by type:', rows)
          if not rows: print('WARNING: No external signals -- external_signals_enabled may be false')
      "
  7b. Check config.yaml: external_signals_enabled value.
      If false: note "external_signals disabled in committed config -- signals not populated (expected)."
      If B enabled it in P1: signals should be populated if TC-1 migration applied.
  7c. If TC-1 columns exist: check raw_value/relevance_score/trend_direction are populated.
      py -3.12 -c "
      from sqlalchemy import create_engine, text
      e = create_engine('sqlite:///data/cycle061_e2e.db')
      with e.begin() as conn:
          rows = conn.execute(text('SELECT raw_value, relevance_score, trend_direction FROM external_signals LIMIT 5')).fetchall()
          print('TC-1 field sample:', rows)
      "

====================================================================
PART 6: CONFIG GATE AND FINAL CHECKS
====================================================================

Task 8 (LARGE): Config gate verification.
  8a. Read committed config.yaml. Must show: collection.scrapfly.enabled = false.
      Get-Content config.yaml | Select-String "enabled|scrapfly"
      If scrapfly.enabled = true in committed file: CONFIG-GATE VIOLATION. Report to PM.
  8b. Verify throwaway DB was NOT used for baseline:
      py -3.12 -c "import os; print(os.path.exists('data/cycle037_live.db'))"
      Must be True (file exists and unchanged -- E never touched it).

Task 9 (LARGE): E zone final verification.
  9a. Get E's own commit SHA: git log --oneline -5 (find E's doc commit)
  9b. git show --name-only <E_SHA>
      Must contain ONLY: docs/cycle_reports/CYCLE_061_AGENT_E.md
      Any src/ = ZONE VIOLATION. Do NOT proceed. Report to PM immediately.
  9c. If zone is clean: record E SHA in report.

====================================================================
PART 7: WRITE E REPORT
====================================================================

Task 10 (XLARGE): Create CYCLE_061_AGENT_E.md with all sections.
  REQUIRED sections (all substantive content, no padding):
  ## Preflight (outputs from Task 1)
  ## TC-1 Schema Validation (PRAGMA output, ORM test)
  ## DL-207 URL Verification (test outputs, fix status, live log evidence if available)
  ## ScrapFly Setup (config created, key status, ScrapFly session line if present)
  ## Live Collection Attempt (command run, exit code, any errors)
  ## URL Shape Evidence (actual URLs from logs -- correct or bare path form)
  ## RSV Band (LIVE or SEED, count from result_set_validations)
  ## External Signals Snapshot (signal types, TC-1 column values if populated)
  ## P2 Regression Validation (P2-1 and P2-2 test results)
  ## Config Gate (scrapfly.enabled=false confirmed in committed config)
  ## Zone Verification (E SHA, files in commit -- only E report)
  ## Cleanup (config.live_e2e.yaml deleted, throwaway DB noted)
  ## Completion Checklist
  ## Agent C Signal ("E complete. C may proceed after B also signals ready.")

EACH SECTION must contain actual command output, not summary placeholders.
Fill with real data: actual PRAGMA output, real RSV counts, real URL shapes, real test results.

====================================================================
COMPLETION STANDARD
====================================================================

[ ] TC-1 PRAGMA: columns verified present (or gap documented)
[ ] DL-207: URL construction verified (correct format or bug documented)
[ ] ScrapFly: live run attempted (LIVE or SEED documented with evidence)
[ ] URL shape: actual URLs from live logs captured
[ ] RSV band: LIVE or SEED noted with row count
[ ] P2-1 and P2-2: tests pass or regression noted
[ ] External signals snapshot in report
[ ] Config gate: scrapfly.enabled=false in committed config
[ ] Zone: E commit contains ONLY E report file
[ ] config.live_e2e.yaml deleted after run
[ ] throwaway DB noted (data/cycle061_e2e.db -- NOT cycle037_live.db)
[ ] CYCLE_061_AGENT_E.md committed and pushed
[ ] NO pad lines ("floor-line-NNN" style lines are PROHIBITED)
[ ] Signal: "E complete. C may proceed after B also signals ready."

====================================================================
REGRESSION PACK (sec7 v2.4 -- 41 names -- E runs selected subset)
====================================================================

Run E's targeted subset (SRDI integrity regressions):
py -3.12 -m pytest -q tests/unit/ -k "ghost_filter_handles_null OR llm_alert_counts_actual OR stealth_sponsored OR first_recommendation_quality OR eligibility_ghost OR ghost_market_excluded OR ghost_discovery_recorded OR feedback_excludes OR low_specificity" --no-header

Full 41-name pack (for E reference -- C and D run the full pack):
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
ADDITIONAL TASKS 11-25
====================================================================

Task 11 (LARGE): Validate dashboard pages no longer import build_dashboard_demo_data.
  If B has committed dashboard wiring: Get-ChildItem src\dashboard\pages\ | ForEach-Object { Get-Content $_.FullName | Select-String "build_dashboard_demo_data" }
  Expected after B's work: empty. If any match found: record as partial completion in E report.
  Note: E cannot fix this. Record and continue.

Task 12 (LARGE): Capture live collection logs (URL shapes).
  During the live run (Task 4): capture stdout to a temp file.
  py -3.12 run.py run --mode collect-only ... 2>&1 | Tee-Object -FilePath e_live_run.txt
  Search for URL patterns: Select-String "fiverr.com" e_live_run.txt | Head -20
  Extract the actual URL format. Record in E report:
    "Live URLs observed: https://www.fiverr.com/search/gigs?query=... (CORRECT)" or
    "Live URLs observed: https://www.fiverr.com/Python automation script (BARE PATH -- DL-207 not fixed)"
  Delete e_live_run.txt when done: Remove-Item e_live_run.txt -Force -EA 0

Task 13 (LARGE): Check collection speed and timing.
  From live run output: note time per stage, any 403 errors, any timeouts.
  If 403s appear with ScrapFly: ScrapFly is not working (config issue, key issue, or credits exhausted).
  Record: "Stage X completed in Ys. Stage Y returned 403 (N times). ScrapFly: active/inactive."

Task 14 (LARGE): Check RSV distribution from throwaway DB.
  After live run completes: analyze RSV quality:
  py -3.12 -c "
  from sqlalchemy import create_engine, text
  e = create_engine('sqlite:///data/cycle061_e2e.db')
  with e.begin() as conn:
      r = conn.execute(text('SELECT COUNT(*) as total, SUM(CASE WHEN rsv_score >= 0.78 THEN 1 ELSE 0 END) as above_target FROM result_set_validations')).fetchone()
      print(f'RSV: total={r[0]}, above_0.78={r[1]}, rate={r[1]/r[0]:.1%}' if r[0] else 'RSV: no rows')
  "
  Target: avg_relevance > 0.78 per SRDI success KPIs.

Task 15 (LARGE): Check keyword count in throwaway DB.
  py -3.12 -c "
  from sqlalchemy import create_engine, text
  e = create_engine('sqlite:///data/cycle061_e2e.db')
  with e.begin() as conn:
      kw = conn.execute(text('SELECT COUNT(*) FROM keywords')).scalar()
      gigs = conn.execute(text('SELECT COUNT(*) FROM gigs')).scalar()
      print(f'keywords={kw}, gigs={gigs}')
  "
  If kw=0 or gigs=0: SEED band. Record.

Task 16 (LARGE): Verify E doesn't accidentally have src/ in staged files.
  git diff --cached --name-only 2>&1
  Must return empty (E has no staged changes) OR only show CYCLE_061_AGENT_E.md.
  Any src/ file in staged set: E has committed src/ -- ZONE VIOLATION -- stop immediately.

Task 17 (LARGE): Verify throwaway DB was not the baseline DB.
  py -3.12 -c "
  import os
  mtime = os.path.getmtime('data/cycle037_live.db')
  print(f'Baseline DB mtime: {mtime}')
  # Expected: 1780279258.7126791 (from C060 verification)
  assert abs(mtime - 1780279258.7) < 1.0, f'BASELINE MODIFIED: {mtime}'
  print('Baseline DB: UNTOUCHED -- correct')
  "

Task 18 (LARGE): Run full smoke test in dry-run mode.
  py -3.12 run.py run --mode collect-only --dry-run true --database-url sqlite:///data/cycle061_e2e.db
  Must pass without error. Record exit code and output.

Task 19 (LARGE): Check config.yaml for any violations.
  py -3.12 -c "
  import yaml
  with open('config.yaml') as f: cfg = yaml.safe_load(f)
  scrapfly = cfg.get('collection',{}).get('scrapfly',{}).get('enabled',False)
  ext_sig = cfg.get('analysis',{}).get('external_signals_enabled', False)
  llm = cfg.get('relevance',{}).get('llm_relevance_enabled', False)
  print(f'scrapfly.enabled={scrapfly} (must be false)')
  print(f'external_signals_enabled={ext_sig}')
  print(f'llm_relevance_enabled={llm}')
  assert not scrapfly, 'CONFIG GATE VIOLATION: scrapfly.enabled is true in committed config'
  print('Config gate: PASS')
  "

Task 20 (LARGE): Document findings in structured format.
  For each of E's validation areas, produce a structured finding:
  | Area | Command | Result | Status | Notes |
  | TC-1 PRAGMA | py -3.12 -c "..." | [actual output] | PASS/FAIL/GAP | |
  | DL-207 URL | py -3.12 -c "..." | [actual URL] | CORRECT/BARE-PATH | |
  | ScrapFly live | run.py run --config-path... | LIVE/SEED/ERROR | | |
  | RSV band | sqlite query | [count/score] | LIVE/SEED | |
  | P2-1 ghost filter | pytest -k ghost_filter | [count] passed | PASS/FAIL | |
  | P2-2 LLM alert | pytest -k llm_alert_counts | [count] passed | PASS/FAIL | |
  Include this table in E report.

Task 21 (LARGE): Commit E report.
  git add docs/cycle_reports/CYCLE_061_AGENT_E.md
  git commit -m "docs(cycle061): Agent E live validation -- TC-1 schema, DL-207 URL, live collection"
  git push origin cycle/061/integration
  Record E commit SHA.

Task 22 (LARGE): Final cleanup.
  Remove-Item config.live_e2e.yaml -Force -EA 0
  Remove-Item e_live_run.txt -Force -EA 0
  Confirm: git status --short shows only CYCLE_061_AGENT_E.md if anything.

Task 23 (LARGE): Update Jira control task.
  Comment: "E complete. SHA: <E_SHA>. TC-1 PRAGMA: <PASS/GAP>.
  DL-207 URL: <CORRECT/BARE-PATH/NOT-YET-FIXED>. Live run: <LIVE/SEED>.
  RSV band: <LIVE/SEED>. P2-1: <PASS>. P2-2: <PASS>. C may proceed after B also signals."

Task 24 (LARGE): Record all tool versions used.
  py -3.12 --version
  py -3.12 -c "import sqlalchemy; print('SQLAlchemy:', sqlalchemy.__version__)"
  py -3.12 -c "import streamlit; print('Streamlit:', streamlit.__version__)"
  Record in E report under "Environment."

Task 25 (LARGE): Final E checklist.
  [ ] TC-1 PRAGMA: 3 columns verified present (or gap documented)
  [ ] DL-207: URL verified correct or bug documented
  [ ] ScrapFly: live attempted; LIVE or SEED documented with evidence
  [ ] URL shape: actual log output captured
  [ ] RSV band: row count documented
  [ ] P2-1 and P2-2: test results documented
  [ ] External signals snapshot: signal types and TC-1 fields captured
  [ ] Config gate: scrapfly.enabled=false confirmed
  [ ] Dashboard demo-data check: result documented
  [ ] Zone: E commit has ONLY docs/cycle_reports/CYCLE_061_AGENT_E.md
  [ ] config.live_e2e.yaml deleted after run
  [ ] CYCLE_061_AGENT_E.md committed and pushed (NO pad lines)
  [ ] Signal sent to C: "E complete"

END OF PROMPT

====================================================================
ADDITIONAL TASKS 26-40 (E expansion)
====================================================================

Task 26 (LARGE): Verify collection queue processes URLs correctly.
  26a. From throwaway DB after live run: check gig_url formats in gigs table:
       py -3.12 -c "
       from sqlalchemy import create_engine, text
       e = create_engine('sqlite:///data/cycle061_e2e.db')
       with e.begin() as conn:
           rows = conn.execute(text('SELECT gig_url FROM gigs LIMIT 5')).fetchall()
           for r in rows: print(r[0])
       "
  26b. Expected: "https://www.fiverr.com/[username]/..." (gig page URLs)
  26c. NOT expected: bare path forms or collection search URLs.
  26d. Record URL format sample in E report.

Task 27 (LARGE): Verify ExternalSignal model after TC-1.
  27a. If TC-1 columns are present: verify backward-compat aliases still work.
       py -3.12 -c "
       from src.models.external_signal import ExternalSignal
       es = ExternalSignal(keyword_id=1, signal_type='test', signal_value=0.5)
       # Backward compat aliases should still work
       print('normalized_value:', es.normalized_value)
       print('raw_value_json:', es.raw_value_json)
       print('TC-1 new fields: raw_value:', es.raw_value)
       print('TC-1 new fields: relevance_score:', es.relevance_score)
       print('TC-1 new fields: trend_direction:', es.trend_direction)
       print('Backward compat: PASS')
       "
  27b. If any AttributeError: TC-1 implementation has a bug. Record as gap.

Task 28 (LARGE): Check LLM usage in throwaway DB.
  28a. After live run: check if LLM calls were made (LLM is only called if relevance is enabled).
       py -3.12 -c "
       from sqlalchemy import create_engine, text
       e = create_engine('sqlite:///data/cycle061_e2e.db')
       with e.begin() as conn:
           # Check if llm_calls or similar table exists
           tables = conn.execute(text(\"SELECT name FROM sqlite_master WHERE type='table'\")).fetchall()
           print('Tables in DB:', [t[0] for t in tables])
       "
  28b. If no LLM tables: LLM not invoked (expected -- llm_relevance_enabled=false).
  28c. Record LLM state in E report.

Task 29 (LARGE): Check dead letter queue state.
  29a. After live run: check dead_letter_jobs table.
       py -3.12 -c "
       from sqlalchemy import create_engine, text
       e = create_engine('sqlite:///data/cycle061_e2e.db')
       with e.begin() as conn:
           try:
               rows = conn.execute(text('SELECT job_type, error_message FROM dead_letter_jobs LIMIT 5')).fetchall()
               print('Dead letters:', rows if rows else 'NONE')
           except Exception as exc:
               print('DLQ check:', exc)
       "
  29b. If dead letters present: record job_type and error_message in E report.

Task 30 (LARGE): Test ScrapFly fallback behavior.
  30a. If ScrapFly is unavailable (key missing or credits = 0):
       Confirm system falls back gracefully to SEED mode (not a crash, not a hang).
  30b. Run without ScrapFly and confirm pipeline completes with SEED band:
       py -3.12 run.py run --mode collect-only --database-url sqlite:///data/cycle061_e2e.db --niche-ids python_automation 2>&1 | head -30
  30c. Look for: "SEED" indicator or log line confirming fallback behavior.
  Record: whether fallback to SEED is graceful or crashes.

Task 31 (LARGE): Document collection stage timing.
  31a. From live run output: record how long each stage took.
       Look for lines like: "Stage X complete in Y seconds"
  31b. Calculate: which stages are slowest? Any stage timing anomalies?
  31c. Record in E report under "Collection Timing."

Task 32 (LARGE): Verify niche configuration integrity.
  32a. After live run: confirm all 9 niche_ids are present in DB:
       py -3.12 -c "
       from sqlalchemy import create_engine, text
       e = create_engine('sqlite:///data/cycle061_e2e.db')
       with e.begin() as conn:
           rows = conn.execute(text('SELECT niche_id, COUNT(*) FROM keywords GROUP BY niche_id')).fetchall()
           print('Keywords per niche:', rows)
       "
  32b. Expected: niches that were seeded should have keywords.
  32c. Record: which niches have data vs. which are empty.

Task 33 (LARGE): Check config.live_e2e.yaml was not committed.
  33a. git status --short config.live_e2e.yaml
       Must show no tracked file.
  33b. git log --oneline --all -- config.live_e2e.yaml
       Must return empty (never committed).
  33c. If it appears in git history: THIS IS A PROBLEM. ScrapFly key may be exposed.
       Report to PM immediately.

Task 34 (LARGE): Verify throwaway DB is gitignored.
  34a. cat .gitignore | Select-String "cycle061_e2e\|e2e.*db\|data/\*.db"
  34b. Confirm cycle061_e2e.db would be gitignored.
  34c. git status --short data/cycle061_e2e.db
       Must show "??" (untracked, not "M" or "A").

Task 35 (LARGE): Final summary table for E report.
  Build and include in CYCLE_061_AGENT_E.md:
  | Validation | Command | Result | Status |
  |-----------|---------|--------|--------|
  | TC-1 PRAGMA | py -3.12 -c "..." | [raw_value present=T/F] | PASS/GAP |
  | DL-207 URL format | py -3.12 -c "..." | [URL sample] | CORRECT/BARE |
  | ScrapFly session | run.py run ... | LIVE/SEED/ERROR | [status] |
  | URL shape in logs | grep fiverr.com | [URL sample] | CORRECT/BARE |
  | RSV band | sqlite query | [count/score] | LIVE/SEED |
  | P2-1 ghost filter | pytest -k ghost_filter_handles | [N] passed | PASS/FAIL |
  | P2-2 LLM alert | pytest -k llm_alert_counts | [N] passed | PASS/FAIL |
  | Config gate | grep scrapfly | enabled=false | PASS/FAIL |
  | DLQ check | sqlite query | [count] dead letters | OK/WARN |
  | Dashboard demo-data | Get-ChildItem pages/ | [0 or N matches] | PASS/GAP |
  | E zone | git show --name-only | only E report | PASS/FAIL |
  | config.live_e2e.yaml | git status | untracked/absent | CLEAN/LEAK |
  This table is the core of the E report.

====================================================================
E KNOWN FAILURE MODES
====================================================================

1. E accidentally adds a src/ file to "fix" an import error.
   Guard: E's zone is docs/cycle_reports/CYCLE_061_AGENT_E.md ONLY.
   If any src/ file appears: stop, undo, document the gap for B.

2. E uses $env:SCRAPFLY_API_KEY instead of python-dotenv.
   Guard: always use load_dotenv() + os.getenv('SCRAPFLY_API_KEY').
   $env: may be empty even when .env contains the key.

3. E commits config.live_e2e.yaml.
   Guard: git status --short after every commit. config.live_e2e.yaml must be absent.
   If accidentally staged: git reset HEAD config.live_e2e.yaml before committing.

4. E uses data/cycle037_live.db instead of throwaway DB.
   Guard: always specify --database-url sqlite:///data/cycle061_e2e.db explicitly.
   NEVER run without --database-url on live mode.

5. E pads report to meet 500-line floor.
   Guard: every line must be substantive project content.
   If report is under 500 lines: add more actual findings, not filler.
