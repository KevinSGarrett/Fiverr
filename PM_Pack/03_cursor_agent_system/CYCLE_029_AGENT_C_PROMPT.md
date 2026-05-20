====================================================================
AGENT C — CYCLE 029 PROMPT
16 LARGE–XLARGE tasks, each with embedded sub-tasks
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch: cycle/029/integration
- Python 3.11+ | openai gpt-4o-mini | SQLAlchemy 2.0

## PM VERIFIED STATE (2026-05-19)
- keyword_expansion.py Step 2f (LLM intent classification) = feature-flag stub (False)
- Intent classes per spec: INFORMATIONAL / CONSIDERATION / HIGH_INTENT / TRANSACTIONAL
- Keyword model has intent_class field (verify before implementing)
- src/scoring/orchestrator.py or equivalent: read actual code before assuming auto-recommendation state
- SCRUM-147 = In Progress. SCRUM-20 (E05 Recommendations) = In Progress. Both live verified.

## ⚠️ HARD GATE RULES (G-001, G-003, G-004 — PERMANENT)

## ⚠️ R-092 COVERAGE RULE
Targeted patch coverage on YOUR modules only. Agent D runs the full audit.

---

## TASK 1 [LARGE] — Preflight, Sync, and Full Agent A+B Work Verification
Sub-tasks:
1.1 Preflight: Get-Location, git branch --show-current (cycle/029/integration),
    git log --oneline -10, git worktree list.
1.2 git pull origin cycle/029/integration — sync all Agent A+B changes.
1.3 Verify Agent B's template files exist:
    Test-Path "src\llm\templates\stage02_keyword_expansion\llm_generate.j2" → True
    Test-Path "src\llm\templates\stage02_keyword_expansion\llm_relevance.j2" → True
    If either is False: document as a gap and proceed with your scope anyway.
1.4 Run: python -m pytest -q tests/unit/test_keyword_expansion.py --no-header
    Record pass count. Document any failures without blocking your tasks.
1.5 Confirm feature flag state in keyword_expansion.py:
    python -c "from src.collection.workflows.keyword_expansion import _FEATURE_FLAGS; print(_FEATURE_FLAGS)"
    Expect step_2c=True, step_2d=True (Agent B set these), step_2f=False (your target).

## TASK 2 [XLARGE] — Full Specification Research: Step 2f Spec, Keyword Model, LLM Patterns, Story AC/DoD
Extract every detail needed before implementing intent classification.
Sub-tasks:
2.1 Read in full: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md
    Workflow 2 Step 2f (LLM Intent Classification). Extract and document:
    - Batch size: max 50 per call
    - 4 exact intent class values: INFORMATIONAL, CONSIDERATION, HIGH_INTENT, TRANSACTIONAL
    - Definitions of each class
    - Output format: classify each keyword into one class
    - Cache requirement: check LLM cache before calling API
    - Failure behavior: "store intent_class = null, apply confidence deduction"
2.2 Read: src/models/ — find the Keyword model. Identify intent_class field.
    Confirm: is the field named intent_class? What is its type (str | None)? Is it nullable?
    Run: python -c "from src.models import Keyword; print(Keyword.intent_class)"
    If field is MISSING: you must add it to the Keyword model with nullable=True before
    any implementation. Document whether you added it.
2.3 Read Agent B's templates to understand the established Jinja2 + LLM pattern.
    Read: src/llm/cache.py and src/llm/client.py (establish the exact async API).
2.4 Read SCRUM-147 current state, note Agent B's planning comment.
    Post your own planning comment for Step 2f scope on SCRUM-147.
2.5 Read SCRUM-20 (E05 Recommendations epic) AC/DoD to understand auto-recommendation gate.

## TASK 3 [LARGE] — Add intent_class Field to Keyword Model if Missing
Ensure the intent_class field exists and can accept classification values.
Sub-tasks:
3.1 If python -c "from src.models import Keyword; print(Keyword.intent_class)" fails:
    Add to the Keyword model (nullable String column):
      intent_class: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)
    Register in __init__.py if needed.
