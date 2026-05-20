====================================================================
AGENT D — CYCLE 029 PROMPT
16 LARGE–XLARGE tasks, each with embedded sub-tasks
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/029/integration
- Python 3.11+ | praw (Reddit API) | GitHub CLI

## PM VERIFIED STATE (2026-05-19)
- reddit_signals.py: full stub interface from Cycle 028. Real path raises NotImplementedError.
- Helpers ready: build_subreddit_search_url, parse_reddit_post_count_90d,
  select_top_posts_for_llm, build_reddit_demand_signal_json
- SIGNAL_REDDIT_DEMAND, SIGNAL_REDDIT_ACTIVITY: confirmed in external_signal.py
- SCRUM-152 "[COLLECTION] S2.12 Reddit Signal Collection" = In Progress (live verified)
- Spec: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Workflow 7 (Stage 6b)

## HARD GATE RULES (PERMANENT — G-001, G-003, G-004)
G-001: codecov/patch >= 90% — HARD merge blocker, never merge while FAIL
G-003: Codex GraphQL query MUST run for every PR. Classify all threads.
       Fix VALID_FIXED with regression test. Reply ALL threads. Resolve ALL manually.
G-004: Agent D fills complete merge gate checklist in report AND PR comment.
       ALL PASS/YES before merge.

## R-092 TIER 2 — YOU ARE THE ONLY AGENT RUNNING THE FULL AUDIT
Agents A/B/C ran only targeted patch coverage on their modules.
You run the single comprehensive validation block + per-module audit before PR creation.

---

## TASK 1 [LARGE] — Preflight, Full Suite Baseline, and All Agent Handoff Reads
Sync the branch, verify every expected deliverable from Agents A/B/C exists, and run the first
full baseline test suite to confirm the codebase is clean before any new work begins.
Sub-tasks:
1.1 Run full preflight: Get-Location (must be C:\Fiverr\Fiverr), git branch --show-current
    (must be cycle/029/integration), git log --oneline -12, git worktree list.
1.2 git pull origin cycle/029/integration — sync all Agent A/B/C commits.
1.3 Read ALL three cycle reports in full:
    docs/cycle_reports/CYCLE_029_AGENT_A.md
    docs/cycle_reports/CYCLE_029_AGENT_B.md
    docs/cycle_reports/CYCLE_029_AGENT_C.md
1.4 Verify ALL expected deliverables exist on disk:
    Test-Path "src\collection\workflows\seller_profile.py" → True (W5 real, Agent A)
    Test-Path "src\collection\fiverr_selectors.py" → True (SELLER_* constants, Agent A)
    Test-Path "src\llm\templates\stage02_keyword_expansion\llm_generate.j2" → True (Agent B)
    Test-Path "src\llm\templates\stage02_keyword_expansion\llm_relevance.j2" → True (Agent B)
    Test-Path "src\llm\templates\stage02_keyword_expansion\llm_intent.j2" → True (Agent C)
    Document any missing files as GAPS in your cycle report.
1.5 Run the first full baseline: python -m pytest -q --cov=src --cov-fail-under=90
    Record: total test count, global coverage %. Any test failures = BLOCKERS.
    Resolve all failures before proceeding to Task 2.

## TASK 2 [XLARGE] — Full Specification Research: W7 Reddit Workflow, praw API, and Existing Helpers
Read and extract every detail from the W7 spec and existing codebase before writing a single line
of implementation code.
Sub-tasks:
2.1 Read in full: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
    Focus: Workflow 7 — Stage 6b. Extract and document in your cycle report:
    - All 6 numbered steps with exact action descriptions
    - subreddit.search() parameters: sort="relevance", time_filter="year", limit=25
    - 90-day post recency filter logic (how to classify a post as within 90 days)
    - Top-10 post selection for LLM input (sorted by upvotes descending, n=10)
    - LLM demand intent parse template path: stage06_reddit/reddit_demand_parse.j2
    - signal_json payload shape: post_count_90d, demand_intent_score, intent_phrases,
      subreddits_searched
    - Checkpoint file path: data/checkpoints/{run_id}/stage06_reddit_{niche_id}.json
    - Full error handling table: inaccessible subreddit (skip + log), private subreddit (skip),
      TooManyRequests / 429 (sleep 60s + continue), LLM failure (return null, confidence -0.05)
    - Pacing config key: "reddit_api", base 2s + jitter 0-1s, max 60/hour
