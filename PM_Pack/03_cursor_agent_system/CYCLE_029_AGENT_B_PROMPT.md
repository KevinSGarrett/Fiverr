====================================================================
AGENT B — CYCLE 029 PROMPT
15 LARGE–XLARGE tasks, each with embedded sub-tasks
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/029/integration
- Python 3.11+ | openai gpt-4o-mini | Jinja2 | SQLAlchemy 2.0
- Existing: LLM client at src/llm/client.py, LLM cache at src/llm/cache.py

## PM VERIFIED STATE (2026-05-19)
- keyword_expansion.py: Steps 2b (Google Suggest) + 2e (dedup) are REAL (Cycle 028).
  Steps 2c (LLM keyword gen) and 2d (LLM relevance filter) are feature-flag stubs (False).
  _FEATURE_FLAGS = {"step_2c_llm_generation": False, "step_2d_llm_relevance_filter": False, ...}
- SCRUM-147 "[COLLECTION] S2.7 Keyword Expansion" = In Progress (live verified)
- Spec: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Workflow 2 Steps 2c, 2d

## ⚠️ HARD GATE RULES (G-001, G-003, G-004 — PERMANENT)

## ⚠️ R-092 COVERAGE RULE
Run ONLY targeted patch coverage on YOUR modules. NOT the full suite.
Agent D runs the comprehensive audit.

---

## TASK 1 [LARGE] — Preflight, Agent A Work Verification, and Branch Sync
Ensure the branch is current and Agent A's work is verified before any new implementation.
Sub-tasks:
1.1 Run preflight: Get-Location, git branch --show-current (must be cycle/029/integration),
    git log --oneline -8, git worktree list.
1.2 git pull origin cycle/029/integration to sync Agent A's committed changes.
1.3 Verify Agent A's deliverables exist: Test-Path "src\collection\workflows\seller_profile.py",
    Test-Path "src\collection\fiverr_selectors.py" → both must be True.
1.4 Run: python -m pytest -q tests/unit/test_seller_profile.py --no-header
    Record pass count. If any of Agent A's tests fail: document in your report and continue
    (Agent A's test failures do NOT block your implementation, but note them for Agent D).
1.5 Verify keyword_expansion.py current state:
    python -c "from src.collection.workflows.keyword_expansion import _FEATURE_FLAGS; print(_FEATURE_FLAGS)"
    Confirm step_2c_llm_generation=False and step_2d_llm_relevance_filter=False.

## TASK 2 [XLARGE] — Full Specification Research: Workflow 2 Steps 2c and 2d, LLM Client/Cache Pattern, SCRUM-147 AC/DoD
Extract every detail needed to implement both LLM steps correctly.
Sub-tasks:
2.1 Read in full: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
    Focus on Workflow 2 Steps 2c and 2d. Extract and document in your report:
    Step 2c — LLM Keyword Generation:
      - What to batch (all seeds for this niche in a single prompt)
      - What to generate (10–20 related keywords, long-tail variants, buyer-intent combos per seed)
      - Output format (JSON response → flat keyword list)
      - Cache requirement (check LLM cache before calling API)
      - Failure behavior ("skip LLM-generated keywords for this niche, log warning")
    Step 2d — LLM Relevance Filter:
      - Input (all candidate keywords from 2a+2b+2c combined)
      - Batch size (max 50 per call to avoid token limits)
      - Output format (RELEVANT/IRRELEVANT classification per keyword)
      - Failure behavior ("skip filter (include all keywords), log warning")
2.2 Read in full: src/llm/client.py — document the async complete() method signature,
    what parameters it accepts (prompt, model, response_format), what it returns.
2.3 Read in full: src/llm/cache.py — document get(key) and set(key, value) async API,
    how cache keys are constructed in existing code (look at recommendations/ for examples).
2.4 Read: src/collection/workflows/keyword_expansion.py — document _fetch_google_suggest
    as the pattern to follow for _llm_generate_keywords and _llm_relevance_filter.
2.5 Read SCRUM-147 full AC/DoD. Post planning comment:
    "Cycle 029 Agent B: implementing Steps 2c (LLM keyword generation) and 2d (LLM relevance
    filter). gpt-4o-mini with LLM cache. Batched to 50 per relevance call. Feature flags
    will be set to True on completion."

## TASK 3 [LARGE] — Create Jinja2 Template for Step 2c — LLM Keyword Generation
Build the prompt template that generates long-tail keyword variants from seeds.
Sub-tasks:
3.1 Create directory if needed: src/llm/templates/stage02_keyword_expansion/
3.2 Create: src/llm/templates/stage02_keyword_expansion/llm_generate.j2
    Template requirements per spec Step 2c:
      - System prompt: "You are a Fiverr keyword research expert. Generate keyword
        variants that buyers would type into Fiverr's search bar."
      - User prompt renders: niche_name variable + seeds as a bulleted list
      - Instruction: generate 10–20 long-tail variants per seed, buyer-intent combos,
        modifier phrases (e.g., "for startups", "under $100", "in 24 hours")
      - Output schema instruction: respond with ONLY valid JSON, no preamble:
        {"keywords": [{"text": "...", "intent_hint": "buyer|informational"}]}
