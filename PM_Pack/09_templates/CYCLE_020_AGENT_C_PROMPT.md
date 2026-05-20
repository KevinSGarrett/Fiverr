====================================================================
AGENT C — CYCLE 020 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: cycle/020/integration (created by Agent A)
- Python: 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | OpenAI | asyncio

## YOUR ROLE
Agent C has two equal-weight responsibilities: (1) wire live LLM calls into the 8 scoring
calculators that currently have stubs, using src/llm/client.py + src/llm/cache.py and a
feature flag, and (2) begin E05 Recommendations Engine implementation with the
RecommendationContext Pydantic model and the first 4 async LLM task executors.

## GIT INSTRUCTIONS
1. Ensure you are on: cycle/020/integration
2. Pull latest: git pull origin cycle/020/integration
3. Read Agent A + B handoff notes before coding
4. All work goes on cycle/020/integration
5. Commit: feat(scoring/recommendations): LLM wiring + E05 foundation [Agent C Cycle 020]
6. Do NOT push — human operator pushes after all agents complete

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location
  git rev-parse --show-toplevel
  git branch --show-current
  git status --short --branch
  git log --oneline -8
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py tests/unit/test_scoring_db_integration.py
Pass: branch = cycle/020/integration, all A+B tests pass.

## TASKS

### Task 1: Preflight + read Agent A/B handoffs + read spec files
Read: docs/cycle_reports/CYCLE_020_AGENT_A.md and CYCLE_020_AGENT_B.md
Read: src/llm/client.py, src/llm/cache.py (understand existing LLM client API)
Read: PM_Pack/ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md (full file)
Read: src/recommendations/ directory (existing scaffold)
Note: how LLMClient.complete() works, what parameters it takes, how cache is used.

### Task 2: Read E04 scoring story Jira keys SCRUM-170 through SCRUM-173 before coding
Query SCRUM-19 children. Read AC/DoD for SCRUM-170 (intent), 171 (saturation), 172 (weakness),
173 (trend). Identify which AC bullets reference LLM integration.
Post planning comments on SCRUM-170, 171, 172, 173.

### Task 3: Read E05 Recommendations Jira story keys before coding
Query SCRUM-20 children for stories S5.1 through S5.4.
Record exact Jira keys. Read full AC/DoD text for each story.
Transition S5.1 through S5.4 from To Do to In Progress.
Post planning comments on each key.

### Task 4: Add feature-flagged LLM integration to src/scoring/intent.py
Add async method: async def _get_llm_intent_class(self, keyword_text: str,
  llm_client, cache) -> str | None:
  - Build prompt using intent classification template or inline prompt
  - Call: response = await llm_client.complete(prompt=..., model="gpt-4o-mini", cache=cache)
  - Parse response: extract INFORMATIONAL / CONSIDERATION / HIGH_INTENT / TRANSACTIONAL
  - Return None on LLM failure (non-crashing)
  - Error path: emit "llm_intent_failed" warning in missing_data_warnings

Modify calculate() to accept optional llm_client=None, cache=None parameters:
  - If llm_client is not None: attempt async LLM call (or run in executor if sync context)
  - If llm_client is None: use existing stub (CONSIDERATION default)
  - Feature flag preserves full backward compatibility

### Task 5: Add feature-flagged LLM integration to src/scoring/saturation_score.py
Add async method: async def _get_llm_saturation(self, keyword_text: str, gig_count: int,
  llm_client, cache) -> float | None:
  - Prompt: "Rate saturation for '{keyword_text}' with {gig_count} gigs. Return a
    number 0-100 where 100 = completely saturated. Respond with only the number."
  - Parse response to float, validate 0-100 range
  - Return None on failure with "llm_saturation_failed" warning
Modify calculate() to accept optional llm_client=None, cache=None.

