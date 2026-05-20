====================================================================
AGENT A — CYCLE 029 PROMPT
15 LARGE–XLARGE tasks, each with embedded sub-tasks
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/029/integration
- Python 3.11+ | Playwright async (mocked in tests) | SQLAlchemy 2.0
- Prior cycle PR: #32 ready to merge (1608 tests, 95.04%, codecov/patch 100%)

## PM VERIFIED STATE (2026-05-19)
- seller_profile.py: helpers built (Cycle 028). Real path raises NotImplementedError.
- fiverr_selectors.py: no SELLER_* constants exist yet. Must be added.
- SCRUM-150 "[COLLECTION] S2.10 Seller Profile" = In Progress (live verified)
- SCRUM-517 = In Progress (close after PR #32 merge)
- Spec: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Workflow 5 (Stage 5)

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch ≥ 90% — HARD merge blocker
G-003: Codex GraphQL query mandatory every PR
G-004: Agent D fills full merge gate checklist
G-005: R-091 — delete merged cycle branch remote + local after every merge

## ⚠️ R-092 COVERAGE RULE
Run ONLY targeted patch coverage on YOUR modules. NOT the full suite.
Agent D runs the single comprehensive audit.

---

## TASK 1 [LARGE] — PR #32 Full Gate Verification, Mandatory Codex Disposition, and Merge Execution
Verify all CI checks pass, run the mandatory Codex thread review, and merge PR #32 into develop.
Sub-tasks:
1.1 Run full preflight and record all output: Get-Location (must be C:\Fiverr\Fiverr),
    git rev-parse --show-toplevel, git branch --show-current, git status --short --branch,
    git worktree list, git fetch origin.
1.2 Verify PR #32: gh pr view 32 --json state,mergeable,statusCheckRollup
    Confirm codecov/project=SUCCESS, codecov/patch=SUCCESS, every CI check green.
    Record full statusCheckRollup verbatim. Abort cycle if codecov/patch FAILURE.
1.3 Run mandatory Codex query verbatim (required G-003):
    gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=32
    Record raw result. Agent D Cycle 028 confirmed 3 threads all isResolved=true.
    If any thread is NOT resolved: classify as VALID_FIXED/VALID_INTENDED/INVALID,
    fix VALID_FIXED issues with regression tests, reply with disposition format, resolve manually.
1.4 Merge: gh pr merge 32 --merge. Record merge SHA.
1.5 Post-merge validation: python -m pytest -q --cov=src --cov-fail-under=90
    Expected: 1608 tests, 95.04%+. Record actual output. Any failure is a BLOCKER.
    Resolve failures before proceeding to Task 2.

## TASK 2 [LARGE] — Branch Hygiene Enforcement (R-091), New Cycle Branch Creation, and Cycle Control Ticket Management
Delete the merged stale branch, create the fresh cycle branch, and open the Jira control tickets.
Sub-tasks:
2.1 Checkout develop and sync: git checkout develop && git pull --ff-only origin develop
2.2 Delete merged remote branch (R-091): git push origin --delete cycle/028/integration
2.3 Delete merged local branch (R-091): git branch -D cycle/028/integration
2.4 Prune stale remote refs: git fetch --all --prune
2.5 List remaining remote cycle branches: git branch -r | Select-String "cycle/"
    Record count before (X) and after (Y) cleanup. Cycle 029 is NOT a 5-cycle boundary
    (next periodic deep cleanup at Cycle 030). Document in your cycle report:
      Branch Hygiene — Cycle 029: merged+deleted cycle/028/integration (remote+local),
      remote cycle branches before: X, after: Y, periodic cleanup due: Cycle 030.
2.6 Create cycle branch and push: git checkout -b cycle/029/integration &&
    git push -u origin cycle/029/integration
2.7 Jira: Transition SCRUM-517 → Done. Post evidence comment with merge SHA.
2.8 Jira: Create SCRUM-518 as Cycle 029 control ticket → In Progress.
    Post kickoff comment summarising Cycle 029 scope (W5, W2 LLM steps, W7 Reddit).
2.9 Verify cycle branch is active: git branch --show-current → cycle/029/integration.

## TASK 3 [XLARGE] — Full Specification Research: W5 Workflow Spec, All Related Source Code, and SCRUM-150 AC/DoD Extraction
Read and document every piece of information needed to implement Workflow 5 correctly before touching any source file.
Sub-tasks:
3.1 Read in full: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
    Extract and record in your cycle report every detail from Workflow 5 — Stage 5:
    - All 9 numbered steps with exact descriptions
    - All 11 field names from Step 6 with their exact source description
      (seller_level from badge, member_since from About section, response_time from stats bar,
       response_rate from stats bar, languages list, bio_text, total_reviews from header,
       total_gigs from gig section, active_gig_titles, portfolio_count, badges)
    - Full error handling table (404 → skip no DEAD_LETTER, private/deactivated → skip,
      parse error on field → store null continue)
    - Checkpoint spec: every 25 sellers, file path data/checkpoints/{run_id}/stage05_{niche_id}.json
    - Pacing spec: "fiverr_seller_profile" key, base 5s + jitter 0–3s, max 40/hour
3.2 Read in full: src/collection/workflows/seller_profile.py
    Document: existing helper functions, their signatures, what Cycle 028 Agent C added,
    current state of run_seller_profile_collection stub and should_skip_seller_profile.
3.3 Read in full: src/collection/fiverr_selectors.py
    Document: naming convention for constants, comment style, existing GIG_CARD_* pattern.
    Confirm no SELLER_* constants exist.
3.4 Read: src/models/seller.py — document write_seller_profile() full signature,
    all fields it persists, and get_seller() query helper.
3.5 Read: src/collection/session_manager.py — document new_page() and close_page() API,
    what exceptions they raise, what async context they expect.
3.6 Read SCRUM-150 full AC/DoD in Jira. Post planning comment confirming:
    "Cycle 029 Agent A implementing Workflow 5 real Playwright path per W5 spec.
    Scope: all 11 fields, staleness/dedup guards, 12+ AsyncMock tests."
3.7 Cross-reference: confirm write_seller_profile() accepts all 11 spec fields or note
    any fields missing from the Seller model that need to be added.

## TASK 4 [LARGE] — SELLER_* Selector Constants: Research, Implementation, and Import Verification
Create all named CSS selector constants that Workflow 5 needs to extract seller profile data.
Sub-tasks:
4.1 Based on Fiverr's standard page structure and the GIG_CARD_* naming pattern in
    fiverr_selectors.py, add ALL of the following named constants with best-estimate
    CSS selector values (div[data-testid], span classes matching known Fiverr patterns):
      SELLER_LEVEL_BADGE      — seller badge/level element on profile
      SELLER_MEMBER_SINCE     — "Member since Jan 2022" text container in About section
      SELLER_RESPONSE_TIME    — response time element in stats bar
      SELLER_RESPONSE_RATE    — response rate % element in stats bar
      SELLER_LANGUAGES        — language list container
      SELLER_BIO              — seller bio/description block
      SELLER_TOTAL_REVIEWS    — review count displayed in profile header
      SELLER_TOTAL_GIGS       — gig count in profile gig section
      SELLER_GIG_TITLE        — individual gig title element (for query_selector_all)
      SELLER_PORTFOLIO_ITEM   — portfolio thumbnail element (for query_selector_all count)
      SELLER_BADGE            — individual badge element (for query_selector_all)
4.2 Every constant must include this exact comment on the line above it:
    # UNVERIFIED — requires live DOM validation before first real run
4.3 Run import verification: python -c "from src.collection.fiverr_selectors import SELLER_LEVEL_BADGE, SELLER_MEMBER_SINCE, SELLER_BIO; print('OK')"
    Must print OK with no import errors.
4.4 Run: python -m ruff check src/collection/fiverr_selectors.py → must be clean.
4.5 Run: python -m mypy src/collection/fiverr_selectors.py → must pass.

## TASK 5 [XLARGE] — Implement and Test Staleness Check and Run-Level Deduplication Guards
Implement both pre-navigation guards that prevent redundant Seller collection and write tests for them.
Sub-tasks:
5.1 In the non-dry path of run_seller_profile_collection, before any page = new_page() call,
    implement the staleness check (spec Step 1):
      from sqlalchemy.orm import Session
      from src.models.seller import get_seller
      from datetime import datetime, UTC, timedelta
      if isinstance(db, Session):
          existing = get_seller(seller_username, db)
          if existing and existing.profile_collected and existing.profile_collected_at:
              ttl = timedelta(hours=existing.ttl_hours or 720)
              if datetime.now(UTC) < existing.profile_collected_at + ttl:
                  return {"seller_username": seller_username, "collected": False,
                          "skipped": True, "reason": "fresh_row_exists", "dry_run": False}
5.2 Implement run-level deduplication (spec Step 2). Update should_skip_seller_profile()
    from its current always-False stub to a real check: query sellers table for
    a row with this (seller_username, run_id) combination already having profile_collected=True.
    If found: return {"seller_username": seller_username, "collected": False,
                      "skipped": True, "reason": "already_collected_this_run", "dry_run": False}
5.3 Write 5 unit tests covering all guard branches:
      test_w5_skips_when_fresh_row_exists — mock get_seller returns fresh TTL-valid row → skipped=True
      test_w5_does_not_skip_when_stale_row — row exists but collected_at > TTL → continues
      test_w5_does_not_skip_when_no_row — get_seller returns None → continues
      test_w5_skips_when_already_collected_this_run — should_skip_seller_profile returns True → skipped=True
      test_w5_guards_not_triggered_when_db_not_session — non-Session db → guards skipped gracefully
5.4 Run: python -m pytest -q tests/unit/test_seller_profile.py -k "skip" --no-header
    All 5 new guard tests must pass.

## TASK 6 [LARGE] — Implement _safe_text Helper, Playwright Navigation, Pacing Integration, and 404/Private Error Handling
Build the helper for safe field extraction and the page navigation entry point with all error cases.
Sub-tasks:
6.1 Add to seller_profile.py:
      async def _safe_text(page: Any, selector: str) -> str | None:
          """Extract inner_text from selector. Returns None on any error — spec: 'Store null, continue'."""
          try:
              el = await page.query_selector(selector)
              return (await el.inner_text()).strip() if el else None
          except Exception:
              return None
6.2 In the non-dry path, after guards pass, implement page navigation:
      page = await session_manager.new_page()
      try:
          await page.goto(build_seller_profile_url(seller_username),
                          wait_until="domcontentloaded", timeout=30_000)
          await pacing_manager.wait("fiverr_seller_profile", dry_run=False)
6.3 Implement error handling for 404 and private/deactivated per spec error table:
      except Exception as exc:
          err_str = str(exc).lower()
          if "404" in err_str or "not found" in err_str:
              logger.warning("Seller 404: %s", seller_username)
              await session_manager.close_page(page)
              return {"seller_username": seller_username, "collected": False, "error": "404", "dry_run": False}
          if "private" in err_str or "deactivated" in err_str:
              logger.warning("Seller private/deactivated: %s", seller_username)
              await session_manager.close_page(page)
              return {"seller_username": seller_username, "collected": False, "error": "private_or_deactivated", "dry_run": False}
          raise  # all other errors bubble to retry handler
6.4 Write 4 unit tests:
      test_w5_real_navigates_to_correct_url — page.goto called with fiverr.com/{username}
      test_w5_real_calls_pacing_wait — pacing_manager.wait("fiverr_seller_profile") called
      test_w5_real_handles_404_gracefully — mock goto raises 404 → collected=False, close_page called
      test_safe_text_returns_none_when_selector_not_found — query_selector returns None → None

## TASK 7 [XLARGE] — Implement Stats Field Extraction: Level, Member Since, Response Time/Rate, Review Count, Gig Count + Tests
Extract and parse all core numeric and text stats fields from the seller profile page.
Sub-tasks:
7.1 In the try block after successful navigation, extract all 6 stats fields using _safe_text:
      seller_level_text  = await _safe_text(page, SELLER_LEVEL_BADGE)
      member_since_text  = await _safe_text(page, SELLER_MEMBER_SINCE)
      response_time_text = await _safe_text(page, SELLER_RESPONSE_TIME)
      response_rate_text = await _safe_text(page, SELLER_RESPONSE_RATE)
      total_reviews_text = await _safe_text(page, SELLER_TOTAL_REVIEWS)
      total_gigs_text    = await _safe_text(page, SELLER_TOTAL_GIGS)
7.2 Apply existing parser helpers to produce typed values:
      seller_level  = parse_seller_level(seller_level_text)
      member_since  = parse_member_since(member_since_text)
      response_rate = parse_response_rate(response_rate_text)
7.3 Add new helper for integer parsing:
      def _parse_int(text: str | None) -> int | None:
          import re
          if not text: return None
          nums = re.findall(r"[\d]+", text.replace(",", ""))
          return int(nums[0]) if nums else None
7.4 Apply _parse_int to review count and gig count:
      total_reviews = _parse_int(total_reviews_text)
      total_gigs    = _parse_int(total_gigs_text)
7.5 Write 6 unit tests covering stats extraction:
      test_w5_real_extracts_seller_level — mock SELLER_LEVEL_BADGE returns "Level 2 Seller" → "LEVEL_2"
      test_w5_real_extracts_member_since — mock SELLER_MEMBER_SINCE returns "Member since Jan 2022" → "2022-01"
      test_w5_real_extracts_response_rate — mock SELLER_RESPONSE_RATE returns "98%" → 98
      test_w5_real_extracts_total_reviews — mock SELLER_TOTAL_REVIEWS returns "1,234 Reviews" → 1234
      test_parse_int_handles_commas — "1,234" → 1234
      test_parse_int_none_input → None → None

## TASK 8 [XLARGE] — Implement List Field Extraction: Bio, Active Gig Titles, Portfolio Count, Badges + Tests
Extract array and multi-element fields using query_selector_all.
Sub-tasks:
8.1 Extract single-text field bio:
      bio_text = await _safe_text(page, SELLER_BIO)
8.2 Extract active_gig_titles using query_selector_all:
      gig_els = await page.query_selector_all(SELLER_GIG_TITLE)
      active_gig_titles = [await el.inner_text() for el in gig_els[:20]]
      (cap at 20 per spec depth="full" means top 20 gigs)
8.3 Extract portfolio count using query_selector_all:
      portfolio_els = await page.query_selector_all(SELLER_PORTFOLIO_ITEM)
      portfolio_count = len(portfolio_els)
8.4 Extract badges best-effort:
      badge_els = await page.query_selector_all(SELLER_BADGE)
      badges = [await el.inner_text() for el in badge_els]
8.5 Write 5 unit tests:
      test_w5_real_extracts_active_gig_titles — mock returns 3 gig title elements → list of 3 strings
      test_w5_real_caps_active_gig_titles_at_20 — mock returns 25 elements → only 20 collected
      test_w5_real_extracts_portfolio_count — mock returns 4 portfolio elements → portfolio_count=4
      test_w5_real_extracts_badges — mock badge elements → badges list populated correctly
      test_w5_real_bio_text_none_when_missing — SELLER_BIO selector not found → bio_text=None, no crash

## TASK 9 [LARGE] — Implement DB Write, Checkpoint Write, Page Cleanup in Finally, and Result Return
Persist all extracted data, write checkpoint, ensure page is always closed, build return payload.
Sub-tasks:
9.1 After all field extraction, write sellers row via existing write_seller_profile:
      from src.models.seller import write_seller_profile
      write_seller_profile(
          seller_username=seller_username, run_id=run_id,
          seller_level=seller_level, member_since=member_since,
          response_time=response_time_text, total_reviews=total_reviews,
          total_gigs=total_gigs, db=db,
      )
9.2 Write checkpoint per spec (every 25 sellers):
      if checkpoint_manager:
          await checkpoint_manager.write(run_id, f"stage05_{niche_id}",
              {"seller_username": seller_username, "collected": True})
9.3 Ensure page.close is ALWAYS in the finally block — NOT inside try:
      finally:
          await session_manager.close_page(page)
9.4 Build and return the complete result dict with all collected values.
9.5 Write 4 unit tests:
      test_w5_real_writes_seller_row — write_seller_profile called with all expected args
      test_w5_real_closes_page_on_success — close_page called after successful collection
      test_w5_real_closes_page_on_exception — mock raises mid-extraction → close_page still called in finally
      test_w5_real_returns_collected_true_with_all_fields — complete mock → result has collected=True

## TASK 10 [LARGE] — Verify Dry Run Path Integrity + Validate Full Test Suite Passes
Confirm the existing dry_run=True path is completely untouched by new code.
Sub-tasks:
10.1 Run: python -m pytest -q tests/unit/test_seller_profile.py -k "dry_run" --no-header
     ALL existing dry_run tests must pass unchanged. If any fail: find what your new code
     broke in the dry path and fix it before proceeding.
10.2 Run the complete seller_profile test file: python -m pytest -q tests/unit/test_seller_profile.py --no-header
     Record total count. Minimum 12 NEW tests must exist (from Tasks 5–9).
     If under 12: identify which test cases are missing and add them now.
10.3 Confirm no test in the file creates a real Playwright browser, popen, or subprocess.
     Scan for AsyncMock and MagicMock usage — all Playwright interactions must be mocked.
10.4 Run: python -m pytest -q tests/unit/test_session_manager.py --no-header
     Verify Agent A's upstream changes didn't break session_manager tests.

## TASK 11 [LARGE] — Targeted Patch Coverage Audit and Gap Closure for All Agent A Changed Modules
Run R-092 Tier 1 targeted coverage and close any uncovered lines before handoff.
Sub-tasks:
11.1 Run targeted coverage on seller_profile.py:
       python -m pytest -q --cov=src.collection.workflows.seller_profile --cov-report=term-missing tests/unit/test_seller_profile.py
     Record coverage % and every uncovered line number.
11.2 Run targeted coverage on fiverr_selectors.py:
       python -m pytest -q --cov=src.collection.fiverr_selectors --cov-report=term-missing
     Record coverage % for new SELLER_* constants.
11.3 If seller_profile.py < 90%: write specific tests for every uncovered line or branch.
     Re-run coverage. Repeat until >= 90%.
11.4 Document final per-module coverage in cycle report.
     DO NOT run: python -m pytest --cov=src — that is Agent D's job.

## TASK 12 [LARGE] — Code Quality: Ruff Lint and Mypy Type Check on All Changed Files
Sub-tasks:
12.1 Run ruff check on ALL files you modified:
       python -m ruff check src/collection/workflows/seller_profile.py src/collection/fiverr_selectors.py tests/unit/test_seller_profile.py
     Fix every reported issue. Re-run until completely clean.
12.2 Run mypy on implementation files:
       python -m mypy src/collection/workflows/seller_profile.py src/collection/fiverr_selectors.py
     Fix every type error, especially return types on _safe_text → str | None and _parse_int → int | None.
12.3 Run: python run.py collect-only
     Must complete without errors. Confirms that collect-only mode still works after W5 changes.
     Record pass/fail in report.

## TASK 13 [LARGE] — Jira Story Advancement: SCRUM-150 Evidence, SCRUM-17 Epic Update, Ledger Update
Post all Jira evidence and advance the story status.
Sub-tasks:
13.1 Post implementation evidence on SCRUM-150:
     "Cycle 029 Agent A: Workflow 5 real Playwright path implemented. 10 SELLER_* selectors
     added to fiverr_selectors.py (marked UNVERIFIED — needs live DOM validation).
     Staleness + run-dedup guards prevent re-collection. Navigation via session_manager
     with 30s timeout and pacing enforcement. All 11 spec fields extracted (level/since/
     response/bio/reviews/gig_count/active_titles/portfolio/badges). DB write via
     write_seller_profile. Checkpoint every 25 sellers. Page close in finally. Error
     handling: 404/private per spec table. 12+ AsyncMock tests. seller_profile ≥ 90% patch.
     DoD remaining: live authenticated session validates all 10 SELLER_* selectors."
13.2 Post SCRUM-17 epic progress comment: W5 real Playwright path now available.
13.3 Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md — add Cycle 029 Agent A entries:
     SCRUM-517 (Done, merge SHA evidence), SCRUM-518 (In Progress), SCRUM-150 (advanced, real path done).

## TASK 14 [LARGE] — Artifact Hygiene, No-Main Verification, and Cycle Report Creation
Ensure the workspace is clean and create the complete cycle report.
Sub-tasks:
14.1 Artifact hygiene: git status --short
     Confirm NOT staged: .env, data/sessions/, *.db, coverage.xml, any unintended files.
     git branch --show-current must be cycle/029/integration.
     git worktree list must show single expected worktree.
14.2 Create docs/cycle_reports/CYCLE_029_AGENT_A.md with ALL sections:
     - Branch Hygiene (R-091 evidence: branches deleted, counts before/after, next periodic at 030)
     - PR #32 Codex query result (verbatim raw output)
     - Results for all 14 tasks with pass/fail notation
     - Full list of SELLER_* constants added with their values
     - Test count from targeted run
     - Coverage % per module from Task 11
     - Final agent commit SHA
     - Handoff notes for Agent B: W5 available, selectors added, what Agent B needs to know

## TASK 15 [LARGE] — Scoped Commit and SHA Freeze
Commit exactly the Agent A scope files. Do NOT push.
Sub-tasks:
15.1 Stage ONLY these files (verify with git diff --cached --name-only after each add):
       git add src/collection/workflows/seller_profile.py
       git add src/collection/fiverr_selectors.py
       git add tests/unit/test_seller_profile.py
       git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md
       git add docs/cycle_reports/CYCLE_029_AGENT_A.md
15.2 Verify staged files: git diff --cached --name-only
     Must show exactly the 5 files above. Remove anything unexpected with git restore --staged.
15.3 Commit:
       git commit -m "feat(collection): Workflow 5 real Playwright implementation [Agent A Cycle 029]"
15.4 Record final SHA: git rev-parse HEAD → document in cycle report as the handoff SHA for Agent B.

====================================================================
END AGENT A — 15 LARGE–XLARGE TASKS
====================================================================
