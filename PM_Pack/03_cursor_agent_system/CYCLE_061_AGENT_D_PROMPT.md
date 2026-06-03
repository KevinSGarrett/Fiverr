# CYCLE 061 -- AGENT D PROMPT
# Role: Merge gate, coverage, post-merge cleanup
# Stage: 5 (final -- after ALL of A, B, E, C, F complete)
# Base SHA: 9687fb6f38ebca8b01cefa845630ea4f2b609c07
# Branch: cycle/061/integration

====================================================================
PREREQUISITES (all must be satisfied before D starts)
====================================================================

D runs AFTER all 5 agents: A, B, E, C, F.
Verify: 5 report files exist:
  docs/cycle_reports/CYCLE_061_AGENT_A.md
  docs/cycle_reports/CYCLE_061_AGENT_B.md
  docs/cycle_reports/CYCLE_061_AGENT_E.md
  docs/cycle_reports/CYCLE_061_AGENT_C.md
  docs/cycle_reports/CYCLE_061_AGENT_F.md
If ANY is missing: STOP. Contact PM.

====================================================================
PROJECT CONTEXT
====================================================================

Working dir: C:\Fiverr\Fiverr | Python: py -3.12
GitHub: KevinSGarrett/Fiverr | Connector auth (NEVER paste tokens)
Jira: eae77257-a572-4e19-b746-8b184ba2d01f | Connector auth

====================================================================
PART 1: PREFLIGHT
====================================================================

Task 1 (LARGE): State verification.
  1a. git pull origin cycle/061/integration
  1b. git log --oneline -10 -- confirm A, B, E, C, F commits present
  1c. Read ALL 5 agent reports. Build deliverables table:
      | Agent | SHA | Files Claimed | Verified? |
      | A | <sha> | cycle_reports/A.md + PM_Pack/ | |
      | B | <sha> | src/ + tests/ + cycle_reports/B.md | |
      | E | <sha> | cycle_reports/E.md only | |
      | C | <sha> | cycle_reports/C.md only | |
      | F | <sha> | tests/ + cycle_reports/F.md | |
  1d. py -3.12 run.py config-check -- niches=9
  Record all outputs.

====================================================================
PART 2: G1 -- COMPREHENSIVE COMMIT ATTRIBUTION GATE
====================================================================

Task 2 (XXXLARGE): G1 -- enumerate ALL cycle commits and verify each agent's zone.
  THIS IS THE CRITICAL PROCESS FIX FROM C060.
  D must enumerate ALL commits in the cycle range, NOT just SHAs from C's report.

  2a. Get base SHA:
      base_sha=$(Invoke-Exe git 'merge-base origin/develop HEAD').Out
  2b. List ALL commits:
      Invoke-Exe git "log --oneline $base_sha..HEAD"
      Record EVERY SHA.
  2c. For EACH SHA in the list:
      Invoke-Exe git "show --name-only <SHA>"
      Categorize files as: src/ | tests/ | docs/ | PM_Pack/ | config/ | other
  2d. Build attribution table:
      | SHA | Short desc | Agent | Files | Zone OK? |
      | <sha> | docs(cycle061): Agent A plan | A | docs/AGENT_A.md PM_Pack/... | YES |
      | <sha> | feat(hardening): TC-1 + DL-207... | B | src/ tests/ docs/AGENT_B.md | YES |
      | <sha> | docs(cycle061): Agent E live validation | E | docs/AGENT_E.md | YES |
      | <sha> | docs(cycle061): Agent C integration | C | docs/AGENT_C.md | YES |
      | <sha> | test(hardening): F coverage | F | tests/ docs/AGENT_F.md | YES |
  2e. Zone rules:
      A commits: ONLY docs/cycle_reports/ + PM_Pack/ + NO src/
      B commits: ONLY src/ + tests/ + docs/cycle_reports/CYCLE_061_AGENT_B.md
      E commits: ONLY docs/cycle_reports/CYCLE_061_AGENT_E.md
      C commits: ONLY docs/cycle_reports/CYCLE_061_AGENT_C.md
      F commits: ONLY tests/ + docs/cycle_reports/CYCLE_061_AGENT_F.md
  2f. If ANY src/ file appears in A, E, C, or F commits: BLOCKING ZONE VIOLATION.
      Do NOT merge. Contact PM. Surface the violating SHA and file path.
  2g. If ALL zones are clean: record "G1 ZONE CHECK: ALL PASS" in D report.

====================================================================
PART 3: SEC12.3 OPERATIONAL PLAYBOOK (MANDATORY -- VERBATIM)
====================================================================