2.2 Read in full: src/collection/workflows/reddit_signals.py
    Document all existing helpers (build_subreddit_search_url, parse_reddit_post_count_90d,
    select_top_posts_for_llm, build_reddit_demand_signal_json) — understand their signatures
    and expected inputs/outputs.
2.3 Read: src/models/external_signal.py — confirm SIGNAL_REDDIT_DEMAND constant value
    and write_external_signal() full signature including all parameters.
2.4 Read SCRUM-152 full AC/DoD in Jira. Post planning comment:
    "Cycle 029 Agent D: implementing W7 real praw path. praw.Reddit from env vars.
    Subreddit search loop, 90-day filter, top-10 LLM input, niche-scoped signal writes,
    checkpoint after niche completes. 14 AsyncMock tests."

## TASK 3 [LARGE] — praw Dependency Verification, Environment Variable Setup, and Config Documentation
Ensure praw is installable, credentials are documented, and the config reflects Reddit support.
Sub-tasks:
3.1 Check pyproject.toml [project].dependencies for praw. If missing, add: "praw>=7.7,<8.0"
3.2 Check .env.example. If REDDIT_* entries missing, add:
      REDDIT_CLIENT_ID=your_reddit_client_id_here
      REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
      REDDIT_USER_AGENT=FiverrResearchSystem/0.1
3.3 Check config.yaml.example (or config.yaml). If reddit section missing, add:
      reddit:
        enabled: false            # set true when credentials are configured
        max_posts_per_seed: 25    # matches praw search limit per call
3.4 Run: python -c "import praw; print(praw.__version__)"
    Must succeed without ImportError. If praw just added to pyproject.toml, install it:
    pip install "praw>=7.7,<8.0" --break-system-packages
3.5 Confirm: grep -r "REDDIT_CLIENT_ID" src/ → must return only references to
    os.environ["REDDIT_CLIENT_ID"] or os.getenv, NEVER a hardcoded value.

## TASK 4 [LARGE] — Create LLM Jinja2 Template for Reddit Demand Intent Parse
Build the prompt template that converts Reddit top posts into a demand intent score.
Sub-tasks:
4.1 Create directory if it does not exist: src/llm/templates/stage06_reddit/
4.2 Create: src/llm/templates/stage06_reddit/reddit_demand_parse.j2
    Template must include:
    - System prompt: role as Fiverr market demand analyst
    - User prompt: renders niche_name + top_posts as structured list
      (each post: title, body_snippet, upvotes)
    - Scoring guide embedded in prompt:
        0 = no discussion of needing this type of service
        5 = moderate interest, some "looking for" or "can someone help" language
        10 = strong commercial buyer demand, explicit "hire / pay / looking for service"
    - Output schema instruction: respond ONLY with valid JSON, no preamble:
      {"demand_intent_score": 0-10, "intent_phrases": ["phrase 1", "phrase 2"]}
4.3 Verify template: run a test render call using the project's template renderer.
    Confirm it produces a non-empty string without errors.
4.4 Document the template path in your cycle report.

## TASK 5 [XLARGE] — Implement _llm_reddit_demand_parse() Function with Cache and Null Fallback
Build the async function that calls gpt-4o-mini to score Reddit post demand intent.
Sub-tasks:
5.1 Add to reddit_signals.py:
      async def _llm_reddit_demand_parse(
          top_posts: list[dict], niche_id: str, llm_client: Any, cache: Any
      ) -> tuple[float | None, list[str]]:
          """W7 Step 5: parse top Reddit posts for demand intent. Returns (None, []) on failure."""
          if not top_posts or llm_client is None:
              return None, []
          post_titles = [p["title"] for p in top_posts]
          cache_key = "reddit_intent_v1:" + hashlib.sha256(
              (niche_id + str(post_titles)).encode()).hexdigest()
          if cache:
              cached = await cache.get(cache_key)
              if cached:
                  return cached["demand_intent_score"], cached["intent_phrases"]
          from src.llm.templates import render_template
          prompt = render_template("stage06_reddit/reddit_demand_parse.j2",
                                   niche_name=niche_id, top_posts=top_posts)
          try:
              resp = await llm_client.complete(prompt, model="gpt-4o-mini",
                                               response_format={"type": "json_object"})
              data = json.loads(resp)
              score = min(10.0, max(0.0, float(data.get("demand_intent_score", 0))))
              phrases = [p for p in data.get("intent_phrases", []) if isinstance(p, str)]
              if cache:
                  await cache.set(cache_key,
                      {"demand_intent_score": score, "intent_phrases": phrases})
              return score, phrases
          except Exception as exc:
              # Spec: store null, apply confidence deduction -0.05
              logger.warning("Reddit LLM demand parse failed niche=%s: %s", niche_id, exc)
              return None, []
