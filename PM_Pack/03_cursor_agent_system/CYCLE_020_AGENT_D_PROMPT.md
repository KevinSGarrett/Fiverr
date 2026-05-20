====================================================================
AGENT D — CYCLE 020 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr
- Branch: cycle/020/integration
- Python: 3.11+ | SQLAlchemy 2.0 | asyncio | Pydantic v2 | OpenAI

## YOUR ROLE
Agent D owns: (1) remaining E05 LLM task executors (S5.5-S5.9) plus the async
generate_recommendation() orchestrator, (2) the generate_recommendation() storage path
(write to recommendations table), (3) board reconciliation + SCRUM-24/25 epic corrections,
(4) PR #24 creation, Codex resolution, and final evidence freeze.

## GIT INSTRUCTIONS
1. Ensure you are on: cycle/020/integration
2. Pull latest: git pull origin cycle/020/integration
3. Read all A/B/C handoff reports before coding
4. Commit: feat(recommendations): complete E05 LLM tasks + storage [Agent D Cycle 020]
5. PR: gh pr create --base develop --head cycle/020/integration --title "feat(cycle-020): scoring pipeline wiring and E05 recommendations foundation"
6. Do NOT push until PR body is complete

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git log --oneline -10; git worktree list
  python -m pytest -q tests/unit/test_scoring.py tests/unit/test_scoring_pipeline.py tests/unit/test_scoring_db_integration.py tests/unit/test_scoring_llm.py tests/unit/test_recommendations.py
Pass: All A/B/C tests pass before you start.

## TASKS

### Task 1: Preflight + read all Agent A/B/C handoffs
Read all 3 reports. Confirm test counts match expectations. Confirm Agent C
implemented E05 context, eligibility, and first 4 LLM tasks.
Note any open risks from handoffs.

### Task 2: Read E05 Jira stories S5.5-S5.9 from SCRUM-20 children
Query SCRUM-20 children for stories S5.5 through S5.9.
Record exact keys. Read AC/DoD for each story.
Transition S5.5, S5.6, S5.7, S5.8, S5.9 from To Do to In Progress.
Post planning comment on each key.

### Task 3: Implement remaining 7 async LLM task executors in src/recommendations/tasks.py
Spec: RECOMMENDATION_ENGINE.md (11 LLM tasks, async gather)
Add to src/recommendations/tasks.py (Agent C created this file with first 4 tasks):