Task 3 (XXLARGE): Handle all operational merge-gate issues per sec12.3.

  ISSUE A: PR is too large (>1000 lines changed).
    Action: Apply override:large-pr label.
    Command:
      Invoke-Exe gh "api -X POST repos/KevinSGarrett/Fiverr/issues/<PR_NUM>/labels --field 'labels[]=override:large-pr'"
    Then proceed with merge (label overrides the size gate).
    Document in D report: "PR size: <N> lines. override:large-pr applied."

  ISSUE B: Codex GraphQL thread resolution.
    Required: D must run Codex query TWICE (pre-resolve and post-resolve).
    Command pattern (write query to file first, then execute):
      [System.IO.File]::WriteAllText('codex_query.graphql', 'query{repository(owner:"KevinSGarrett",name:"Fiverr"){pullRequest(number:<PR_NUM>){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:3){nodes{author{login}body}}}}}}}')
      Invoke-Exe gh "api graphql -F query=@codex_query.graphql"
    Pre-resolve: record total threads, resolved count, unresolved count.
    For EACH unresolved thread: read the content. Implement a REAL FIX (not just a "resolved" click).
    Post-resolve: rerun the query. Must show 0 unresolved.
    If 0 unresolved after fix: G-002 satisfied.
    Document both raw JSON outputs in D report.

  ISSUE C: codecov/patch below threshold.
    codecov/patch is ADVISORY -- it is NOT a blocking gate.
    D checks: did coverage/project (>=90%) pass?
      If coverage/project PASS and codecov/patch FAIL: document and proceed. Not a blocker.
      If coverage/project FAIL: BLOCKING. Do NOT merge. Route to B.
    Document in D report: "codecov/patch: PASS/FAIL (advisory). coverage/project: PASS/FAIL."

  ISSUE D: mergeable_state values.
    clean: proceed normally.
    unstable: check CI status. If only advisory checks are failing: proceed + document.
    blocked: STOP. There is a hard blocking check. Do NOT merge. Investigate.
    unknown: wait 30 seconds. Re-query. If still unknown after 3 retries: escalate to PM.
    Command to check:
      Invoke-Exe gh "pr view <PR_NUM> --json mergeable,statusCheckRollup,state"
    Record: mergeable_state value and CI check results.

  ISSUE E: CI still pending.
    Wait up to 5 minutes, checking every 60 seconds.
    Command: Invoke-Exe gh "pr view <PR_NUM> --json statusCheckRollup"
    If still pending after 5 minutes: escalate to PM. Do NOT merge.

====================================================================
PART 4: TC-1 INDEPENDENT VERIFICATION
====================================================================

Task 4 (LARGE): TC-1 PRAGMA -- D re-runs independently (does NOT trust B or C reports).
  py -3.12 -c "
  from sqlalchemy import create_engine, inspect
  e = create_engine('sqlite:///data/foundation_gate_ci.db')
  cols = sorted([c['name'] for c in inspect(e).get_columns('external_signals')])
  required = {'raw_value', 'relevance_score', 'trend_direction'}
  missing = required - set(cols)
  print('D TC-1 PRAGMA:', 'PASS' if not missing else f'FAIL: {missing}')
  print('All columns:', cols)
  "
  If any column missing: DO NOT MERGE. Route to B.

====================================================================
PART 5: DASHBOARD DEMO-DATA FINAL CHECK
====================================================================

Task 5 (LARGE): Dashboard demo-data independent check -- D re-verifies.
  Get-ChildItem src\dashboard\pages\ | ForEach-Object {
      $match = Get-Content $_.FullName | Select-String "build_dashboard_demo_data"
      if($match){ Write-Host "DEMO_DATA_FOUND: $($_.Name)" }
  }
  If ANY match: DO NOT MERGE. Route to B.
  If empty: record "DASHBOARD DEMO-DATA CHECK: PASS"

====================================================================
PART 6: MERGE GATE VERIFICATION (G1-G10)
====================================================================

