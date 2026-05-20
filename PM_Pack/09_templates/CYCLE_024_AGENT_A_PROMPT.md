====================================================================
AGENT A — CYCLE 024 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/024/integration
- Python 3.11+ | Playwright (async) | SQLAlchemy 2.0
- Prior cycle PR: #27 ready to merge (1161 tests, 94.08%, codecov/patch 100%)

## ⚠️ CRITICAL CYCLE PIVOT — READ FIRST

Cycle 024 pivots from product feature work to E02 Collection Engine infrastructure.
The project is ~38% complete end-to-end. The single biggest blocker: E02 Collection has
NEVER scraped real Fiverr data. Without it, the scoring/recommendations/pricing pipeline
is entirely theoretical. This cycle builds the foundation: SessionManager + selectors.

## ⚠️ HARD GATE RULES (PERMANENT)
G-001: codecov/patch ≥ 90% — HARD merge blocker. Never merge while it fails.
G-003: Codex query MUST be run for every PR. Classify, fix VALID_FIXED with regression
  test, reply to ALL threads with disposition format, resolve ALL threads.
G-004: Agent D must complete the mandatory merge gate checklist.

## YOUR ROLE
Agent A owns the PR gate, branch setup, and the SessionManager + fiverr_selectors.py.
These are the two foundational files that ALL collection modules depend on.
Spec: PM_Pack/ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md (read in full).

IMPORTANT TESTING CONSTRAINT: NO real Playwright browser is launched in tests.
All tests mock Playwright using unittest.mock.AsyncMock and MagicMock.
The headed login flow (user input()) MUST be guarded by a config flag.

## GIT INSTRUCTIONS
1. Verify PR #27: gh pr view 27 --json state,mergeable,statusCheckRollup
   Confirm codecov/project=SUCCESS AND codecov/patch=SUCCESS.
2. Run Codex query for PR #27 (see Task 2).
3. gh pr merge 27 --merge (only when all checks SUCCESS and Codex verified).
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/024/integration && git push -u origin cycle/024/integration
6. Commit: feat(collection): SessionManager and fiverr_selectors [Agent A Cycle 024]
7. Do NOT push final branch — human operator pushes after all 4 agents.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 27 --json state,mergeable,statusCheckRollup
Pass: root = C:\Fiverr\Fiverr. All checks SUCCESS. Abort if codecov/patch FAILURE.

## TASKS

### Task 1: Preflight and PR #27 verification
Run all 7 preflight commands. Capture FULL statusCheckRollup output.
Verify: "codecov/patch" conclusion == "SUCCESS".

### Task 2: Codex disposition query for PR #27 (MANDATORY)
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=27
Document: total threads found. Confirm Agent D's 3 threads all show isResolved=true.
If any thread NOT resolved: classify and resolve before merging.

### Task 3: Merge PR #27, close SCRUM-512, create branch
- gh pr merge 27 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 1161+, 94.08%+
- git checkout -b cycle/024/integration && git push -u origin cycle/024/integration
- Jira: SCRUM-512 → Done (post merge SHA comment)
- Jira: Create SCRUM-513 as Cycle 024 control → In Progress

### Task 4: Read E02 collection specs and Jira stories (REQUIRED before coding)
Read in full:
  PM_Pack/ref/project_plan/04_collection/PLAYWRIGHT_SESSION_DESIGN.md
  PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