3.3 Verify the template file exists and is non-empty.
    Attempt a test render using the project's template renderer to confirm no syntax errors.
3.4 Run: python -m ruff check src/llm/templates/ (if ruff checks .j2 — skip if not applicable).

## TASK 4 [XLARGE] — Implement _llm_generate_keywords() Function with Cache and Error Handling
Build the async function that calls gpt-4o-mini to generate keyword variants per niche.
Sub-tasks:
4.1 Add to keyword_expansion.py:
      import hashlib, json
      async def _llm_generate_keywords(
          niche_id: str, seeds: list[str], llm_client: Any, cache: Any, run_id: str
      ) -> list[str]:
          """Step 2c: LLM-based keyword generation. Returns [] on failure per spec."""
          if not seeds or llm_client is None:
              return []
          cache_key = "kw_gen_v1:" + hashlib.sha256((niche_id + str(sorted(seeds))).encode()).hexdigest()
          if cache:
              cached = await cache.get(cache_key)
              if cached:
                  return cached
          from src.llm.templates import render_template  # adjust import to actual renderer path
          prompt = render_template("stage02_keyword_expansion/llm_generate.j2",
                                   niche_name=niche_id, seeds=seeds)
          try:
              response = await llm_client.complete(
                  prompt, model="gpt-4o-mini",
                  response_format={"type": "json_object"}
              )
              data = json.loads(response)
              keywords = [
                  item["text"].strip() for item in data.get("keywords", [])
                  if isinstance(item.get("text"), str) and item["text"].strip()
              ]
          except Exception as exc:
              # Spec: "skip LLM-generated keywords for this niche, log warning"
              logger.warning("LLM keyword generation failed niche=%s: %s", niche_id, exc)
              return []
          if cache and keywords:
              await cache.set(cache_key, keywords)
          return keywords
4.2 Ensure the function signature accepts the llm_client and cache parameters that will
    be threaded through run_keyword_expansion() in Task 9.
4.3 Run: python -m ruff check src/collection/workflows/keyword_expansion.py → must be clean.
4.4 Run: python -m mypy src/collection/workflows/keyword_expansion.py → must pass.

## TASK 5 [LARGE] — Write Complete Unit Test Suite for Step 2c LLM Keyword Generation
Sub-tasks:
5.1 Add to tests/unit/test_keyword_expansion.py (minimum 8 new tests):
      test_llm_generate_keywords_returns_list — mock llm_client returns valid JSON → list of strings
      test_llm_generate_keywords_cache_hit — cache.get returns result → no LLM call made
      test_llm_generate_keywords_cache_miss — cache returns None → LLM called, result cached
      test_llm_generate_keywords_json_decode_error — llm returns malformed JSON → [] returned, no crash
      test_llm_generate_keywords_api_error — llm_client.complete raises Exception → [] returned, warning logged
      test_llm_generate_keywords_empty_seeds — seeds=[] → returns [] without calling LLM
      test_llm_generate_keywords_none_llm_client — llm_client=None → returns [] immediately
      test_llm_generate_keywords_filters_empty_text — JSON contains empty string entries → filtered out
5.2 Run: python -m pytest -q tests/unit/test_keyword_expansion.py -k "llm_gen" --no-header
    All 8 tests must pass. Record count.

## TASK 6 [LARGE] — Create Jinja2 Template for Step 2d — LLM Relevance Filter
Build the prompt template that classifies keywords as RELEVANT or IRRELEVANT to the niche.
Sub-tasks:
6.1 Create: src/llm/templates/stage02_keyword_expansion/llm_relevance.j2
    Template requirements per spec Step 2d:
      - System prompt: establish the niche relevance classification role
      - User prompt renders: niche_name + numbered list of candidate_keywords (max 50)
      - Classification instruction: for each keyword, determine if a Fiverr buyer
        searching this term would be looking for services in this niche
      - Output schema: {"results": [{"keyword": "...", "relevance": "RELEVANT|IRRELEVANT"}]}
      - Strict instruction: output ONLY valid JSON, no preamble, no commentary
6.2 Verify the template file exists and can be rendered without errors.
6.3 Confirm the output schema strictly limits relevance to "RELEVANT" or "IRRELEVANT" —
    any other value returned by the LLM will be treated as RELEVANT (include-all fallback).