Task 6 (XLARGE): Full merge gate checklist.
  G1 (Attribution): completed in Task 2. Status: PASS/FAIL.

  G2 (Codex x2):
    Pre-resolve Codex query: record thread count.
    Implement real fixes for unresolved threads.
    Post-resolve Codex query: confirm 0 unresolved.

  G3 (All CI PASS):
    Invoke-Exe gh "pr view <PR_NUM> --json statusCheckRollup"
    All CI checks must show SUCCESS (except advisory ones per G-001).

  G4 (ONE --cov=src run):
    D runs the single authorized coverage run:
    py -3.12 -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90 --no-header 2>&1 | tail -20
    Record: total %, covered lines, uncovered lines. Must be >=90%.
    This is the ONLY --cov=src run in the cycle.

  G5 (Golden parity):
    py -3.12 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override analysis.external_signals_enabled=false
    kw=110 = 62.7/1.0/CONDITIONAL_GO. kw=96 = 35.8. kw=3 = 56.66.
    Any deviation: BLOCKING. Do NOT merge.

  G6 (Regression pack ALL 41 PASS):
    Run all 41 by exact name (see pack below).
    88+ passed. 0 failed. Plus new C061 tests on top.

  G7 (Ruff + mypy):
    py -3.12 -m ruff check . -- PASS
    py -3.12 -m mypy src -- PASS

  G8 (Config gate):
    Get-Content config.yaml | Select-String "scrapfly"
    scrapfly.enabled must be false. If true: BLOCKING.

  G9 (TC-1 sec11 PRAGMA): covered in Task 4. Status: PASS/FAIL.

  G10 (Dashboard no demo-data): covered in Task 5. Status: PASS/FAIL.

  All 10 gates must PASS before D squash-merges.

====================================================================
PART 7: SQUASH MERGE
====================================================================

Task 7 (LARGE): Verify PR is ready to merge.
  7a. Invoke-Exe gh "pr view <PR_NUM> --json state,mergeable,statusCheckRollup,reviews"
  7b. All gates must be PASS.
  7c. mergeable_state must be "clean" or "unstable" (with only advisory failures).
  7d. Record PR number, PR title, PR SHA.

Task 8 (XXLARGE): Squash merge.
  8a. Apply override:large-pr label (C061 is expected to be large):
      Invoke-Exe gh "api -X POST repos/KevinSGarrett/Fiverr/issues/<PR_NUM>/labels --field 'labels[]=override:large-pr'"
  8b. Squash merge:
      Invoke-Exe gh "pr merge <PR_NUM> --squash --merge-message 'feat(hardening): Post-SRDI Production Hardening -- TC-1 ExternalSignal schema, DL-207 URL fix, dashboard live-data wiring (#<PR_NUM>)'"
  8c. Verify merge:
      Invoke-Exe git "log origin/develop --oneline -3"
      New develop HEAD must be the C061 squash commit.
  8d. Record final develop SHA.

====================================================================
PART 8: POST-MERGE TASKS
====================================================================

Task 9 (LARGE): Update sec7 regression pack if new regressions added.
  9a. Read F report for REG-41+ candidates.
  9b. If F proposed new regressions:
      Read strategy doc sec7 section.
      Add new test names after REG-40.
      Bump pack count (41 -> N).
      Add version history row: "v2.5: C061 added REG-41 through REG-N (TC-1 + DL-207 + dashboard)"
  9c. If no new regressions: leave sec7 at v2.4 / 41 names.

Task 10 (LARGE): Delete cycle branch.
  Invoke-Exe gh "api -X DELETE repos/KevinSGarrett/Fiverr/git/refs/heads/cycle/061/integration"
  Verify: Invoke-Exe git "branch -r | grep cycle/061"
  Must return empty.

Task 11 (LARGE): Jira post-merge plan.
  11a. Via Atlassian connector: transition ALL C061 stories to Done (id 41).
       - TC-1 story: Done with comment "TC-1 implemented. migration_11 applied. PRAGMA PASS."
       - DL-207 story: Done with comment "URL encoding fixed. Tests pass."
       - Dashboard story: Done with comment "9 pages live-data wired. Empty-DB graceful."
       - Artifacts story: Done with comment "11/12/13 placeholder docs committed."
  11b. Transition C061 control task to Done.
  11c. Post final comment on control task: "C061 complete. Squash SHA: <SHA>. develop: <SHA>."

Task 12 (LARGE): Update hydration header.
  Read PM_Pack\07_hydration\HYDRATION_HEADER.md.
  Update:
    CYCLE_CURRENT = 062
    CYCLE_DONE = 061
    Latest squash SHA = <C061_SQUASH_SHA>
    Suite: <count> passed (from G4 --cov=src run)
    Coverage: <coverage>%
    G-B gate: CLOSED (TC-1 ExternalSignal schema complete)
    G-C gate: CLOSED (dashboard live-data wiring complete)
  Commit: git add PM_Pack\07_hydration\HYDRATION_HEADER.md && git commit -m "chore(governance): C061 post-merge hydration update" && git push origin develop