5.2 Run: python -m ruff check src/collection/workflows/reddit_signals.py → clean.
5.3 Run: python -m mypy src/collection/workflows/reddit_signals.py → clean.

## TASK 6 [LARGE] — Implement _resolve_keyword_id() Scoped to Niche (Anti-Cross-Niche Pattern)
Implement the niche-scoped keyword ID lookup following the Cycle 028 Codex Fix #1 pattern.
Sub-tasks:
6.1 Add to reddit_signals.py:
      def _resolve_keyword_id(keyword_text: str, niche_id: str, db: Any) -> int | None:
          """Lookup keyword_id by BOTH text AND niche_id. Prevents cross-niche signal writes.
          Pattern established by Cycle 028 Codex Fix #1 in google_trends.py."""
          from sqlalchemy.orm import Session
          from src.models import Keyword
          if not isinstance(db, Session):
              return None
          kw = db.query(Keyword).filter(
              Keyword.keyword_text == keyword_text,
              Keyword.niche_id == niche_id,
          ).first()
          return kw.id if kw else None
6.2 Write 2 unit tests to confirm scoped behavior:
      test_resolve_reddit_keyword_id_scoped_to_niche — same keyword text in 2 niches →
        returns correct ID only for the queried niche, not the other
      test_resolve_reddit_keyword_id_returns_none_when_missing — keyword not in DB → None

## TASK 7 [XLARGE] — Implement run_reddit_signals_collection() Real praw: Auth, Accessibility Check, and Search Loop
Replace the NotImplementedError with real praw Reddit authentication and the per-subreddit
per-seed search loop.
Sub-tasks:
7.1 In the non-dry path of run_reddit_signals_collection(), replace NotImplementedError:
      import praw, os
      reddit = praw.Reddit(
          client_id=os.environ["REDDIT_CLIENT_ID"],
          client_secret=os.environ["REDDIT_CLIENT_SECRET"],
          user_agent=os.environ.get("REDDIT_USER_AGENT", "FiverrResearchSystem/0.1"),
      )
7.2 Implement subreddit accessibility check per spec Step 1a:
      subreddits_accessed: list[str] = []
      all_posts: list[dict] = []
      for subreddit_name in subreddits:
          try:
              _ = reddit.subreddit(subreddit_name).id  # raises PrawcoreException if inaccessible
          except Exception as exc:
              logger.warning("Subreddit %s inaccessible: %s", subreddit_name, exc)
              continue
          subreddits_accessed.append(subreddit_name)
7.3 Implement per-seed search loop for each accessible subreddit per spec Steps 1b-1d:
      for seed in seed_keywords:
          try:
              results = reddit.subreddit(subreddit_name).search(
                  seed, sort="relevance", time_filter="year", limit=25
              )
              for post in results:
                  all_posts.append({
                      "title": post.title,
                      "body_snippet": (post.selftext or "")[:200],
                      "upvotes": post.score,
                      "created_utc": post.created_utc,
                      "subreddit": subreddit_name,
                  })
              await pacing_manager.wait("reddit_api", dry_run=False)
          except Exception as exc:
              if "429" in str(exc) or "toomany" in str(exc).lower():
                  import asyncio
                  await asyncio.sleep(60)
                  continue
              logger.warning("Reddit search %s/%s failed: %s", subreddit_name, seed, exc)

## TASK 8 [XLARGE] — Implement W7 Completion: 90d Count, LLM Parse, Signal Write, Checkpoint, Result
Complete the second half of the workflow: compute stats, run LLM parse, write signals per
keyword, write checkpoint, and return the complete result dict.
Sub-tasks:
8.1 After the search loop, compute 90-day post count using the existing helper:
      post_count_90d = parse_reddit_post_count_90d(all_posts)
8.2 Select top posts for LLM input:
      top_posts = select_top_posts_for_llm(all_posts, n=10)
8.3 Run LLM demand intent parse:
      demand_intent_score, intent_phrases = await _llm_reddit_demand_parse(
          top_posts, niche_id, llm_client, cache)