3.2 Run: python run.py init-db to confirm the column is created without errors.
3.3 Run: python -c "from src.models import Keyword; print(Keyword.__table__.columns.intent_class.type)"
    Must print a valid type without error.
3.4 If the field already exists: document it with its current definition and proceed.
3.5 Write 2 model-level tests if you added the field:
    test_keyword_intent_class_field_exists, test_keyword_intent_class_nullable

## TASK 4 [LARGE] — Create Jinja2 Template for Step 2f — LLM Intent Classification
Sub-tasks:
4.1 Create: src/llm/templates/stage02_keyword_expansion/llm_intent.j2
    Template requirements per spec Step 2f:
      - System prompt: role as Fiverr keyword intent analyst
      - Definitions for all 4 classes:
        * INFORMATIONAL: "how to", "what is", educational/research intent
        * CONSIDERATION: comparison, "best for X", "vs", evaluation intent
        * HIGH_INTENT: "hire", "service", "freelance", "build me" — direct service seeking
        * TRANSACTIONAL: specific Fiverr commercial intent ("Fiverr X", "buy X service")
      - User prompt: renders niche_name + numbered list of up to 50 keywords
      - Output schema: {"results": [{"keyword": "...", "intent_class": "INFORMATIONAL|CONSIDERATION|HIGH_INTENT|TRANSACTIONAL"}]}
      - Instruction: output ONLY valid JSON, no preamble
4.2 Verify template exists and can be rendered: test with a simple render call.
4.3 Validate that the 4 intent class values exactly match the spec strings.

## TASK 5 [XLARGE] — Implement _llm_classify_intent() with Batching, Cache, and Null Fallback
Build the async function that maps each keyword to its intent classification.
Sub-tasks:
5.1 Add to keyword_expansion.py:
      async def _llm_classify_intent(
          niche_id: str, keywords: list[str], llm_client: Any, cache: Any
      ) -> dict[str, str | None]:
          """Step 2f: LLM intent classification. Returns {kw: intent_class | None} per spec."""
          VALID_CLASSES = {"INFORMATIONAL", "CONSIDERATION", "HIGH_INTENT", "TRANSACTIONAL"}
          result: dict[str, str | None] = {}
          if not keywords or llm_client is None:
              return {kw: None for kw in keywords}
          for i in range(0, len(keywords), 50):
              batch = keywords[i:i + 50]
              cache_key = "intent_v1:" + hashlib.sha256((niche_id + str(sorted(batch))).encode()).hexdigest()
              if cache:
                  cached = await cache.get(cache_key)
                  if cached is not None:
                      result.update(cached)
                      continue
              prompt = render_template("stage02_keyword_expansion/llm_intent.j2",
                                       niche_name=niche_id, keywords=batch)
              try:
                  response = await llm_client.complete(
                      prompt, model="gpt-4o-mini",
                      response_format={"type": "json_object"}
                  )
                  data = json.loads(response)
                  batch_map = {
                      r["keyword"]: r["intent_class"]
                      for r in data.get("results", [])
                      if r.get("intent_class") in VALID_CLASSES
                  }
                  for kw in batch:
                      if kw not in batch_map:
                          batch_map[kw] = None
                          logger.warning("Intent null for kw=%s niche=%s — confidence deduction applies", kw, niche_id)
              except Exception as exc:
                  logger.warning("LLM intent classification failed niche=%s: %s", niche_id, exc)
                  batch_map = {kw: None for kw in batch}
              if cache:
                  await cache.set(cache_key, batch_map)
              result.update(batch_map)
          return result
5.2 Run ruff + mypy on keyword_expansion.py → clean.

## TASK 6 [LARGE] — Wire Step 2f into run_keyword_expansion() and Update Feature Flag
Sub-tasks:
6.1 In run_keyword_expansion() non-dry path, after Step 2d relevance filter completes:
      if _FEATURE_FLAGS["step_2f_llm_intent_classification"]:
          intent_map = await _llm_classify_intent(niche_id, filtered_keywords, llm_client, cache)
      else:
          intent_map = {}
