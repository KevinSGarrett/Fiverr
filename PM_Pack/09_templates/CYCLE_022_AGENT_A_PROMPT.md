====================================================================
AGENT A — CYCLE 022 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/022/integration
- Python 3.11+ | SQLAlchemy 2.0 | asyncio | OpenAI
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM
- Prior cycle PR: #25 ready to merge (1002 tests, 93.00%)

## ⚠️ PROTOCOL CORRECTION — READ BEFORE ANYTHING ELSE

Two rules changed this cycle. You must follow both or the PR will be blocked:

RULE G-001: codecov/patch IS a hard merge blocker.
  If codecov/patch shows FAIL after you push, you MUST add tests, re-push, and wait
  for it to show PASS before recommending merge. Previous cycles incorrectly merged
  with patch failing. This is prohibited going forward.

RULE G-003: Codex review threads MUST be queried, classified, dispositioned, and resolved.
  Run the exact GraphQL query in Task 7. If 0 threads: document explicitly.
  If any threads: classify each, fix VALID_FIXED with regression test, reply to ALL,
  resolve ALL before merge.

## YOUR ROLE
Agent A owns the PR gate, branch setup, and E04 Stage 14 — the explanation text
generation stub for the scoring pipeline. Stage 14 uses gpt-4o to generate a
human-readable explanation of each keyword's final recommendation score. Your job
is to create a feature-flagged generate_score_explanation() function that:
- When llm_client is None: returns a deterministic template explanation
- When llm_client is provided: calls gpt-4o with the score context
Also wire score_keyword() into --mode full in run.py.

## GIT INSTRUCTIONS
1. Verify PR #25: gh pr view 25 --json state,mergeable,statusCheckRollup
2. ⚠️ ALSO CHECK: gh pr view 25 --json statusCheckRollup | grep codecov
   Both codecov/project AND codecov/patch must show SUCCESS before merge.
   If codecov/patch shows FAILURE: add tests, push, wait for re-check, then merge.
3. Merge PR #25 only when BOTH codecov checks show SUCCESS.
4. git checkout develop && git pull --ff-only origin develop
5. git checkout -b cycle/022/integration && git push -u origin cycle/022/integration
6. Commit: feat(scoring): Stage 14 explanation + mode full wiring [Agent A Cycle 022]
7. Do NOT push — human operator pushes after all agents complete

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 25 --json state,mergeable,statusCheckRollup
Pass: root = C:\Fiverr\Fiverr, PR #25 MERGEABLE, ALL checks including codecov/patch = SUCCESS.

## TASKS

### Task 1: Preflight and PR #25 verification
Run all 7 preflight commands. Capture FULL output of gh pr view 25 statusCheckRollup.
⚠️ Verify BOTH of these are SUCCESS before proceeding to merge:
  - "codecov/project" conclusion: SUCCESS
  - "codecov/patch" conclusion: SUCCESS
If codecov/patch is FAILURE:
  - Run: python -m pytest -q --cov=src/scoring/pipeline.py --cov-report=term-missing
  - Run: python -m pytest -q --cov=src/recommendations --cov-report=term-missing
  - Add tests for any uncovered NEW lines (lines added in cycles 020/021)
  - Commit the tests, push, wait for re-check
  - Only proceed to merge after codecov/patch shows SUCCESS

### Task 2: Merge PR #25, close SCRUM-510, create branch
- Merge ONLY after codecov/patch PASS confirmed.
- gh pr merge 25 --merge
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 1002 tests, 93.00%+
- git checkout -b cycle/022/integration && git push -u origin cycle/022/integration
- Jira: Transition SCRUM-510 to Done with merge SHA comment.
- Jira: Create SCRUM-511 as Cycle 022 control → In Progress.

### Task 3: Read existing scoring pipeline before implementing Stage 14
Read: src/scoring/pipeline.py (full file — understand score_keyword() output structure)
Read: PM_Pack/ref/project_plan/05_scoring/SCORING_DIRECTION.md (Explanation Field Standard)
Read: src/llm/client.py (LLMClient.complete() API)
Note: The explanation_text field is in every score result payload. Score context needed
for generating an explanation: keyword_text, niche_id, tag, final_score, confidence_modifier,
top 3 score components (by contribution), any red_flags, missing_data_warnings.

### Task 4: Implement generate_score_explanation() in src/scoring/pipeline.py
Add to src/scoring/pipeline.py:

async def generate_score_explanation(
    keyword_id: int,
    keyword_text: str,
    scores: dict,
    components: dict,
    final_score: float,
    tag: str,
    llm_client,
    cache,
) -> str:
  """
  Generates a human-readable explanation for a keyword's final recommendation score.
  Feature-flagged: returns template explanation when llm_client is None.
  """
  # Always available (no LLM required) — build template explanation
  top_components = sorted(
    [(k, v["contribution"]) for k, v in components.items() if v.get("contribution")],
    key=lambda x: x[1], reverse=True
  )[:3]
  top_text = ", ".join(f"{k.replace('_score', '')}={v:.1f}" for k, v in top_components)
  template_explanation = (
    f"Final score: {final_score:.1f} ({tag}). "
    f"Confidence: {scores.get('confidence_modifier', 0):.2f}. "
    f"Top drivers: {top_text}. "
    f"Profile: {scores.get('scoring_profile', 'default')}."
  )

  if llm_client is None:
    return template_explanation

  # LLM path — feature-flagged, stub-safe
  try:
    prompt = (
      f"Explain in 2-3 sentences why '{keyword_text}' scored {final_score:.1f}/100 "
      f"with tag {tag}. Top score drivers: {top_text}. "
      f"Confidence modifier: {scores.get('confidence_modifier', 0):.2f}. "
      f"Be specific and actionable for a new Fiverr seller."
    )
    result = await llm_client.complete(
      prompt=prompt, model="gpt-4o", temperature=0.3
    )
    return result.text or template_explanation
  except Exception:
    return template_explanation