Read: src/collection/ directory (existing stubs from audit PR #16)
Query SCRUM-17 children → find S2.1 (SessionManager/session) story key.
Read full AC/DoD for that story. Transition to In Progress. Post planning comment.
Record the exact Jira story key in your report.

### Task 5: Verify .gitignore covers session and runtime files
Check .gitignore for:
  - data/sessions/
  - data/sessions/fiverr_session.json
  - data/checkpoints/
If missing, add them. Run: git check-ignore -v data/sessions/fiverr_session.json
Expected: shows it is gitignored. Document in report.

### Task 6: Create src/collection/fiverr_selectors.py
Implement EXACTLY as specced in PLAYWRIGHT_SESSION_DESIGN.md "Fiverr DOM Selectors" section.
Every named constant must be present:
- Session verification: LOGGED_IN_INDICATOR, LOGGED_IN_FALLBACK
- Search results page: SEARCH_RESULT_COUNT, GIG_CARD_CONTAINER, GIG_CARD_TITLE,
  GIG_CARD_SELLER_NAME, GIG_CARD_SELLER_LEVEL, GIG_CARD_RATING, GIG_CARD_REVIEW_COUNT,
  GIG_CARD_PRICE, GIG_CARD_DELIVERY, GIG_CARD_LINK, GIG_CARD_SPONSORED, GIG_CARD_QUEUE,
  PAGINATION_NEXT
- Gig detail page: GIG_DETAIL_TITLE through GIG_DETAIL_READ_MORE (all from spec)
- Seller profile page: SELLER_LEVEL_BADGE through SELLER_BADGES (all from spec)
No logic in this file — constants only.

### Task 7: Create src/collection/human_events.py
Spec: PLAYWRIGHT_SESSION_DESIGN.md references this module.
Implement stubs for the 3 functions SessionManager depends on:
  def random_viewport() -> dict:
    """Returns a random viewport dict. For tests: always returns {"width": 1280, "height": 800}"""
    import random
    widths = [1280, 1366, 1440, 1536, 1920]
    heights = [720, 768, 800, 864, 900, 1080]
    return {"width": random.choice(widths), "height": random.choice(heights)}

  def random_user_agent() -> str:
    """Returns a random Chrome user agent string."""
    agents = [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    ]
    import random
    return random.choice(agents)

  def attach_human_events(page: "Page", pacing_config: dict) -> None:
    """
    Attaches human-like event simulation to a Playwright page.
    Stub: no-op in v1. Future: add random scroll timing, mouse movement.
    """
    pass

### Task 8: Create src/collection/session_manager.py
Implement EXACTLY as specced in PLAYWRIGHT_SESSION_DESIGN.md.
Key implementation requirements:
- Full SessionManager class with __aenter__ / __aexit__
- new_page() → creates page, attaches human_events, increments _pages_open
- close_page(page) → closes page, decrements _pages_open
- close() → gracefully closes context, browser, playwright
- _initialize() → called once at startup (idempotent)
- _load_or_login() → checks for session file, calls _load_session_headless() or _headed_login_flow()
- _verify_session(context) → navigates to fiverr.com, checks LOGGED_IN_INDICATOR
- _headed_login_flow() → checks config flag FIRST:

  CRITICAL: The headed login flow MUST be guarded:
  At the top of _headed_login_flow(), add:
    # Guard: if playwright.require_login is False (default), raise a safe error
    # This prevents tests and phase2-smoke from triggering the interactive login
    if not self.config.get("playwright", {}).get("require_login", False):
      raise SessionLoginError(
        "Headed login flow is disabled. Set playwright.require_login: true in config "
        "and run: python run.py --mode relogin to authenticate."
      )

- _load_session_headless() → opens Chromium headless with storage_state
- _context_options() → returns dict with random_viewport, random_user_agent, locale, etc.
- _browser_args() → returns list from spec
- SessionLoginError exception class (defined at module level)

Also add a class-level constant:
  FIVERR_BASE_URL = "https://www.fiverr.com"

### Task 9: Write tests for session_manager and selectors
Create: tests/unit/test_session_manager.py

ALL Playwright objects must be mocked — NO real browser launched.
Use AsyncMock for coroutines, MagicMock for sync objects.

Required tests (minimum 14):
- test_session_manager_init — creates SM with config, attributes set correctly
- test_selectors_constants_present — LOGGED_IN_INDICATOR, GIG_CARD_TITLE, etc. are strings
- test_random_viewport_returns_dict — random_viewport() returns dict with width and height
- test_random_user_agent_returns_string — random_user_agent() returns non-empty string
- test_attach_human_events_no_crash — attach_human_events(mock_page, {}) does not raise
- test_close_cleans_resources — sm.close() closes context, browser, playwright in order
- test_new_page_increments_counter — new_page() increments _pages_open
- test_close_page_decrements_counter — close_page() decrements _pages_open
- test_headed_login_disabled_by_default — _headed_login_flow() raises SessionLoginError
  when config does not have playwright.require_login=True
- test_load_or_login_no_session_file — session file not present → calls _headed_login_flow
  (mock the _headed_login_flow method to avoid actual login)
- test_load_or_login_session_expired — _verify_session returns False → calls _headed_login_flow
  (mock both methods)
- test_verify_session_success — mock page.query_selector returns a truthy element → True
- test_verify_session_failure — mock page.query_selector returns None → False
- test_context_manager_enter_exit — async with SessionManager(config) calls close()

### Task 10: Run targeted tests
python -m pytest -q tests/unit/test_session_manager.py
All 14+ tests pass. Record count.

### Task 11: Run targeted patch coverage
python -m pytest -q --cov=src.collection.session_manager --cov-report=term-missing
python -m pytest -q --cov=src.collection.fiverr_selectors --cov-report=term-missing
python -m pytest -q --cov=src.collection.human_events --cov-report=term-missing
All new code ≥ 90% covered. Add tests for any uncovered branches.

### Task 12: Run ruff + mypy
python -m ruff check src/collection/session_manager.py src/collection/fiverr_selectors.py src/collection/human_events.py tests/unit/test_session_manager.py
python -m mypy src/collection/session_manager.py src/collection/
Both must pass.

### Task 13: Run full validation block
python -m ruff check . && python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle024.db
python run.py phase2-smoke
Target: ≥ 1175 tests. Coverage ≥ 90%. All PASS.

### Task 14: Post Jira evidence for E02 S2.1 story
Post: "Cycle 024 Agent A: SessionManager implemented in src/collection/session_manager.py.
  All selectors in fiverr_selectors.py. human_events.py stubs. Headed login guarded by
  require_login config flag. 14+ tests (all mocked Playwright). data/sessions/ gitignored.
  DoD remaining: real login flow tested with actual Fiverr session, session expiry re-login."

### Tasks 15-24: Standard completion
15. Update ACTIVE_STORY_DOD_LEDGER.md (SCRUM-513, E02 S2.1 story key).
16. Artifact hygiene: no .env, *.db, coverage.xml, data/sessions/ staged.
17. No-main / worktree check.
18. Record SHA and handoff to Agent B.
19. Create docs/cycle_reports/CYCLE_024_AGENT_A.md.
20. Commit scoped files only.
21. Run python run.py recommendations-only → must pass.
22. Run python run.py phase2-smoke → must pass.
23. Read E02 S2.2 (Queue/Job) story for Agent B — post planning intent comment.
24. Final SHA + test count recorded.

## FILES CREATED THIS CYCLE (Agent A)
| Action | File |
|---|---|
| CREATE | src/collection/session_manager.py |
| CREATE | src/collection/fiverr_selectors.py |
| CREATE | src/collection/human_events.py |
| MODIFY | .gitignore (if data/sessions/ not already covered) |
| CREATE | tests/unit/test_session_manager.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_024_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/collection/session_manager.py src/collection/fiverr_selectors.py src/collection/human_events.py
git add .gitignore tests/unit/test_session_manager.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_024_AGENT_A.md
git commit -m "feat(collection): SessionManager and fiverr_selectors [Agent A Cycle 024]"
====================================================================
END OF AGENT A PROMPT
====================================================================