Task 13 (LARGE): Update EPIC_STATUS_TRACKER.
  Update PM_Pack\08_task_queue\EPIC_STATUS_TRACKER.md:
    C061 scope row: MERGED | <C061_SQUASH_SHA>
    G-B: CLOSED
    G-C: CLOSED
    G-A: PARTIAL (launch artifacts placeholders created)
    Next cycle (C062): Wave 9 Pricing Strategy Engine start; G-D initiative
  Commit with hydration header.

Task 14 (LARGE): Create CYCLE_061_PM_REVIEW seed entries.
  Create: PM_Pack\10_cycle_log\CYCLE_061_PM_REVIEW.md
  Seed content:
    ## Cycle 061 PM Review Checklist Status
    G-B gate: CLOSED (TC-1 ExternalSignal schema -- migration_11 applied, PRAGMA verified)
    G-C gate: CLOSED (dashboard live-data wiring -- all 9 pages use real SQLAlchemy)
    G-A gate: PARTIAL (launch artifacts 11/12/13 are placeholders, not full docs)
    G-D gate: OPEN (Waves 9-12 still unstarted -- C062 will scope Wave 9 Pricing)
    New §7 pack: REG-41 through REG-N (see D report)
    sec13.10 check: all 14 tracks reviewed -- track status table in A report

Task 15 (LARGE): Create CYCLE_061_AGENT_D.md report.
  Contents:
  ## Preflight (5 agents' reports read)
  ## G1 Attribution (complete table of all cycle commits with zone verdict)
  ## sec12.3 Operational (PR size, Codex x2 JSON outputs, codecov/patch, mergeable_state)
  ## TC-1 PRAGMA Independent (D's own PRAGMA run, not trusting B or C)
  ## Dashboard Demo-Data (D's own check)
  ## Gates G2-G10 (each gate with result)
  ## G4 --cov=src run (only run -- coverage %, missing lines)
  ## Golden Parity (kw=110 value)
  ## Regression Pack (count, any new tests, proposed REG-41+ names)
  ## Merge Executed (PR num, squash SHA, new develop HEAD)
  ## Post-Merge (branch deleted, Jira, hydration, tracker updated)
  ## sec7 Update (if new regressions added)

====================================================================
ADDITIONAL TASKS 16-25
====================================================================

Task 16 (LARGE): Verify no worktrees were left.
  git worktree list -- must show exactly ONE worktree at C:\Fiverr\Fiverr.
  If extra worktrees: git worktree remove --force <path> for each stale one.

Task 17 (LARGE): Verify no stale GitHHub branches from this cycle.
  Invoke-Exe git "branch -r | grep cycle/061"
  After merge and delete: must be empty.
  If cycle/061/integration still exists: delete it.

Task 18 (LARGE): Verify new develop HEAD matches squash commit.
  Invoke-Exe git "fetch origin"
  Invoke-Exe git "log origin/develop --oneline -3"
  First line must be the C061 squash commit.
  Record: C061 squash SHA.

Task 19 (LARGE): Run full suite on develop HEAD post-merge.
  git checkout develop && git pull
  py -3.12 -m pytest -q tests/unit/ --no-header 2>&1 | tail -5
  Must pass. This confirms merge didn't break anything.
  Record: post-merge test count.

Task 20 (LARGE): Check Jira backlog for any C061 stories not yet Done.
  Via Atlassian connector: query project = SCRUM AND status != Done AND summary ~ "C061"
  Any remaining open C061 story: transition it to Done with appropriate comment.

Task 21 (LARGE): Verify sec11.2 parity table will be in D report.
  D independently builds the parity confirmation:
  | Column | ORM type | Migration | DDL | Present in DB? |
  | raw_value | float | migration_11 | ADD COLUMN raw_value REAL | YES (verified by D PRAGMA) |
  | relevance_score | float | migration_11 | ADD COLUMN relevance_score REAL | YES |
  | trend_direction | str | migration_11 | ADD COLUMN trend_direction VARCHAR(16) | YES |
  Include this table in D report independent of B's report.

Task 22 (LARGE): DL-207 final verification.
  py -3.12 -c "
  from urllib.parse import quote
  kws = ['python automation script', 'AI agent development', 'PRD template']
  for kw in kws:
      enc = quote(kw, safe='')
      url = f'https://www.fiverr.com/search/gigs?query={enc}'
      assert ' ' not in url
      assert 'search/gigs' in url
  print('D DL-207 FINAL: PASS')
  "

Task 23 (LARGE): Record final production readiness gate status.
  Document in D report:
  G-A: PARTIAL (launch artifacts placeholders created; full docs = future Tier A)
  G-B: CLOSED (TC-1 ExternalSignal raw_value + relevance_score + trend_direction in DB)
  G-C: CLOSED (all 9 dashboard pages use real SQLAlchemy; no build_dashboard_demo_data)
  G-D: OPEN (Waves 9-12 unstarted; C062 will scope Wave 9 Pricing)