- async def generate_package_structure(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/package_structure.j2 | Model: gpt-4o
  Return: {"output": dict with basic/standard/premium packages, "cost_usd": float}

- async def generate_description_outline(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/description_outline.j2 | Model: gpt-4o
  Return: {"output": dict with overview/experience/process/why_us sections, "cost_usd": float}

- async def generate_faq_entries(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/faq_entries.j2 | Model: gpt-4o-mini
  Return: {"output": list of 5-7 Q+A dicts, "cost_usd": float}

- async def generate_buyer_persona(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/buyer_persona.j2 | Model: gpt-4o-mini
  Return: {"output": dict with persona details, "cost_usd": float}

- async def generate_thumbnail_direction(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/thumbnail_direction.j2 | Model: gpt-4o-mini
  Return: {"output": str with thumbnail creative direction, "cost_usd": float}

- async def generate_upsell_structure(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/upsell_structure.j2 | Model: gpt-4o-mini
  Return: {"output": list of upsell opportunities, "cost_usd": float}

- async def generate_niche_viability(context, llm_client, cache) -> dict:
  Template: src/llm/prompts/niche_viability.j2 | Model: gpt-4o
  Return: {"output": dict with viability assessment, "cost_usd": float}

All 7 functions: render template → LLM call → parse → cost estimate → return dict.
Return {"output": None, "cost_usd": 0.0} on any failure (non-crashing).

### Task 4: Implement async generate_recommendation() orchestrator
Add to src/recommendations/tasks.py:
async def generate_recommendation(keyword_id, context, llm_client, cache, db) -> dict:
  """Run all 11 LLM tasks concurrently for a single keyword."""
  tasks = [
    generate_gig_titles(context, llm_client, cache),
    generate_tag_sets(context, llm_client, cache),
    generate_package_structure(context, llm_client, cache),
    generate_description_outline(context, llm_client, cache),
    generate_faq_entries(context, llm_client, cache),
    generate_differentiation_angle(context, llm_client, cache),
    generate_buyer_persona(context, llm_client, cache),
    generate_thumbnail_direction(context, llm_client, cache),
    generate_upsell_structure(context, llm_client, cache),
    generate_red_flags(context, llm_client, cache),
    generate_niche_viability(context, llm_client, cache),
  ]
  import asyncio
  results = await asyncio.gather(*tasks, return_exceptions=True)
  field_names = ["gig_titles","tag_sets","package_structure","description_outline",
    "faq_entries","differentiation_angle","buyer_persona","thumbnail_direction",
    "upsell_structure","red_flags","niche_viability_assessment"]
  recommendation_data = {}
  all_succeeded = True
  total_cost = 0.0
  for field, result in zip(field_names, results):
    if isinstance(result, Exception):
      recommendation_data[field] = None; all_succeeded = False
    else:
      recommendation_data[field] = result.get("output")
      total_cost += result.get("cost_usd", 0.0)
  recommendation_data["generation_complete"] = all_succeeded
  recommendation_data["llm_cost_usd"] = total_cost
  return recommendation_data

### Task 5: Implement write_recommendation() storage function
Add to src/recommendations/eligibility.py (or create src/recommendations/storage.py):
def write_recommendation(keyword_id, run_id, context, recommendation_data, db) -> bool:
  - If Recommendation model exists in src/models/: upsert row
  - If not: write sidecar JSON to data/recommendation_results/{keyword_id}_{run_id}.json
  - Return True on success, False on failure (non-crashing)
  - Include: keyword_id, niche_id, run_id, tag, final_score, all 11 output fields,
    generation_complete, llm_cost_usd, generated_at timestamp

### Task 6: Add remaining E05 tests to tests/unit/test_recommendations.py
Extend the test file created by Agent C. Add minimum 14 new tests:
- test_generate_package_structure_mock — mock returns package dict → output correct
- test_generate_description_outline_mock — mock returns outline → output correct
- test_generate_faq_entries_mock — mock returns FAQ list → output is list
- test_generate_buyer_persona_mock — mock returns persona → output is dict
- test_generate_thumbnail_direction_mock — mock returns string → output is str
- test_generate_upsell_structure_mock — mock returns upsells → output is list
- test_generate_niche_viability_mock — mock returns viability → output is dict
- test_generate_recommendation_all_succeed — asyncio.gather with all mocks succeed
- test_generate_recommendation_partial_failure — 2 tasks fail → generation_complete=False
- test_generate_recommendation_cost_accumulated — costs sum correctly
- test_generate_recommendation_exception_handling — exception in task → captured gracefully
- test_write_recommendation_returns_true — sidecar or DB write returns True
- test_11_task_names_match_field_names — field_names list has exactly 11 entries
- test_generate_recommendation_no_crash_no_llm — mock llm_client returning None output

### Task 7: Run all tests — confirm A/B/C/D tests pass
  python -m pytest -q tests/unit/test_scoring.py
  python -m pytest -q tests/unit/test_scoring_pipeline.py
  python -m pytest -q tests/unit/test_scoring_db_integration.py
  python -m pytest -q tests/unit/test_scoring_llm.py
  python -m pytest -q tests/unit/test_recommendations.py
All must pass. Record total across all files.

### Task 8: Run ruff + mypy
  python -m ruff check src/scoring/ src/recommendations/ tests/unit/
  python -m mypy src/scoring/ src/recommendations/
Both must pass clean.

### Task 9: Run full validation block
All 6 commands. Total tests >= 934 (920 + ~14 new D tests). Coverage >= 90%.

### Task 10: Board reconciliation — fix stale epic statuses
- SCRUM-19 (E04 Scoring epic): verify In Progress (Agent A should have done this; confirm)
- SCRUM-24 (E09 Dashboard epic): query current status; transition to In Progress if showing To Do
- SCRUM-25 (E10 Integration epic): query current status; transition to In Progress if showing To Do
- SCRUM-20 (E05 Recommendations epic): transition from To Do to In Progress
- Document all status corrections in your report.

### Task 11: Post Jira evidence for E05 S5.5-S5.9
For each story key: "Cycle 020 Agent D: [story title] implemented in
  src/recommendations/tasks.py. generate_recommendation() async orchestrator implemented.
  11 concurrent LLM tasks with asyncio.gather. Storage path implemented. Tests: [count].
  DoD remaining: full E2E LLM run with real data, recommendation table persistence."

### Task 12: Post Jira evidence for SCRUM-509 (Cycle 020 control)
Post summary: branch, PR number, final SHA, test count, coverage, epic corrections made.

### Task 13: Create PR #24
gh pr create --base develop --head cycle/020/integration \
  --title "feat(cycle-020): scoring pipeline wiring and E05 recommendations foundation"
PR body must include:
- Summary: score_keyword() pipeline, SQLAlchemy DB integration, LLM wiring (4 calculators),
  E05 context/eligibility/11 LLM tasks, generate_recommendation() orchestrator
- Jira Keys: SCRUM-509, SCRUM-165 through SCRUM-177, E05 story keys S5.1-S5.9
- Changed Files: src/scoring/pipeline.py, calculator updates, src/recommendations/ (4 new files),
  new test files (4)
- Validation: ruff clean, mypy clean, [count] tests, [%] coverage, all gates pass
- AC/DoD table (per-story rows)
- Guardrails confirmation: no main, no worktrees, no secrets

### Task 14: Monitor PR #24 CI checks
gh pr checks [PR number] — wait for all checks to settle.
Required: Lint/Typecheck/Tests/Gates PASS | codecov/project PASS.
If large-PR label needed: gh pr edit [PR] --add-label "override:large-pr"

### Task 15: Resolve all Codex review findings on PR #24 in-cycle
For each Codex finding:
- Valid: fix code + test + push + reply with evidence + resolve thread
- Invalid: evidence-backed reply + resolve thread
No unresolved Codex threads at handoff.

### Task 16: Final artifact hygiene sweep
git status --short — no .env, *.db runtime databases, coverage.xml, *.zip, __pycache__ staged.
Confirm: data/scoring_results/ and data/recommendation_results/ are gitignored or local-only.

### Task 17: Final SHA freeze
git rev-parse origin/cycle/020/integration → record final pushed SHA.
Verify SHA matches PR head.
Post final freeze comment to PR #24.

### Task 18: Update ACTIVE_STORY_DOD_LEDGER.md with Agent D rows
Add rows for E05 S5.5-S5.9 story keys + SCRUM-509 + any E10/E09 monitoring comments.

### Task 19: Confirm all 4 agent reports exist
  docs/cycle_reports/CYCLE_020_AGENT_A.md
  docs/cycle_reports/CYCLE_020_AGENT_B.md
  docs/cycle_reports/CYCLE_020_AGENT_C.md
  docs/cycle_reports/CYCLE_020_AGENT_D.md (this file)

### Task 20: Create Agent D report at docs/cycle_reports/CYCLE_020_AGENT_D.md
Sections: Preflight, E05 implementation summary (S5.5-S5.9 + orchestrator + storage),
board reconciliation actions, PR #24 URL, CI status, Codex findings disposition,
final SHA, test count, coverage, AC/DoD table, merge readiness recommendation.

### Task 21: Post final freeze comment on PR #24
"Final freeze. SHA: [sha]. Tests: [count]. Coverage: [%]. Ruff clean. Mypy clean.
All gates PASS. Codex: resolved. No main changes. Ready to merge."

### Task 22: Merge readiness recommendation
State explicitly: "PR #24 is ready to merge when approved." or document any blockers.

## FILES CREATED THIS CYCLE (Agent D)
| Action | File Path |
|---|---|
| MODIFY | src/recommendations/tasks.py |
| CREATE | src/recommendations/storage.py (or modify eligibility.py) |
| MODIFY | tests/unit/test_recommendations.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_020_AGENT_D.md |

## COMMIT INSTRUCTIONS
git add src/recommendations/ tests/unit/test_recommendations.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_020_AGENT_D.md
git commit -m "feat(recommendations): complete E05 LLM tasks and generate_recommendation orchestrator [Agent D Cycle 020]"

====================================================================
END OF AGENT D PROMPT
====================================================================