### Task 6: Add feature-flagged LLM integration to src/scoring/weakness.py
LLM inputs for weakness (8 total — all should be feature-flagged):
  For each LLM-derived component that is currently None with llm_not_implemented warning:
  - Add a private async method: async def _get_llm_[component](..., llm_client, cache)
  - Use model="gpt-4o" for description_quality, weakness_count, package_differentiation,
    niche_specificity (higher quality LLM needed)
  - Use model="gpt-4o-mini" for thumbnail_quality, faq_completeness (simpler tasks)
  - Each method: call llm_client.complete(), parse response, return float|None
Modify calculate() to accept optional llm_client=None, cache=None.

### Task 7: Add feature-flagged LLM integration to src/scoring/trend.py
Add async method: async def _get_llm_trend_class(self, keyword_text: str,
  slope_value: float | None, llm_client, cache) -> str | None:
  - Prompt: "Classify the trend for keyword '{keyword_text}' with slope {slope_value}.
    Respond with exactly one of: STRONGLY_RISING, RISING, STABLE, DECLINING, STRONGLY_DECLINING"
  - Map to numeric: STRONGLY_RISING=100, RISING=75, STABLE=50, DECLINING=25, STRONGLY_DECLINING=0
  - Return None on failure with "llm_trend_failed" warning
Modify calculate() to accept optional llm_client=None, cache=None.

### Task 8: Add LLM wiring tests (tests/unit/test_scoring_llm.py)
Create: tests/unit/test_scoring_llm.py
Use mock/patch for llm_client. Do NOT make real LLM API calls in tests.
Required tests (minimum 16):
- test_intent_with_llm_transactional — mock returns TRANSACTIONAL → score contrib = 100
- test_intent_without_llm_uses_stub — llm_client=None → CONSIDERATION (40) + warning
- test_intent_llm_failure_graceful — mock raises exception → warning emitted, score continues
- test_saturation_with_llm_score — mock returns "75" → llm component = 75
- test_saturation_without_llm_stub — llm_client=None → warning, score from other components
- test_saturation_llm_invalid_response — mock returns "not a number" → graceful None
- test_weakness_collection_inputs_no_llm — video/portfolio rates still compute without LLM
- test_weakness_with_llm_description_quality — mock returns quality score → used in calc
- test_weakness_llm_partial_failure — some LLM tasks fail → score from available inputs
- test_trend_with_llm_strongly_rising — mock returns STRONGLY_RISING → contribution = 100
- test_trend_without_llm_uses_stable — llm_client=None → STABLE (50) + warning
- test_trend_llm_unknown_classification — mock returns unexpected string → None + warning
- test_feature_flag_backward_compat_demand — demand.py unchanged when llm_client=None
- test_feature_flag_backward_compat_competition — competition unchanged without llm_client
- test_llm_cache_used_on_second_call — same keyword+prompt → cache hit (mock verification)
- test_llm_client_none_no_crash_any_calculator — pass llm_client=None to all calculators, no crash

### Task 9: Implement src/recommendations/context.py — RecommendationContext
Spec: PM_Pack/ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md (RecommendationContext section)
Create: src/recommendations/context.py

Implement the full Pydantic model RecommendationContext with all fields from the spec:
  keyword_id, keyword_text, niche_id, niche_name, tag, final_score,
  demand_score, competition_score, opportunity_score, feasibility_score, profitability_score,
  score_components, top_competitor_weaknesses, cluster_synthesis_narrative,
  entry_feasibility_rating, dominant_sellers, positioning_gaps,
  top_buyer_complaints, top_buyer_praise, red_flag_patterns,
  starter_price_basic, starter_price_standard, starter_price_premium, hard_exclusions,
  total_result_count, trends_slope, reddit_intent_score, cluster_label, opportunity_narrative

Implement: build_recommendation_context(keyword_id: int, db, config) -> RecommendationContext
  - Build context from DB queries (keyword, scores, analysis, review data, config)
  - Handle None gracefully for all optional fields
  - Return a valid RecommendationContext even with partial data