Task 24 (LARGE): Verify baseline DB untouched.
  py -3.12 -c "
  import os; mtime = os.path.getmtime('data/cycle037_live.db')
  print(f'Baseline mtime: {mtime}')
  assert abs(mtime - 1780279258.7) < 1.0, f'BASELINE MODIFIED: {mtime}'
  print('Baseline: UNTOUCHED')
  "
  If mtime changed: CRITICAL. Document and escalate to PM.

Task 25 (LARGE): Final D checklist.
  [ ] All 5 agent reports read; deliverables table built
  [ ] G1 attribution: ALL commits verified by zone (not just C's SHAs)
  [ ] TC-1 PRAGMA: D ran independently; all 3 columns confirmed
  [ ] Dashboard demo-data: D ran independently; zero matches
  [ ] Codex x2: pre+post JSON outputs in D report; 0 unresolved after fix
  [ ] PR size: override:large-pr applied
  [ ] G2 (Codex): PASS | G3 (CI): PASS | G4 (--cov=src): PASS >=90%
  [ ] G5 (golden): kw=110 = 62.7/1.0/CONDITIONAL_GO
  [ ] G6 (regression pack): 88+ passed | G7 (ruff+mypy): PASS
  [ ] G8 (config gate): scrapfly.enabled=false
  [ ] G9 (TC-1 PRAGMA): PASS | G10 (dashboard): PASS
  [ ] PR squash-merged; new develop HEAD recorded
  [ ] Cycle branch deleted
  [ ] Jira: all C061 stories Done + control task Done
  [ ] Hydration header updated (CYCLE_CURRENT=062, G-B and G-C CLOSED)
  [ ] EPIC_STATUS_TRACKER updated
  [ ] sec7 updated (if new regressions from F)
  [ ] CYCLE_061_PM_REVIEW.md seed created
  [ ] CYCLE_061_AGENT_D.md committed and pushed to develop
  [ ] Baseline DB mtime unchanged

====================================================================
REGRESSION PACK (sec7 v2.4 -- 41 names -- D runs ALL)
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

====================================================================
HARD GATE RULES (verbatim)
====================================================================

G-001 COVERAGE: Enforced = CI + codecov/project >=90%.
  codecov/patch ADVISORY. Document miss; proceed if project floor PASSED.
G-002: Codex TWICE. Pre-resolve + post-resolve. BOTH raw JSONs in D report.
  Real fix required for each thread, not just "resolved" click.
G-003: All merge gates PASS before squash.
G-004: EXACTLY ONE --cov=src by D only. No other agent runs --cov=src.
G-005: Golden: kw=110 = 62.7/1.0/CONDITIONAL_GO. kw=96=35.8. kw=3=56.66. Baseline UNTOUCHED.
G1 PROCESS FIX: enumerate ALL commits via git log, NOT just from C report.
BLOCKING: TC-1 PRAGMA missing column = NO-GO. Dashboard demo-data found = NO-GO.

END OF PROMPT

====================================================================
PART 9: COMPREHENSIVE CODEX GRAPHQL PROCEDURE (VERBATIM)
====================================================================

Task 26 (XXXLARGE): Codex GraphQL -- full procedure (G-002 requires 2 runs).

  PRE-RESOLVE RUN:
  Step 1: Write query to file (required -- gh api graphql cannot accept inline query reliably):
    [System.IO.File]::WriteAllText('codex_query.graphql', 'query{repository(owner:"KevinSGarrett",name:"Fiverr"){pullRequest(number:<PR_NUM>){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:3){nodes{author{login}body}}}}}}}',[System.Text.Encoding]::ASCII)

  Step 2: Run pre-resolve query:
    Invoke-Exe gh "api graphql -F query=@codex_query.graphql"
    Record: full JSON output in D report under "Codex Pre-Resolve JSON".
    Count total threads, resolved count, unresolved count.

  Step 3: For EACH unresolved thread:
    a) Read the thread content (author, body)
    b) Understand what the reviewer is asking
    c) Implement a REAL FIX in src/ (if code issue) or document why no change needed
    d) Mark the thread as resolved via GitHub UI or GraphQL mutation
    Do NOT just click "resolve" without addressing the underlying issue.

  POST-RESOLVE RUN:
  Step 4: Re-run the same query after fixes:
    Invoke-Exe gh "api graphql -F query=@codex_query.graphql"
    Record: full JSON output in D report under "Codex Post-Resolve JSON".
    Must show 0 unresolved threads.

  Step 5: Cleanup:
    Remove-Item codex_query.graphql -Force

  If post-resolve still shows unresolved threads: BLOCKING. Fix remaining threads before merging.

  GraphQL mutation to resolve a thread (if needed):
    [System.IO.File]::WriteAllText('resolve_mutation.graphql', 'mutation{resolveReviewThread(input:{threadId:"<THREAD_ID>"}){thread{id isResolved}}}', [System.Text.Encoding]::ASCII)
    Invoke-Exe gh "api graphql -F query=@resolve_mutation.graphql"