## TASK 7 [XLARGE] — Implement _llm_relevance_filter() with Batching, Cache, and Fallback Behavior
Build the async function that filters the combined keyword list to niche-relevant items only.
Sub-tasks:
7.1 Add to keyword_expansion.py:
      async def _llm_relevance_filter(
          niche_id: str, candidates: list[str], llm_client: Any, cache: Any
      ) -> list[str]:
          """Step 2d: LLM relevance filter. Returns all candidates on failure per spec."""
          if not candidates or llm_client is None:
              return candidates
          relevant: list[str] = []
          for i in range(0, len(candidates), 50):  # spec: max 50 per call
              batch = candidates[i:i + 50]
              cache_key = "rel_v1:" + hashlib.sha256((niche_id + str(sorted(batch))).encode()).hexdigest()
              if cache:
                  cached = await cache.get(cache_key)
                  if cached is not None:
                      relevant.extend(cached)
                      continue
              prompt = render_template("stage02_keyword_expansion/llm_relevance.j2",
                                       niche_name=niche_id, candidate_keywords=batch)
              try:
                  response = await llm_client.complete(
                      prompt, model="gpt-4o-mini",
                      response_format={"type": "json_object"}
                  )
                  data = json.loads(response)
                  batch_relevant = [
                      r["keyword"] for r in data.get("results", [])
                      if r.get("relevance") in ("RELEVANT", None)  # unknown = include
                  ]
              except Exception as exc:
                  # Spec: "skip filter (include all keywords), log warning"
                  logger.warning("LLM relevance filter failed niche=%s batch_start=%d: %s", niche_id, i, exc)
                  batch_relevant = list(batch)
              if cache:
                  await cache.set(cache_key, batch_relevant)
              relevant.extend(batch_relevant)
          return relevant
7.2 Verify function handles edge case: empty candidates → returns [] immediately.
7.3 Run: python -m ruff check + python -m mypy on the file.

## TASK 8 [LARGE] — Write Complete Unit Test Suite for Step 2d LLM Relevance Filter
Sub-tasks:
8.1 Add to tests/unit/test_keyword_expansion.py (minimum 7 new tests):
      test_llm_relevance_filter_returns_relevant_only — IRRELEVANT items removed
      test_llm_relevance_filter_batches_50 — 60 candidates → 2 batches (50+10) → 2 LLM calls
      test_llm_relevance_filter_cache_hit — cached batch → no LLM call for that batch
      test_llm_relevance_filter_api_error_fallback — LLM raises → all candidates kept, warning logged
      test_llm_relevance_filter_json_error_fallback — malformed JSON → all candidates kept
      test_llm_relevance_filter_empty_candidates → returns [] without calling LLM
      test_llm_relevance_filter_unknown_relevance_value — LLM returns "MAYBE" → included as RELEVANT
8.2 Run: python -m pytest -q tests/unit/test_keyword_expansion.py -k "relevance" --no-header
    All 7 tests must pass.

## TASK 9 [XLARGE] — Wire Steps 2c and 2d into run_keyword_expansion() Non-Dry Path and Update Feature Flags
Integrate both new functions into the main keyword expansion pipeline.
Sub-tasks:
9.1 Update run_keyword_expansion() function signature to accept llm_client and cache parameters:
      async def run_keyword_expansion(
          niche_id, seeds, depth, run_id, db, session_manager, pacing_manager,
          dry_run=True, llm_client=None, cache=None  # NEW
      ) -> dict
9.2 In the non-dry path, after Step 2b (Google Suggest) completes:
      # Step 2c: LLM keyword generation
      if _FEATURE_FLAGS["step_2c_llm_generation"]:
          llm_keywords = await _llm_generate_keywords(niche_id, seeds, llm_client, cache, run_id)
          combined += llm_keywords
      else:
          llm_keywords = []
      # Step 2d: LLM relevance filter
      if _FEATURE_FLAGS["step_2d_llm_relevance_filter"]:
          combined = await _llm_relevance_filter(niche_id, combined, llm_client, cache)
9.3 Update _FEATURE_FLAGS at module top: step_2c_llm_generation = True, step_2d_llm_relevance_filter = True
9.4 Update return dict to include "llm_generated" count:
      "sources": {
          "fiverr_autocomplete": 0,
          "google_suggest": google_suggest_count,
          "llm_generated": len(llm_keywords),
      }
9.5 Verify dry_run=True path is completely unchanged — it still returns the stub result
    without touching llm_client or cache at all.