6.2 When writing Keyword rows to the DB, set intent_class from the map:
      keyword_row.intent_class = intent_map.get(keyword_text, None)
6.3 Update _FEATURE_FLAGS: step_2f_llm_intent_classification = True
6.4 Ensure the llm_client and cache params are already in run_keyword_expansion() signature
    (Agent B added them in Task 9). If not: add them now as optional (default None).
6.5 Verify dry_run=True path is completely unchanged by running existing dry_run tests.

## TASK 7 [LARGE] — Write Complete Unit Test Suite for Step 2f Intent Classification
Sub-tasks:
7.1 Add to tests/unit/test_keyword_expansion.py (minimum 8 new tests):
      test_llm_classify_intent_returns_dict_mapping
      test_llm_classify_intent_batches_50
      test_llm_classify_intent_cache_hit
      test_llm_classify_intent_invalid_class_becomes_null
      test_llm_classify_intent_api_error_returns_null_map
      test_run_expansion_step2f_sets_intent_on_db_keywords
      test_run_expansion_step2f_flag_false_no_classification
      test_llm_classify_intent_missing_kw_in_response_becomes_null
7.2 Run: python -m pytest -q tests/unit/test_keyword_expansion.py -k "intent" --no-header
    All 8 tests must pass.

## TASK 8 [XLARGE] — Read and Analyse Scoring Orchestrator for Auto-Recommendation Integration Point
Mandatory research before any scoring code is touched.
Sub-tasks:
8.1 Read ALL of the following files in full:
    - src/scoring/orchestrator.py (or src/scoring/__init__.py)
    - src/recommendations/eligibility.py
    - src/recommendations/engine.py
    - src/scoring/composite.py (if it exists)
8.2 Document in your cycle report EXACTLY:
    - Which function computes the final GO/NO-GO tag
    - What the tag values are (exact strings)
    - Whether any auto-recommendation trigger already exists
    - The exact call stack from run.py → scoring → tag assignment
8.3 If trigger ALREADY EXISTS: document completely, note "already wired — no changes needed",
    skip Tasks 9-10.
8.4 Identify the EXACT insertion point for the trigger.

## TASK 9 [XLARGE] — Implement Auto-Recommendation Trigger for STRONG_GO and CONDITIONAL_GO Keywords
Only implement if Task 8 confirmed trigger does NOT already exist.
Sub-tasks:
9.1 At the insertion point from Task 8, add:
      if final_tag in ("STRONG_GO", "CONDITIONAL_GO"):
          _auto_config = config.get("recommendations", {}) if isinstance(config, dict) else {}
          if _auto_config.get("auto_generate", True):
              try:
                  from src.recommendations.engine import generate_recommendation
                  await generate_recommendation(keyword_id=keyword_obj.id, db=db,
                                                 llm_client=llm_client, cache=cache)
              except Exception as exc:
                  logger.warning("Auto-recommendation failed keyword=%s tag=%s: %s",
                                 keyword_obj.id, final_tag, exc)
9.2 Add to config.yaml.example:
      recommendations:
        auto_generate: true
9.3 Run: python -m ruff check + python -m mypy on orchestrator.py → clean.
9.4 Run: python run.py phase2-smoke → must still pass.

## TASK 10 [LARGE] — Write Unit Tests for Auto-Recommendation Trigger
Sub-tasks:
10.1 Create tests/unit/test_scoring_auto_recommend.py (minimum 6 tests):
       test_score_keyword_strong_go_triggers_recommendation
       test_score_keyword_conditional_go_triggers_recommendation
       test_score_keyword_no_go_does_not_trigger
       test_score_keyword_auto_generate_disabled
       test_score_keyword_recommendation_exception_does_not_crash_scoring
       test_score_keyword_trigger_is_idempotent
10.2 Run: python -m pytest -q tests/unit/test_scoring_auto_recommend.py --no-header
     All tests must pass.