8.4 Build signal JSON using existing helper:
      signal_json = build_reddit_demand_signal_json(
          post_count_90d, demand_intent_score, intent_phrases, subreddits_accessed)
8.5 Write external_signals rows — one per seed keyword, niche-scoped:
      signals_written = 0
      for seed in seed_keywords:
          keyword_id = _resolve_keyword_id(seed, niche_id, db)
          if keyword_id:
              write_external_signal(
                  keyword_id=keyword_id, signal_type=SIGNAL_REDDIT_DEMAND,
                  signal_value=demand_intent_score, signal_json=signal_json,
                  run_id=run_id, collection_method="reddit_api", db=db)
              signals_written += 1
8.6 Write checkpoint per spec (after full niche Reddit collection completes):
      if checkpoint_manager:
          await checkpoint_manager.write(run_id, f"stage06_reddit_{niche_id}",
              {"niche_id": niche_id, "posts_collected": len(all_posts),
               "signals_written": signals_written})
8.7 Update run_reddit_signals_collection() signature to accept llm_client, cache,
    checkpoint_manager as optional parameters (default None).
8.8 Return complete result dict with all metrics.

## TASK 9 [XLARGE] — Write Complete Unit Test Suite for Workflow 7 Real praw Implementation
Write all required tests using AsyncMock and MagicMock — no real praw calls in tests.
Sub-tasks:
9.1 Add to tests/unit/test_reddit_signals.py (minimum 14 new tests):
      test_reddit_real_checks_subreddit_accessibility
        — mock sub.id call verifies the accessibility check runs
      test_reddit_real_inaccessible_subreddit_skipped
        — mock sub.id raises → subreddit skipped, warning logged, search not called
      test_reddit_real_searches_per_seed
        — mock .search called once per seed per accessible subreddit
      test_reddit_real_handles_429
        — mock search raises TooManyRequests → asyncio.sleep(60), loop continues
      test_reddit_real_calls_pacing_wait
        — pacing_manager.wait("reddit_api", dry_run=False) called after each search
      test_reddit_real_collects_post_fields
        — mock post with title/selftext/score/created_utc → all fields collected correctly
      test_reddit_real_computes_90d_count
        — parse_reddit_post_count_90d called with all_posts after loop
      test_reddit_real_selects_top_10_for_llm
        — select_top_posts_for_llm called with n=10
      test_reddit_real_calls_llm_demand_parse
        — mock llm_client → demand_intent_score present in final result
      test_reddit_real_writes_signal_per_keyword
        — write_external_signal called once per seed keyword with resolved keyword_id
      test_reddit_real_scoped_keyword_lookup
        — _resolve_keyword_id called with niche_id → no cross-niche writes
      test_llm_reddit_demand_parse_cache_hit
        — cached result → no LLM call made
      test_llm_reddit_demand_parse_api_error
        — llm_client.complete raises → returns (None, [])
      test_reddit_real_writes_checkpoint
        — checkpoint_manager.write called after collection completes
9.2 Run: python -m pytest -q tests/unit/test_reddit_signals.py --no-header
    All tests must pass. Record count.

## TASK 10 [XLARGE] — R-092 Tier 2: Comprehensive Full Validation Block and Per-Module Coverage Audit
You are the ONLY agent who runs this. Run the complete validation suite and audit every
module touched this cycle.
Sub-tasks:
10.1 Run the full validation block:
       python -m ruff check .
       python -m mypy src
       python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
       python run.py config-check
       python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle029.db
       python run.py phase2-smoke
       python run.py collect-only
     Record every result. Any failure is a BLOCKER — resolve before proceeding to Task 11.
10.2 Run per-module patch coverage audit for every module touched this cycle:
       python -m pytest -q --cov=src.collection.workflows.seller_profile --cov-report=term-missing
       python -m pytest -q --cov=src.collection.fiverr_selectors --cov-report=term-missing
       python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing
       python -m pytest -q --cov=src.collection.workflows.reddit_signals --cov-report=term-missing
       python -m pytest -q --cov=src.scoring.orchestrator --cov-report=term-missing
10.3 Document per-module results in your cycle report:
     module → coverage % → list of any uncovered lines.

## TASK 11 [LARGE] — Gap Tests: Close Any Module Below 90% Patch Coverage
Write targeted tests for every uncovered line identified in Task 10 until all modules >= 90%.
Sub-tasks:
11.1 For each module showing < 90%: list every uncovered line by number.
11.2 Write specific tests targeting those exact lines/branches.
11.3 Re-run that module's targeted coverage after each test addition.
11.4 Repeat until all modules reach >= 90%.
11.5 Re-run the full suite: python -m pytest -q --cov=src --cov-fail-under=90
     Record the CANONICAL final test count and global coverage % — these are the
     numbers that go in the merge gate checklist.