Update score_keyword() to call generate_score_explanation() and populate explanation_text
in the returned result dict and write_keyword_score() call.

### Task 5: Wire score_keyword() into --mode full in run.py
Read run.py fully. Find where --mode full is handled in the orchestrator.
Add score_keyword_batch() call to the full-run pipeline after analysis stage:
  - Get keyword_ids from DB (all keywords for the run's niches)
  - Call score_keyword_batch(keyword_ids, profile_name, db, llm_client=None, cache=None)
  - Store results (write_keyword_score for each)
  - Log summary: "Scoring complete: {N} keywords scored"
Keep it smoke-safe: llm_client=None for dry-run / phase2-smoke paths.
Test: python run.py phase2-smoke → must still pass after wiring.

### Task 6: Add tests for Stage 14 explanation function
Add to tests/unit/test_scoring_pipeline.py:
- test_generate_score_explanation_no_llm — llm_client=None → returns template string
- test_generate_score_explanation_template_contains_score — template includes final_score
- test_generate_score_explanation_template_contains_tag — template includes tag
- test_generate_score_explanation_llm_mock — mock llm_client → returns mock text
- test_generate_score_explanation_llm_failure — mock raises exception → falls back to template
- test_generate_score_explanation_empty_components — empty components → no crash
- test_score_keyword_explanation_populated — explanation_text is non-empty string in result
- test_mode_full_smoke — python run.py phase2-smoke passes after wiring (indirect test)
Minimum 7 new tests.

### Task 7: Run Codex disposition query for PR #25 (MANDATORY)
Run this exact query:
  gh api graphql -f query='{repository(owner:"KevinSGarrett",name:"Fiverr"){pullRequest(number:25){reviewThreads(first:50){nodes{id isResolved isOutdated comments(first:3){nodes{author{login}body}}}}}}}'
Document in your report:
  "Codex review query for PR #25: [paste raw result]"
  "Total threads found: [N]"
  "Disposition: [none required / list of threads and their classification]"
If any threads exist: follow CODEX_REVIEW_DISPOSITION_PROTOCOL.md for each.

### Task 8: Run targeted tests
python -m pytest -q tests/unit/test_scoring_pipeline.py
Expect ≥ 32 tests passing (25 prior + 7 new). Record count.

### Task 9: Run ruff + mypy
python -m ruff check src/scoring/pipeline.py run.py tests/unit/test_scoring_pipeline.py
python -m mypy src/scoring/pipeline.py run.py
Both must pass. Fix all issues.

### Task 10: Run full validation block
  python -m ruff check .
  python -m mypy src
  python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
  python run.py config-check
  python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle022.db
  python run.py phase2-smoke
Expect ≥ 1009 tests. Coverage ≥ 90%. Record exact values.

### Task 11: Run targeted patch coverage check
python -m pytest -q --cov=src/scoring/pipeline.py --cov-report=term-missing
Identify and list every line/function still showing as uncovered (marked ">").
Document in your report. If any new functions from Tasks 4/5 are uncovered, add tests now.

### Task 12: Post Jira evidence for SCRUM-175, SCRUM-177
Comment on SCRUM-175 (Final Composite): "Cycle 022 Agent A: Stage 14 explanation generator
  added with feature flag. Template path requires no LLM. LLM path uses gpt-4o.
  score_keyword() now populates explanation_text."
Comment on SCRUM-177 (Orchestration): "Cycle 022 Agent A: score_keyword_batch() wired into
  --mode full run path. Phase2-smoke confirmed passing."

### Task 13: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md
Add Cycle 022 Agent A rows for SCRUM-511, SCRUM-175, SCRUM-177.

### Task 14: Artifact hygiene + commit
git status --short — no .env, *.db, coverage.xml staged.
Message: feat(scoring): Stage 14 explanation and mode-full wiring [Agent A Cycle 022]

### Task 15: No-main / worktree check + record SHA
git worktree list → canonical root only. No main changes.
git rev-parse HEAD → record Agent A SHA.

### Task 16: Handoff to Agent B
Handoff note: "Stage 14 explanation feature-flagged. score_keyword in --mode full.
Agent B: build E06 S6.3 price distribution analysis runner."

### Task 17: Create Agent A report at docs/cycle_reports/CYCLE_022_AGENT_A.md
Sections: Preflight, PR #25 codecov/patch status verification, merge evidence,
Codex query result (explicit), Stage 14 design, --mode full wiring, test count,
validation block, patch coverage check, Jira comments, handoff.

### Tasks 18-24: Remaining items
18. Read E06 S6.3 Jira key from SCRUM-21 children; post planning intent comment for Agent B.
19. Verify python run.py recommendations-only still passes.
20. Verify python run.py phase2-smoke still passes.
21. Confirm .cursorrules compliance for new functions.
22. Confirm no push done (human operator pushes after all agents).
23. Confirm data/scoring_results/ and data/recommendation_results/ not staged.
24. Final SHA + count recorded for handoff.

## FILES CREATED THIS CYCLE (Agent A)
| Action | File |
|---|---|
| MODIFY | src/scoring/pipeline.py |
| MODIFY | run.py |
| MODIFY | tests/unit/test_scoring_pipeline.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_022_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/scoring/pipeline.py run.py
git add tests/unit/test_scoring_pipeline.py docs/jira/ACTIVE_STORY_DOD_LEDGER.md
git add docs/cycle_reports/CYCLE_022_AGENT_A.md
git commit -m "feat(scoring): Stage 14 explanation and mode-full wiring [Agent A Cycle 022]"
====================================================================
END OF AGENT A PROMPT
====================================================================