## TASK 10 [LARGE] — Integration Tests: Step 2c+2d Wiring in run_keyword_expansion() End-to-End
Sub-tasks:
10.1 Add to tests/unit/test_keyword_expansion.py (minimum 5 new integration tests):
       test_run_expansion_includes_llm_keywords_when_step_2c_enabled — with step_2c=True, mock llm_client → llm_generated count > 0
       test_run_expansion_applies_relevance_filter_when_step_2d_enabled — with step_2d=True, mock filter → irrelevant removed
       test_run_expansion_skips_llm_when_flags_false — step_2c=False, step_2d=False → no LLM calls at all
       test_run_expansion_dry_run_unchanged — dry_run=True → stub result, no LLM calls
       test_run_expansion_llm_failure_does_not_break_pipeline — both LLM steps raise → returns valid result with 0 llm_generated
10.2 Run: python -m pytest -q tests/unit/test_keyword_expansion.py --no-header
     Record total pass count. All tests must pass.

## TASK 11 [LARGE] — Targeted Patch Coverage Audit and Gap Closure for keyword_expansion.py (R-092 Tier 1)
Sub-tasks:
11.1 Run:
       python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing tests/unit/test_keyword_expansion.py
     Record coverage % and every uncovered line number.
11.2 If < 90%: write targeted tests for uncovered branches. Re-run until >= 90%.
11.3 Document: final coverage %, list of any remaining uncovered lines (if acceptable edge paths).
11.4 Verify the template files exist using Test-Path for both .j2 files.
     DO NOT run: python -m pytest --cov=src — that is Agent D's job.

## TASK 12 [LARGE] — Full Code Quality: Ruff, Mypy, and Template Validation
Sub-tasks:
12.1 Run ruff on ALL changed files:
       python -m ruff check src/collection/workflows/keyword_expansion.py tests/unit/test_keyword_expansion.py
     Fix every reported issue.
12.2 Run mypy on implementation files:
       python -m mypy src/collection/workflows/keyword_expansion.py
     Fix all type errors, especially Any annotations on llm_client and cache params.
12.3 Verify template renderer works for both new templates (attempt a render call on each).
12.4 Run: python run.py collect-only → must complete without errors.
     Record pass/fail in report.

## TASK 13 [LARGE] — Jira Story Advancement: SCRUM-147 Evidence, Epic Update, and Ledger Update
Sub-tasks:
13.1 Post implementation evidence on SCRUM-147:
     "Cycle 029 Agent B: Steps 2c and 2d real LLM implementation complete.
     Step 2c: _llm_generate_keywords with gpt-4o-mini + LLM cache. Jinja2 template
     stage02_keyword_expansion/llm_generate.j2. Generates 10-20 long-tail keyword variants
     per seed. JSON cache-keyed per niche+seeds. Graceful failure returns [] per spec.
     Step 2d: _llm_relevance_filter batching to 50 per LLM call. Filters IRRELEVANT
     candidates out. Cache-keyed per batch. Failure returns all candidates per spec.
     _FEATURE_FLAGS: step_2c=True, step_2d=True. 20+ tests, keyword_expansion ≥ 90% patch.
     DoD remaining: Step 2a (Fiverr autocomplete, needs auth session), Step 2f (Agent C)."
13.2 Post SCRUM-17 epic progress: keyword expansion now includes LLM keyword generation + filtering.
13.3 Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md — add Cycle 029 Agent B row for SCRUM-147.

## TASK 14 [LARGE] — Artifact Hygiene, No-Main Check, and Cycle Report Creation
Sub-tasks:
14.1 Artifact hygiene: git status --short → no .env, *.db, coverage.xml, data/sessions/ staged.
14.2 git branch --show-current → cycle/029/integration. git worktree list → single worktree.
14.3 Create docs/cycle_reports/CYCLE_029_AGENT_B.md with:
     - Spec extraction summary (Task 2 findings)
     - Both template paths confirmed
     - Function signatures for _llm_generate_keywords and _llm_relevance_filter
     - Feature flags final state
     - Total test count from Task 10
     - Coverage % from Task 11
     - Final agent SHA
     - Handoff notes for Agent C: LLM client/cache patterns established,
       templates in src/llm/templates/stage02_keyword_expansion/,
       Step 2f (intent classification) is the next remaining stub

## TASK 15 [LARGE] — Scoped Commit and SHA Freeze
Sub-tasks:
15.1 Stage ONLY Agent B scope files:
       git add src/collection/workflows/keyword_expansion.py
       git add src/llm/templates/stage02_keyword_expansion/
       git add tests/unit/test_keyword_expansion.py
       git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md
       git add docs/cycle_reports/CYCLE_029_AGENT_B.md
15.2 git diff --cached --name-only → verify only the above appear. Remove any extra files.
15.3 git commit -m "feat(collection): Workflow 2 Steps 2c+2d real LLM implementation [Agent B Cycle 029]"
15.4 Record final SHA: git rev-parse HEAD → include in cycle report as handoff SHA for Agent C.

====================================================================
END AGENT B — 15 LARGE–XLARGE TASKS
====================================================================