### Task 10: Implement src/recommendations/eligibility.py — gating logic
Spec: RECOMMENDATION_ENGINE.md (Eligibility and Gating sections)
Create: src/recommendations/eligibility.py

Implement:
- get_eligible_keywords(run_id: str, db, config) -> list[dict]:
  - Query OpportunityRanking for STRONG_GO/CONDITIONAL_GO keywords
  - Skip niches with recommendation_generation=False in config
  - Return list of keyword dicts
- _tags_at_or_above(min_tag: str) -> list[str]:
  - Returns list of tags from min_tag upward in priority
- passes_recommendation_gates(keyword_data: dict, db) -> tuple[bool, str]:
  - Gate 1: confidence_modifier >= 0.40
  - Gate 2: demand_score >= 20
  - Gate 3: at least one GigQualityScore with analysis_complete=True
  - Gate 4: force_recommended override
- should_regenerate_recommendation(keyword_id: int, current_final_score: float, db) -> bool:
  - Check existing Recommendation with generation_complete=True
  - If score delta > 5.0 → regenerate
  - If newer competitor analysis → regenerate
  - Else return False (skip)

### Task 11: Implement src/recommendations/tasks.py — first 4 async LLM task executors
Spec: RECOMMENDATION_ENGINE.md (LLM Task Execution section)
Create: src/recommendations/tasks.py

