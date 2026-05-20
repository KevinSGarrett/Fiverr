====================================================================
AGENT A — CYCLE 023 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/023/integration
- Python 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | asyncio | OpenAI | Jinja2
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM
- Prior cycle PR: #26 ready to merge (1083 tests, 93.88%, codecov/patch 95.28% PASS)

## ⚠️ HARD GATE RULES — READ BEFORE ANYTHING ELSE

Rule G-001: codecov/patch ≥ 90% is a HARD merge blocker. Never merge while it fails.
Rule G-003: Codex review query MUST be run for every PR. Classify, fix, reply, resolve ALL threads.
Rule G-004: Agent D must complete the full merge gate checklist. Agent A must check these
  rules are satisfied before recommending Agent D's PR.

## YOUR ROLE
Agent A owns the PR gate, branch setup, and E06 Task 12 — the LLM pricing strategy task
that adds a 12th concurrent LLM task to generate_recommendation(). This extends the
recommendation system to also generate a complete pricing strategy per keyword.

Spec: PM_Pack/ref/project_plan/09_pricing/PRICING_RECOMMENDATIONS_LLM.md (read in full).

## GIT INSTRUCTIONS
1. Verify PR #26: gh pr view 26 --json state,mergeable,statusCheckRollup
   Confirm codecov/project=SUCCESS AND codecov/patch=SUCCESS before merging.
2. gh pr merge 26 --merge (only when both codecov checks show SUCCESS)
3. git checkout develop && git pull --ff-only origin develop
4. git checkout -b cycle/023/integration && git push -u origin cycle/023/integration
5. Commit: feat(pricing): Task 12 LLM pricing strategy and PricingStrategy schema [Agent A Cycle 023]
6. Do NOT push final branch — human operator pushes after all 4 agents complete.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 26 --json state,mergeable,statusCheckRollup
Pass: root = C:\Fiverr\Fiverr. codecov/patch MUST show SUCCESS. Abort if FAILURE.

## TASKS

### Task 1: Preflight and PR #26 verification
Run all 7 preflight commands. Capture FULL statusCheckRollup output.
Explicitly verify: "codecov/patch" conclusion == "SUCCESS".
If codecov/patch shows FAILURE: add tests to uncovered cycle/022 lines, push to
cycle/022/integration, wait for re-check, confirm PASS, then merge.

### Task 2: Codex disposition query for PR #26 (MANDATORY before merge)
Run:
  gh api graphql -f query='query($owner:String!,$name:String!,$number:Int!){repository(owner:$owner,name:$name){pullRequest(number:$number){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:5){nodes{author{login}body}}}}}}}' -f owner=KevinSGarrett -f name=Fiverr -F number=26
Document in your report: "Codex query PR #26: [raw result]. Total threads: [N]."
If threads exist: classify and handle per CODEX_REVIEW_DISPOSITION_PROTOCOL.md.
PR #26 Agent D already dispositioned 2 threads (VALID_FIXED). Verify both show isResolved=true.

### Task 3: Merge PR #26, close SCRUM-511, create branch
- gh pr merge 26 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 1083+, 93.88%+
- git checkout -b cycle/023/integration && git push -u origin cycle/023/integration
- Jira: SCRUM-511 → Done (post merge SHA comment)
- Jira: Create SCRUM-512 as Cycle 023 control → In Progress

### Task 4: Read E06 Task 12 spec before coding (REQUIRED)
Read in full: PM_Pack/ref/project_plan/09_pricing/PRICING_RECOMMENDATIONS_LLM.md
Note: prompt template pricing_strategy.j2, PricingStrategy schema, skip condition,
  integration into generate_recommendation(), updated FIELD_NAMES list (11→12).