## TASK 12 [LARGE] — Live Jira Board Reconciliation: Verify All Expected Story Statuses
Sub-tasks:
12.1 Query live Jira via Atlassian MCP or REST API. Check actual current status of:
     SCRUM-517 (Cycle 028 control) → must be Done
     SCRUM-518 (Cycle 029 control) → must be In Progress
     SCRUM-17 (E02 Collection epic) → In Progress
     SCRUM-19 (E04 Scoring epic) → In Progress
     SCRUM-20 (E05 Recommendations epic) → In Progress
     SCRUM-25 (E10 Integration epic) → In Progress
     SCRUM-147 (W2 Keyword Expansion) → In Progress
     SCRUM-150 (W5 Seller Profile) → In Progress
     SCRUM-152 (W7 Reddit Signals) → In Progress
     SCRUM-231 (E10 E2E Pipeline) → In Review
12.2 For any status that does NOT match expected: transition it to correct state.
12.3 Document every key: "[SCRUM-XXX] verified as [STATUS] — match / corrected to [STATUS]"

## TASK 13 [LARGE] — Epic Progress Comments and SCRUM-152 Story Evidence Posts
Sub-tasks:
13.1 Post SCRUM-152 implementation evidence comment:
     "Cycle 029 Agent D: Workflow 7 real praw implementation complete.
     praw.Reddit authenticated via REDDIT_CLIENT_ID/SECRET env vars. Subreddit
     accessibility check prevents private/banned sub errors. Per-seed search
     (sort=relevance, time_filter=year, limit=25). TooManyRequests handled with
     60s sleep. 90-day post count computed. Top-10 by upvotes selected for LLM.
     LLM demand intent parse via stage06_reddit/reddit_demand_parse.j2 (gpt-4o-mini,
     cached). Niche-scoped keyword lookup prevents cross-niche signal writes (Codex
     Fix #1 pattern). Writes SIGNAL_REDDIT_DEMAND to external_signals per keyword.
     Checkpoint written after niche completes. 14 AsyncMock tests.
     DoD remaining: real REDDIT_CLIENT_ID/SECRET configured in .env, live subreddit
     validation run."
13.2 Post SCRUM-17 (E02 Collection epic) progress comment:
     "Cycle 029: W5 Seller Profile real Playwright (Agent A), W2 Steps 2c/2d/2f LLM
     keyword gen/relevance/intent (Agents B+C), W7 Reddit real praw (Agent D).
     Current workflow status: W1/W3/W4/W6 fully real; W5 real (selectors unvalidated);
     W2 partial (2a needs auth, 2g deferred); W7 real (credentials needed)."
13.3 Post SCRUM-231 (E10 E2E) progress comment noting collection substantially real.
13.4 Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md — add Cycle 029 Agent D rows for
     SCRUM-152 and all Jira keys reconciled in Task 12.

## TASK 14 [LARGE] — Scoped Commit, PR #33 Creation, and CI Monitoring
Sub-tasks:
14.1 Stage ONLY Agent D scope files:
       git add src/collection/workflows/reddit_signals.py
       git add src/llm/templates/stage06_reddit/
       git add pyproject.toml
       git add .env.example
       git add tests/unit/test_reddit_signals.py
       git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md
       git add docs/cycle_reports/CYCLE_029_AGENT_D.md
     Also add any gap test files created in Task 11 (if separate files).
14.2 git diff --cached --name-only → verify only Agent D scope appears. Remove extras.
14.3 Commit:
       git commit -m "feat(collection): Workflow 7 Reddit real praw + R-092 comprehensive audit [Agent D Cycle 029]"
14.4 Create PR #33:
       gh pr create --base develop --head cycle/029/integration \
         --title "feat(cycle-029): W5 Seller real, W2 Steps 2c+2d+2f LLM, W7 Reddit real, auto-recommendation"
     PR body must include: all 4 agents' deliverables, Jira keys
     (SCRUM-518, SCRUM-147, SCRUM-150, SCRUM-152, SCRUM-20, SCRUM-231),
     full changed files list, validation results from Task 10,
     per-story AC/DoD reference table, guardrails section.
14.5 Monitor ALL CI checks until fully settled.
     codecov/patch MUST show SUCCESS. If FAILURE: add gap tests, push, re-check CI.
     DO NOT proceed to Task 15 until every check shows SUCCESS.

## TASK 15 [LARGE] — Mandatory Codex Disposition: Query, Classify, Fix VALID_FIXED, Reply All, Resolve All
Sub-tasks:
15.1 Run the EXACT Codex GraphQL query for PR #33 (required G-003):
     gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=33
     Document the raw JSON result verbatim in your cycle report.
15.2 For each thread found, classify and act:
     VALID_FIXED: implement the fix in source, write a regression test proving it is fixed,
       commit + push, wait for CI to re-pass, then reply to thread with EXACT format:
         "Disposition: VALID_FIXED
          Decision: [description of what was wrong and what you fixed]
          Evidence: File: [path/to/file.py]; Test: [test_name]; Commit: [SHA]
          Resolution: Fixed with regression coverage and pushed."
       Then call resolveReviewThread GraphQL mutation to close the thread.
     VALID_INTENDED: reply explaining why the pattern is intentional + resolve.
     INVALID: reply explaining why the finding does not apply + resolve.
15.3 If 0 threads: document "Codex query PR #33: 0 review threads confirmed.
     No disposition required."
15.4 Re-run the Codex query after all actions to confirm every thread shows isResolved=true.
     Document the re-check result.

## TASK 16 [LARGE] — Final Steward: SHA Freeze, Artifact Hygiene, Merge Gate Checklist, Merge Recommendation
Sub-tasks:
16.1 Freeze final SHA: git rev-parse origin/cycle/029/integration
     Record this canonical SHA in your cycle report.
16.2 Confirm all 4 cycle reports are present:
     Test-Path "docs\cycle_reports\CYCLE_029_AGENT_A.md" → True
     Test-Path "docs\cycle_reports\CYCLE_029_AGENT_B.md" → True
     Test-Path "docs\cycle_reports\CYCLE_029_AGENT_C.md" → True
     Test-Path "docs\cycle_reports\CYCLE_029_AGENT_D.md" → True
16.3 Final artifact hygiene: git status --short
     Confirm NOT staged: .env, data/sessions/, *.db, coverage.xml.
     git branch --show-current → cycle/029/integration.
16.4 Create docs/cycle_reports/CYCLE_029_AGENT_D.md with ALL sections:
     - Task 1 baseline test count and coverage
     - Task 2 spec extraction summary
     - Task 10 per-module coverage results table
     - Task 11 gap tests added (list)
     - Task 12 Jira reconciliation results
     - Task 15 Codex query raw result + disposition table
     - Canonical final test count and coverage %
     - Final SHA
16.5 Post SCRUM-518 final steward summary comment:
     "Cycle 029 complete. All 4 agents on-scope. W5 Seller real, W2 LLM Steps 2c/2d/2f,
     W7 Reddit real praw, auto-recommendation trigger. PR #33 created. CI: [all pass].
     codecov/patch: [%]. Codex: [N threads, all resolved]. Merge gate: ALL PASS/YES."
16.6 Fill EXACTLY this merge gate checklist in your cycle report AND post it as a PR #33
     comment (required G-004 — every item must show PASS or YES before recommending merge):

MERGE GATE CHECKLIST — Cycle 029 PR #33
==========================================
CODECOV:
[ ] codecov/project: [PASS/FAIL] — [exact %]
[ ] codecov/patch: [PASS/FAIL] — [exact %]
[ ] Local --cov-fail-under=90: [PASS/FAIL]
[ ] All new lines covered by tests: [YES/NO]
  If NO, uncovered files: [list or N/A]

CODEX:
[ ] reviewThreads query executed: YES
[ ] Total threads found: [N]
[ ] All threads dispositioned: [YES/N/A]
[ ] All VALID_FIXED threads have regression tests: [YES/N/A]
[ ] All threads manually resolved with reply: [YES/N/A]
[ ] Zero unresolved threads: [YES]

FINAL:
[ ] PR #33 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]

If any item shows FAIL or NO: fix the blocker, push, re-check CI, re-run Codex query,
then re-fill the checklist before recommending merge.
Final statement must be either:
  "PR #33 is ready to merge when approved."
OR
  "PR #33 is NOT ready to merge. Blockers: [explicit list]"

====================================================================
END AGENT D — 16 LARGE–XLARGE TASKS
====================================================================