Implement as async functions (each takes context: RecommendationContext, llm_client, cache):
- async def generate_gig_titles(context, llm_client, cache) -> dict:
  - Template: src/llm/prompts/gig_titles.j2 (from audit PR #16)
  - Render template with context fields, call llm_client.complete(model="gpt-4o")
  - Return: {"output": list_of_titles, "cost_usd": float}
  - On failure: return {"output": None, "cost_usd": 0.0}

- async def generate_tag_sets(context, llm_client, cache) -> dict:
  - Template: src/llm/prompts/tag_sets.j2
  - Model: gpt-4o-mini
  - Return: {"output": list_of_tag_sets, "cost_usd": float}

- async def generate_differentiation_angle(context, llm_client, cache) -> dict:
  - Template: src/llm/prompts/differentiation_angle.j2
  - Model: gpt-4o (differentiation requires deeper reasoning)
  - Return: {"output": str, "cost_usd": float}

- async def generate_red_flags(context, llm_client, cache) -> dict:
  - Template: src/llm/prompts/red_flags.j2
  - Model: gpt-4o
  - Return: {"output": list_of_red_flags, "cost_usd": float}

Each function must: render Jinja2 template, call LLM, parse output, estimate cost,
return {"output": ..., "cost_usd": float}. None-safe on LLM failure.

### Task 12: Add RecommendationContext tests (tests/unit/test_recommendations.py)
Create: tests/unit/test_recommendations.py
Required tests (minimum 12):
- test_recommendation_context_valid_construction — all required fields, no exception
- test_recommendation_context_optional_fields_none — optional fields default gracefully
- test_build_context_with_mock_db — mock db returns Keyword/scores, context built correctly
- test_get_eligible_keywords_filters_tags — only STRONG_GO/CONDITIONAL_GO returned
- test_passes_gates_confidence_too_low — confidence < 0.40 → (False, reason)
- test_passes_gates_demand_too_low — demand < 20 → (False, reason)
- test_passes_gates_no_gig_analysis — no GigQualityScore → (False, reason)
- test_passes_gates_all_pass — all gates pass → (True, "All gates passed")
- test_should_regenerate_no_existing — no existing recommendation → True
- test_should_regenerate_score_delta — delta > 5 → True
- test_should_regenerate_stable — delta <= 5, no new competitor data → False
- test_gig_titles_task_mock_llm — mock LLM returns titles → output is list

### Task 13: Run targeted tests
  python -m pytest -q tests/unit/test_scoring_llm.py
  python -m pytest -q tests/unit/test_recommendations.py
All must pass. Record counts.

### Task 14: Run full scoring test suite (confirm no regression)
  python -m pytest -q tests/unit/test_scoring.py
  python -m pytest -q tests/unit/test_scoring_pipeline.py
  python -m pytest -q tests/unit/test_scoring_db_integration.py
All must pass. No regression from Agent B changes.

### Task 15: Run ruff + mypy on new modules
  python -m ruff check src/scoring/ src/recommendations/ tests/unit/test_scoring_llm.py tests/unit/test_recommendations.py
  python -m mypy src/scoring/ src/recommendations/
Both must pass. Fix all type errors and linting issues.

### Task 16: Run full validation block
All 6 commands. Total tests >= 920 (848 + A's ~16 + B's ~10 + C's ~28).
Coverage >= 90%. Record in report.

### Task 17: Update src/recommendations/__init__.py exports
Add: RecommendationContext, build_recommendation_context, get_eligible_keywords,
passes_recommendation_gates, should_regenerate_recommendation,
generate_gig_titles, generate_tag_sets, generate_differentiation_angle, generate_red_flags.

### Task 18: Post Jira evidence for SCRUM-170, 171, 172, 173 (E04 LLM wiring)
For each: "Cycle 020 Agent C: Feature-flagged LLM integration added to [file].py.
  Stub fallback preserved (llm_client=None). LLM wiring tests: [count] passing.
  Model: [gpt-4o or gpt-4o-mini]. Status recommendation: Keep In Progress."

### Task 19: Post Jira evidence for E05 S5.1, S5.2, S5.3, S5.4
For each story key: "Cycle 020 Agent C: [story name] implemented in
  src/recommendations/[file].py. Context builder / gating logic / eligibility /
  first 4 LLM task executors complete. Tests: [count]. DoD remaining: full async
  gather + storage + S5.5-S5.9 LLM tasks still needed."

### Task 20: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Agent C rows
Add rows for SCRUM-170-173 (E04 LLM wiring) and E05 S5.1-S5.4 story keys.

### Task 21: Artifact hygiene check and commit
  git status --short — no .env, *.db, coverage.xml staged.
  Commit scope: scoring LLM additions, recommendations/ new files, test files, ledger, report.
  Message: feat(scoring/recommendations): LLM wiring and E05 foundation [Agent C Cycle 020]

### Task 22: No-main / worktree check
  git worktree list → canonical root only. No main changes.

### Task 23: Record SHA and handoff to Agent D
  git rev-parse HEAD → record SHA.
  Handoff: "LLM wiring feature-flagged in 4 calculators. E05 context, eligibility,
  and first 4 task executors built. Agent D: implement remaining E05 tasks + PR."

### Task 24: Create Agent C report at docs/cycle_reports/CYCLE_020_AGENT_C.md
Sections: Preflight, LLM client API summary, design decisions for feature-flag pattern,
E05 context builder design, test counts, validation output, Jira keys, AC/DoD, handoff.

## FILES CREATED THIS CYCLE (Agent C)
| Action | File Path |
|---|---|
| MODIFY | src/scoring/intent.py |
| MODIFY | src/scoring/saturation_score.py |
| MODIFY | src/scoring/weakness.py |
| MODIFY | src/scoring/trend.py |
| CREATE | tests/unit/test_scoring_llm.py |
| CREATE | src/recommendations/context.py |
| CREATE | src/recommendations/eligibility.py |
| CREATE | src/recommendations/tasks.py |
| MODIFY | src/recommendations/__init__.py |
| CREATE | tests/unit/test_recommendations.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_020_AGENT_C.md |

## COMMIT INSTRUCTIONS
git add src/scoring/intent.py src/scoring/saturation_score.py src/scoring/weakness.py src/scoring/trend.py
git add src/recommendations/ tests/unit/test_scoring_llm.py tests/unit/test_recommendations.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_020_AGENT_C.md
git commit -m "feat(scoring/recommendations): LLM wiring and E05 foundation [Agent C Cycle 020]"

====================================================================
END OF AGENT C PROMPT
====================================================================