Read: src/recommendations/tasks.py (current 11 tasks, understand pattern)
Read: src/llm/prompts/ (check if pricing_strategy.j2 exists from audit PR #16)

### Task 5: Find or note E06 Task 12 Jira story key
Query SCRUM-21 children for S6.6 or "Task 12" or "LLM pricing" story.
If not found: check if story key is SCRUM-192 or nearby. Read full AC/DoD.
Transition to In Progress. Post planning comment.

### Task 6: Create src/schemas/pricing_output.py — PricingStrategy Pydantic schema
Spec: PRICING_RECOMMENDATIONS_LLM.md "Output Schema" section.

Implement exactly as specced:
- EntryPrices (basic, standard, premium, lead_tier, lead_tier_reasoning)
  - validator: standard > basic, premium > standard
- AcquisitionPrices (basic, standard, premium, acquisition_period)
- PriceLadderStep (milestone_reviews, basic, standard, premium, adjustment_rationale)
- PricingRisk (risk, severity, mitigation)
- RecommendedExtra (name, price, rationale)
- ProjectedAOV (at_entry, at_50_reviews, aov_growth_pct)
- PricingStrategy (all 7 fields, price_ladder ≥4 steps, strategy_narrative 100-500 chars,
  recommended_extras 2-4, validator: price ladder prices ascending)

Create: src/schemas/__init__.py (if not exists) exporting PricingStrategy.

### Task 7: Create pricing_strategy.j2 Jinja2 template
Check: does src/llm/prompts/pricing_strategy.j2 exist?
If yes: read and verify it matches PRICING_RECOMMENDATIONS_LLM.md template exactly.
If no: create it based exactly on the spec template.
The template MUST render correctly when given a RecommendationContext with None pricing fields
(all {% if %} guards must handle None gracefully).

### Task 8: Add generate_pricing_strategy() to src/recommendations/tasks.py
Spec: PRICING_RECOMMENDATIONS_LLM.md "generate_pricing_strategy()" function.

Add to tasks.py:
async def generate_pricing_strategy(context, llm_client, cache) -> dict:
  """Task 12: Generate LLM pricing strategy. Skips if no price_distribution in context."""
  if not getattr(context, "price_distribution", None):
    return {"output": None, "cost_usd": 0.0}
  # Render prompt from pricing_strategy.j2
  # Call LLM (gpt-4o, temperature=0.2, response_format=json_object)
  # Parse and validate with PricingStrategy(**parsed["pricing_strategy"])
  # Return {"output": strategy.model_dump(), "cost_usd": result.usage_cost}
  # On exception: return {"output": None, "cost_usd": 0.0}

### Task 9: Update generate_recommendation() to include Task 12
In src/recommendations/tasks.py, update generate_recommendation():
  - Add generate_pricing_strategy(context, llm_client, cache) to the tasks list
  - Update RECOMMENDATION_FIELD_NAMES from 11 to 12 entries, adding "pricing_strategy"
  - Verify existing tests still pass after 12-field change

### Task 10: Write tests for generate_pricing_strategy() and PricingStrategy schema
Create: tests/unit/test_pricing_strategy.py (new file)
Required tests (minimum 12):
- test_pricing_strategy_valid_construction — all fields, no exception
- test_entry_prices_standard_above_basic — validator: standard > basic
- test_entry_prices_premium_above_standard — validator: premium > standard
- test_entry_prices_invalid_order — standard < basic → ValidationError
- test_price_ladder_ascending — price_ladder prices ascending validator
- test_price_ladder_too_few_steps — less than 4 steps → ValidationError
- test_generate_pricing_strategy_no_price_distribution — returns {"output": None, "cost_usd": 0.0}
- test_generate_pricing_strategy_mock_llm — mock LLM returns valid JSON → parsed correctly
- test_generate_pricing_strategy_llm_failure — LLM raises → {"output": None, "cost_usd": 0.0}
- test_generate_pricing_strategy_invalid_json — LLM returns invalid JSON → {"output": None}
- test_generate_recommendation_12_tasks — generate_recommendation returns 12 field keys
- test_field_names_count — RECOMMENDATION_FIELD_NAMES has exactly 12 entries

### Task 11: Run targeted tests
python -m pytest -q tests/unit/test_pricing_strategy.py tests/unit/test_recommendations.py
All must pass. Record counts.

### Task 12: Run targeted patch coverage
python -m pytest -q --cov=src.recommendations.tasks --cov-report=term-missing
python -m pytest -q --cov=src.schemas --cov-report=term-missing
Target: new functions ≥ 90% coverage. Add tests for any uncovered branches.

### Task 13: Run ruff + mypy
python -m ruff check src/recommendations/tasks.py src/schemas/ tests/unit/test_pricing_strategy.py
python -m mypy src/recommendations/tasks.py src/schemas/
Both must pass. Fix all issues.

### Task 14: Run full validation block
python -m ruff check . && python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle023.db
python run.py phase2-smoke
Target: ≥ 1095 tests. Coverage ≥ 90%. All PASS.

### Task 15: Post Jira evidence for E06 Task 12 story
Post: "Cycle 023 Agent A: generate_pricing_strategy() async task 12 implemented.
  PricingStrategy Pydantic schema with price validation. pricing_strategy.j2 template.
  Skip if no price_distribution in context. 12 tests. generate_recommendation() now
  runs 12 concurrent tasks. DoD remaining: real LLM run with real price data."

### Task 16-24: Standard completion tasks
16. Update ACTIVE_STORY_DOD_LEDGER.md (SCRUM-512, E06 Task 12 story, SCRUM-511 Done).
17. Artifact hygiene: no .env, *.db, coverage.xml staged.
18. No-main / worktree check.
19. Record SHA and handoff to Agent B.
20. Create docs/cycle_reports/CYCLE_023_AGENT_A.md.
21. Commit: all scoped files only.
22. Read E07 discovery spec (DISCOVERY_ENGINE_ARCHITECTURE.md) — post planning intent for Agent C.
23. Run python run.py recommendations-only → must pass.
24. Final SHA recorded.

## FILES CREATED THIS CYCLE (Agent A)
| Action | File |
|---|---|
| CREATE | src/schemas/pricing_output.py |
| CREATE | src/schemas/__init__.py |
| MODIFY | src/recommendations/tasks.py |
| CREATE | tests/unit/test_pricing_strategy.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_023_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/schemas/ src/recommendations/tasks.py
git add tests/unit/test_pricing_strategy.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_023_AGENT_A.md
git commit -m "feat(pricing): Task 12 LLM pricing strategy and PricingStrategy schema [Agent A Cycle 023]"
====================================================================
END OF AGENT A PROMPT
====================================================================