## TASK 11 [LARGE] — Targeted Patch Coverage Audit for All Agent C Changed Modules (R-092 Tier 1)
Sub-tasks:
11.1 python -m pytest -q --cov=src.collection.workflows.keyword_expansion --cov-report=term-missing tests/unit/test_keyword_expansion.py
11.2 python -m pytest -q --cov=src.scoring.orchestrator --cov-report=term-missing
11.3 For any module < 90%: write gap tests and re-run until >= 90%.
11.4 Document final per-module coverage. DO NOT run full pytest --cov=src.

## TASK 12 [LARGE] — Code Quality: Ruff, Mypy, and Pipeline Verification
Sub-tasks:
12.1 python -m ruff check src/collection/workflows/keyword_expansion.py src/scoring/orchestrator.py tests/unit/test_keyword_expansion.py tests/unit/test_scoring_auto_recommend.py
12.2 python -m mypy src/collection/workflows/keyword_expansion.py src/scoring/orchestrator.py
12.3 python run.py collect-only → must pass.
12.4 python run.py recommendations-only → must pass.

## TASK 13 [LARGE] — Jira Story Advancement: SCRUM-147 Step 2f + SCRUM-20 Auto-Recommendation Evidence
Sub-tasks:
13.1 Post SCRUM-147 evidence: Step 2f complete, template created, _FEATURE_FLAGS step_2f=True,
     8 tests, >= 90% patch. DoD remaining: Steps 2a (auth needed), 2g (embeddings).
13.2 Post SCRUM-20 evidence: auto-recommendation trigger wired, STRONG_GO/CONDITIONAL_GO
     triggers generate_recommendation(), exception-safe, 6 tests.
13.3 Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md — Agent C rows for SCRUM-147 and SCRUM-20.

## TASK 14 [LARGE] — Artifact Hygiene, No-Main Check, and Cycle Report Creation
Sub-tasks:
14.1 git status --short → no .env, *.db, coverage.xml, data/sessions/ staged.
14.2 git branch --show-current → cycle/029/integration. git worktree list → single worktree.
14.3 Create docs/cycle_reports/CYCLE_029_AGENT_C.md with Task 8 orchestrator findings,
     all task results, intent_class field status, test counts, coverage %, final SHA,
     handoff notes for Agent D (W7 Reddit remaining, praw auth needed).

## TASK 15 [LARGE] — Scoped Commit and SHA Freeze
Sub-tasks:
15.1 Stage ONLY Agent C scope:
       git add src/collection/workflows/keyword_expansion.py
       git add src/llm/templates/stage02_keyword_expansion/llm_intent.j2
       git add src/scoring/orchestrator.py
       git add src/models/ (only if intent_class field was added)
       git add tests/unit/test_keyword_expansion.py
       git add tests/unit/test_scoring_auto_recommend.py
       git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md
       git add docs/cycle_reports/CYCLE_029_AGENT_C.md
15.2 git diff --cached --name-only → verify only Agent C scope. Remove extras.
15.3 git commit -m "feat(collection,scoring): Step 2f intent classification + auto-recommendation trigger [Agent C Cycle 029]"
15.4 Record final SHA: git rev-parse HEAD → handoff SHA for Agent D.

## TASK 16 [LARGE] — Read and Document W7 Reddit Spec for Agent D Handoff
Sub-tasks:
16.1 Read: PM_Pack/ref/project_plan/04_collection/COLLECTION_WORKFLOWS.md Workflow 7 (Stage 6b).
16.2 Confirm: praw status in pyproject.toml (present or missing).
16.3 Confirm: REDDIT_CLIENT_ID/SECRET status in .env.example.
16.4 Document in handoff note for Agent D:
     - W7 spec steps 1-6 summary, current reddit_signals.py state,
       praw dependency status, LLM template needed: stage06_reddit/reddit_demand_parse.j2.

====================================================================
END AGENT C — 16 LARGE–XLARGE TASKS
====================================================================