====================================================================
PART 10: --cov=src PROCEDURE (G-004 -- THE ONLY AUTHORIZED RUN)
====================================================================

Task 27 (XXLARGE): G4 -- single authorized --cov=src run.

  IMPORTANT: D is the ONLY agent authorized to run --cov=src in the entire cycle.
  If any other agent ran --cov=src: G-004 violation. Document it.

  D's coverage run:
    py -3.12 -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=90 --no-header tests/unit/ 2>&1 | Tee-Object -FilePath coverage_output.txt
    Wait for completion.

  Read coverage output:
    Get-Content coverage_output.txt | tail -40

  Extract and record in D report:
    Total coverage %: (look for "TOTAL" line)
    Individual module coverage for C061 deliverables:
      src/models/external_signal.py: should be >=85%
      src/collection/orchestrator.py: should be >=88%
      src/dashboard/pages/opportunities.py: should be >=75%
      (and other dashboard pages)
    Any module below 80%: note as coverage gap for C062 scope.

  Pass criteria:
    --cov-fail-under=90 means overall coverage must be >=90%
    If fails: BLOCKING. Route to F for additional tests or accept with PM approval.

  Cleanup:
    Remove-Item coverage_output.txt -Force -EA 0

====================================================================
PART 11: MERGE PROCEDURE AND PR VERIFICATION
====================================================================

Task 28 (XXLARGE): Full PR state verification before merge.

  28a. Get PR number (from A's report or commit messages):
       PR_NUM = <number from CYCLE_061_AGENT_A.md>

  28b. Verify PR state:
       Invoke-Exe gh "pr view $PR_NUM --json state,mergeable,statusCheckRollup,headRefName,baseRefName,additions,deletions"
       Record:
         state: must be OPEN (not already merged)
         mergeable: clean or unstable
         headRefName: must be cycle/061/integration
         baseRefName: must be develop
         additions+deletions: total line count (if >1000: override:large-pr needed)

  28c. Check each CI status:
       statusCheckRollup contains all CI checks.
       Required PASS: Lint + Typecheck + Tests + Gates CI
       Required PASS: codecov/project
       Advisory (OK to have FAIL): codecov/patch
       Record each check name and state.

  28d. If all required checks PASS: proceed to merge.

Task 29 (LARGE): Apply override:large-pr label proactively.
  C061 changes: TC-1 model + migration + dashboard wiring (9 pages) = likely >1000 lines.
  Apply the label regardless:
    Invoke-Exe gh "api -X POST repos/KevinSGarrett/Fiverr/issues/$PR_NUM/labels --field 'labels[]=override:large-pr'"
  Verify: label appears in PR labels.

Task 30 (LARGE): Execute squash merge with correct message format.
  merge_message = "feat(hardening): Post-SRDI Production Hardening -- TC-1 ExternalSignal schema + DL-207 URL fix + dashboard live-data wiring (#$PR_NUM)"

  Invoke-Exe gh "pr merge $PR_NUM --squash --merge-message '$merge_message'"

  If merge fails with "blocked":
    Check: is there a branch protection rule requiring admin review?
    If yes: need to temporarily relax protection (Tier D -- ask PM) or use admin merge.
    Do NOT force-push. Do NOT bypass protection without PM authorization.

  After successful merge: verify new develop HEAD:
    Invoke-Exe git "fetch origin"
    Invoke-Exe git "log origin/develop --oneline -3"
    First line must be the C061 squash commit.
    Record: C061 squash SHA (this replaces 9687fb6f38ebca8b01cefa845630ea4f2b609c07 in next cycle).

====================================================================
PART 12: SEC7 PACK UPDATE PROCEDURE
====================================================================

Task 31 (LARGE): Update sec7 regression pack based on F's proposed new tests.

  31a. Read docs/cycle_reports/CYCLE_061_AGENT_F.md -- find "New Regression Candidates" section.
  31b. For each proposed REG-41+:
       Verify it exists in tests/unit/ and passes:
         py -3.12 -m pytest -q tests/unit/ -k "<test_name>" --no-header
  31c. If test passes and is genuinely regression-worthy (failure would indicate real breakage):
       Add to strategy doc sec7 section after REG-40.
  31d. Update version to v2.5 (or next) with version history row.
  31e. Proposed additions (D decides final inclusion):
       REG-41: test_external_signal_raw_value_stored_and_retrieved
         Regression meaning: if TC-1 migration regresses, raw_value will be lost.
       REG-42: test_collection_url_encodes_spaces_correctly
         Regression meaning: if DL-207 fix regresses, spaces in URLs will break collection.
       REG-43: test_collection_url_never_bare_path
         Regression meaning: if DL-207 fix regresses, bare paths will be used.
       REG-44: test_dashboard_opportunities_renders_empty_db_gracefully
         Regression meaning: if demo-data wiring regresses, dashboard will crash on empty DB.

  If D includes all 4: pack becomes sec7 v2.5 / 45 names.
  If D excludes some: document rationale.

====================================================================
PART 13: D REPORT STRUCTURE
====================================================================

Task 32 (LARGE): CYCLE_061_AGENT_D.md must contain ALL of these sections.
  Required sections (every section must have real output, not placeholder text):

  ## 1. Preflight
     - All 5 agent reports: read and summarized
     - config-check: output recorded
     - git log -10: output recorded

  ## 2. G1 -- Comprehensive Commit Attribution
     - base SHA: <value>
     - ALL commit SHAs from git log (every one enumerated)
     - For EACH SHA: git show --name-only output
     - Attribution table: SHA | Agent | Files | Zone OK?
     - Verdict: ALL PASS or ZONE VIOLATION (specific SHA/file)

  ## 3. sec12.3 Operational Issues
     - PR size: <additions + deletions> lines; override:large-pr applied
     - Codex Pre-Resolve JSON: full JSON (not truncated)
     - Thread analysis: N threads, M resolved, K unresolved
     - Fixes applied: (list each fix or "no fixes needed")
     - Codex Post-Resolve JSON: full JSON
     - Final: 0 unresolved confirmed
     - codecov/patch: PASS/FAIL (advisory)
     - coverage/project: PASS/FAIL (gate)
     - mergeable_state: clean/unstable/blocked

  ## 4. TC-1 Independent PRAGMA
     - D's own PRAGMA output (full column list)
     - raw_value: PRESENT / ABSENT
     - relevance_score: PRESENT / ABSENT
     - trend_direction: PRESENT / ABSENT
     - D parity table: all YES or blocking failure

  ## 5. Dashboard Demo-Data Independent Check
     - Get-ChildItem command output
     - Result: CLEAN (0 matches) or FOUND (list matches)

  ## 6. Gates G2-G10
     - Each gate: command + result + PASS/FAIL

  ## 7. G4 --cov=src
     - Full coverage output (tail -40 of coverage.txt)
     - Total %: <value>
     - External_signal: <value>%
     - Orchestrator: <value>%
     - Dashboard pages: <value>% each

  ## 8. Golden Parity
     - Full run.py score --golden output
     - kw=110: <tag>/<modifier>/<confidence>

  ## 9. Regression Pack
     - Count: 88+ passed (or N if F added new tests)
     - Any failures: none or list

  ## 10. Merge
     - PR: #<num>
     - merge_message: <value>
     - Squash SHA: <C061_SQUASH_SHA>
     - New develop HEAD: <SHA>

  ## 11. Post-Merge
     - Branch deleted: YES
     - Jira stories: Done (list each key)
     - Hydration header: updated
     - EPIC_STATUS_TRACKER: updated
     - sec7: v2.5 with REG-41 through REG-N OR "no new regressions"
     - CYCLE_061_PM_REVIEW.md: created

  ## 12. Production Readiness Gates
     - G-A: PARTIAL | G-B: CLOSED | G-C: CLOSED | G-D: OPEN

====================================================================
ADDITIONAL TASKS 33-40
====================================================================

Task 33 (LARGE): Remove scratch files from PM_Pack (Tier A cleanup).
  The following scratch scripts were created during C061 planning and should be removed:
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\cnt.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\vc.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\find_pm.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\fix_eop.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\expand_b.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\fix2.ps1 -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\counts2.txt -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\fix_result.txt -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\find_pm.txt -Force -EA 0
  Remove-Item C:\Fiverr\Fiverr\PM_Pack\cnt.txt -Force -EA 0
  If any are absent: the -EA 0 prevents errors.

Task 34 (LARGE): Verify final develop HEAD is clean.
  After post-merge commits (hydration, tracker):
  git status --short -- must be clean
  git log origin/develop --oneline -5 -- confirm hydration commits on top

Task 35 (LARGE): Record C062 scope seed.
  In D report under "C062 Preview":
    P0: G-D initiation -- Wave 9 Pricing Strategy Engine start (PM_Pack/ref/project_plan/09_pricing/)
    P1: Enable external_signals_enabled if not done in C061
    P1: Close ~65 stale Jira board-setup issues (SCRUM-5 through ~SCRUM-72)
    P2: Close G-A fully -- expand 11/12/13 from placeholders to real documents
    Deferred: Wave 10-12 (Discovery, Playbook, UX)

Task 36 (LARGE): Verify no config.live_e2e.yaml on disk.
  Test-Path C:\Fiverr\Fiverr\config.live_e2e.yaml
  Must return False. If True: E left it behind. Remove immediately.
  Remove-Item config.live_e2e.yaml -Force -EA 0

Task 37 (LARGE): Final Jira sprint status check.
  Via Atlassian connector: query all C061 stories.
  All should be Done. Control task should be Done.
  Any still In Progress: transition with comment "C061 complete, transitioning to Done."

Task 38 (LARGE): Confirm coverage floor holds after post-merge hydration commits.
  D's --cov=src was run on the cycle branch before merge.
  After merge, do a quick sanity check:
  git checkout develop && git pull
  py -3.12 -m pytest -q --cov=src --cov-fail-under=90 --no-header tests/unit/ 2>&1 | tail -5
  Must still be >=90%. Post-merge commits are docs-only so coverage should be identical.

Task 39 (LARGE): Final Jira board hygiene (part of Tier A plan).
  39a. Via Atlassian connector: search for stale board-setup issues.
       JQL: project = SCRUM AND status = "To Do" AND issueType = Task AND created < "2025-01-01"
  39b. This will return the stale Wave 1-9 board setup issues (SCRUM-5 through ~SCRUM-72).
  39c. Per previous PM audit: these are confirmed completed but never closed.
  39d. For C061: D should close the most clearly-done ones to start cleaning the board.
       Close with comment: "Board setup work for this wave was completed during initial project setup. Closing to clean board."
       Target for D: close at least 10-15 of the most clearly-done ones.
       Leave ones requiring active decision (like SCRUM-55 schema reconciliation) In Progress.
  39e. DO NOT close canonical product epics (SCRUM-16 through SCRUM-25).

Task 40 (LARGE): Final D checklist (expanded).
  [ ] All 5 agent reports read; deliverables table built
  [ ] G1 attribution: EVERY commit SHA enumerated via git log; zone table complete
  [ ] G1 result: ALL PASS or documented violations
  [ ] TC-1 PRAGMA: D ran independently; raw_value + relevance_score + trend_direction PRESENT
  [ ] D parity table: all YES
  [ ] Dashboard demo-data: D ran independently; zero matches
  [ ] Codex pre-resolve: JSON in D report; thread count recorded
  [ ] Codex fixes: implemented; threads resolved
  [ ] Codex post-resolve: JSON in D report; 0 unresolved confirmed
  [ ] PR size: override:large-pr label applied
  [ ] G2 (Codex x2): BOTH JSONs in D report
  [ ] G3 (CI): all required checks PASS
  [ ] G4 (--cov=src): one run; >=90% overall; module details in D report
  [ ] G5 (golden): kw=110 = 62.7/1.0/CONDITIONAL_GO
  [ ] G6 (regression pack): 88+ passed; new tests included
  [ ] G7 (ruff + mypy): PASS
  [ ] G8 (config gate): scrapfly.enabled=false
  [ ] G9 (TC-1 PRAGMA): PASS
  [ ] G10 (dashboard): PASS
  [ ] PR squash-merged; C061_SQUASH_SHA recorded
  [ ] Cycle branch deleted
  [ ] Jira: all C061 stories Done + control Done
  [ ] Hydration header: CYCLE_CURRENT=062, G-B CLOSED, G-C CLOSED, squash SHA recorded
  [ ] EPIC_STATUS_TRACKER: updated with C061 result and C062 preview
  [ ] sec7: updated if new regressions from F
  [ ] CYCLE_061_PM_REVIEW.md seed: created
  [ ] Scratch scripts removed from PM_Pack
  [ ] config.live_e2e.yaml absent from disk
  [ ] Baseline DB mtime unchanged
  [ ] CYCLE_061_AGENT_D.md committed and pushed to develop
