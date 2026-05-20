====================================================================
AGENT A — CYCLE 021 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | GitHub: https://github.com/KevinSGarrett/Fiverr
- Local: C:\Fiverr\Fiverr | Branch (to create): cycle/021/integration
- Python 3.11+ | SQLAlchemy 2.0 | Pydantic v2 | asyncio | Click
- Jira: https://kevinsgarrett.atlassian.net | Project: SCRUM
- Prior cycle: PR #24 ready to merge (0 Codex, 935 tests, 92.79%)

## YOUR ROLE
Agent A owns the PR gate, branch setup, and the two functional gaps that prevent
run.py from executing the full end-to-end pipeline: (1) hook run_recommendations()
into run.py AVAILABLE_MODES so Stage 13 is callable as a CLI mode, and (2) close the
codecov/patch gap from PR #24 by adding targeted tests for previously uncovered lines
in pipeline.py and recommendations/.

## GIT INSTRUCTIONS
1. Verify PR #24: gh pr view 24 --json state,mergeable,statusCheckRollup
2. Merge: gh pr merge 24 --merge (only if checks green + mergeable)
3. git checkout develop && git pull --ff-only origin develop
4. git checkout -b cycle/021/integration && git push -u origin cycle/021/integration
5. All work on cycle/021/integration — no other branches
6. Commit: feat(recommendations): run_recommendations CLI and coverage gap [Agent A Cycle 021]
7. Do NOT push — human operator pushes after all 4 agents complete

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git rev-parse --show-toplevel; git branch --show-current
  git status --short --branch; git worktree list; git fetch origin
  gh pr view 24 --json state,mergeable,statusCheckRollup
Pass: root = C:\Fiverr\Fiverr, PR #24 MERGEABLE + all checks SUCCESS.

## TASKS

### Task 1: Preflight and PR #24 verification
Run all 7 preflight commands. Capture full gh pr view 24 output.
Confirm CI checks SUCCESS. Confirm 0 unresolved review threads.
Abort and document if PR #24 is not mergeable.

### Task 2: Merge PR #24, close SCRUM-509, create branch
- gh pr merge 24 --merge
- git checkout develop && git pull --ff-only origin develop
- Baseline: python -m pytest -q --cov=src --cov-fail-under=90 → expect 935 tests, ~92.79%
- git checkout -b cycle/021/integration && git push -u origin cycle/021/integration
- Jira: Transition SCRUM-509 to Done. Comment: "PR #24 merged. SHA: [merge commit].
  935 tests, 92.79%. Cycle 020 complete."
- Jira: Create SCRUM-510 as Cycle 021 control → In Progress. Comment: branch + scope.

### Task 3: Read existing recommendations/__init__.py and run.py AVAILABLE_MODES
Read: src/recommendations/__init__.py (exports from Cycle 020)
Read: run.py (all CLI commands and AVAILABLE_MODES dict)
Read: src/recommendations/eligibility.py (get_eligible_keywords, passes_recommendation_gates)
Read: src/recommendations/tasks.py (generate_recommendation)
Read: src/recommendations/storage.py (write_recommendation)
Note: what exists, what is exported, and what the CLI needs to call for Stage 13.
Record your design plan in your report before writing code.

### Task 4: Implement run_recommendations() orchestration function
Create: src/recommendations/run.py (or add to orchestrator.py — read existing file first)

Implement:
async def run_recommendations_stage(run_id: str, db, config, llm_client, cache,
  dry_run: bool = True) -> dict:
  """
  Stage 13 orchestration: eligibility → gates → skip check → context →
  generate_recommendation → write_recommendation.
  Returns summary: {eligible_count, generated, skipped, failed, total_cost_usd}
  """
  eligible = get_eligible_keywords(run_id, db, config)
  summary = {"eligible_count": len(eligible), "generated": 0, "skipped": 0,
             "failed": 0, "total_cost_usd": 0.0}
  for kw in eligible:
    passes, reason = passes_recommendation_gates(kw, db)
    if not passes:
      summary["skipped"] += 1; continue
    should_regen = should_regenerate_recommendation(kw["keyword_id"],
      kw.get("final_score", 0), db)
    if not should_regen:
      summary["skipped"] += 1; continue
    try:
      from src.recommendations.context import build_recommendation_context
      context = build_recommendation_context(kw["keyword_id"], db, config)
      if dry_run:
        # Smoke safe: skip real LLM, return stub result
        result = {"generation_complete": False, "llm_cost_usd": 0.0,
                  "gig_titles": None, "tag_sets": None,
                  "package_structure": None, "description_outline": None,
                  "faq_entries": None, "differentiation_angle": None,
                  "buyer_persona": None, "thumbnail_direction": None,
                  "upsell_structure": None, "red_flags": None,
                  "niche_viability_assessment": None}
      else:
        result = await generate_recommendation(kw["keyword_id"], context,
          llm_client, cache, db)
      write_recommendation(kw["keyword_id"], run_id, context, result, db)
      summary["generated"] += 1
      summary["total_cost_usd"] += result.get("llm_cost_usd", 0.0)
    except Exception as e:
      summary["failed"] += 1
  return summary

### Task 5: Hook recommendations-only mode into run.py
Read run.py fully. Find AVAILABLE_MODES dict and the --mode Click option.
Add "recommendations-only" to AVAILABLE_MODES with description:
  "recommendations-only: Re-run Stage 13 for all eligible keywords using existing scores."
Add handling in the main run function: when mode == "recommendations-only":
  import asyncio
  from src.recommendations.run import run_recommendations_stage
  result = asyncio.run(run_recommendations_stage(run_id, db, config,
    llm_client=None, cache=None, dry_run=True))
  click.echo(f"Recommendations stage complete: {result}")
Test: python run.py recommendations-only → must not crash and must output summary.
If run_id and db are not available in the simple CLI path, generate a placeholder run_id
and pass a minimal mock db object that returns empty lists for all queries.

### Task 6: Investigate codecov/patch failure from PR #24
Read: coverage.xml (check which lines in pipeline.py and recommendations/ have no test coverage)
Run: python -m pytest -q --cov=src/scoring/pipeline.py --cov-report=term-missing
Run: python -m pytest -q --cov=src/recommendations --cov-report=term-missing
Identify: specific line numbers and functions with 0% patch coverage.
Document: in your report, list every uncovered function and its file.

### Task 7: Add targeted patch-gap tests for pipeline.py
In tests/unit/test_scoring_pipeline.py, add tests for lines missed by codecov/patch:
Focus areas (based on typical uncovered paths in pipeline.py from Cycle 020):
- score_keyword() when keyword_id maps to empty DB data → returns None gracefully
- score_keyword_batch() with mixed success/fail keywords → error captured per keyword
- write_keyword_score() when data/scoring_results/ directory doesn't exist → auto-creates it
- detect_red_flags_from_scores() with trend_score < 25 → MEDIUM flag returned
- DEPTH_SCORE_AVAILABILITY["feasibility"] correctly excludes scores 6-9
- validate_scoring_profile() with weights summing to 0.999 → passes (within tolerance)
- calculate_final_score() confidence_floor applied when confidence = 0.0 → floor = 0.20
Add minimum 8 new tests. Document each with the line/function they cover.

### Task 8: Add targeted patch-gap tests for recommendations/
In tests/unit/test_recommendations.py, add tests for uncovered recommendation lines:
Focus areas:
- run_recommendations_stage() dry_run=True → no crash, summary returned with correct keys
- run_recommendations_stage() keyword that fails gates → skipped count incremented
- run_recommendations_stage() keyword that doesn't need regeneration → skipped count
- write_recommendation() when data/recommendation_results/ doesn't exist → auto-creates dir
- build_recommendation_context() when Keyword not found in DB → safe None return
- get_eligible_keywords() returns empty list when no STRONG_GO/CONDITIONAL_GO keywords
Add minimum 8 new tests.

### Task 9: Run targeted tests for Agent A additions
python -m pytest -q tests/unit/test_scoring_pipeline.py
python -m pytest -q tests/unit/test_recommendations.py
All must pass. Record test counts per file.

### Task 10: Run python run.py recommendations-only smoke test
python run.py recommendations-only
Must complete without exception. Must output a summary dict.
Record exact output in your report.

### Task 11: Run python run.py phase2-smoke (confirm no regression)
python run.py phase2-smoke
Must still pass after run.py changes.

### Task 12: Run ruff + mypy on changed files
python -m ruff check src/recommendations/ run.py tests/unit/test_scoring_pipeline.py tests/unit/test_recommendations.py
python -m mypy src/recommendations/ run.py
Both must pass. Fix all issues.

### Task 13: Run full validation block
All 6 commands. Total tests >= 951 (935 + 16 new). Coverage >= 90%.
Record in report.

### Task 14: Read E05 Jira stories SCRUM-182-186 and post Agent A contribution comments
For SCRUM-183 (run_recommendations orchestrator) and SCRUM-184 (storage validation):
Post comment: "Cycle 021 Agent A: run_recommendations_stage() implemented in
  src/recommendations/run.py. Hooked as 'recommendations-only' CLI mode in run.py.
  Dry-run smoke tested. Coverage gap tests added (+16). Status: In Progress."

### Task 15: Post comment on SCRUM-175 (Final Composite) about recommendations-only mode
Comment: "Cycle 021 Agent A: recommendations-only mode now callable via CLI. Stage 13
  orchestration consumes score_keyword() outputs from pipeline.py. Full pipeline now
  callable from CLI for both scoring and recommendations."

### Task 16: Update docs/jira/ACTIVE_STORY_DOD_LEDGER.md with Cycle 021 Agent A rows
Add rows for SCRUM-510, SCRUM-183, SCRUM-184 with AC advanced, DoD remaining, validation.

### Task 17: Verify .cursorrules compliance for new files
Read .cursorrules. Verify src/recommendations/run.py:
- Type annotations on all public functions
- No print() (use click.echo for CLI, logging for library code)
- Line length within configured limit

### Task 18: Artifact hygiene check before commit
git status --short — no .env, *.db, coverage.xml staged.
Commit scope: src/recommendations/run.py, run.py, test additions, ledger, report.
Message: feat(recommendations): run_recommendations CLI and coverage patch gap [Agent A Cycle 021]

### Task 19: No-main / worktree check
git worktree list → canonical root only. No main changes.

### Task 20: Record SHA and handoff to Agent B
git rev-parse HEAD → record as Agent A SHA.
Handoff: "recommendations-only CLI mode works. Coverage gap partially closed (+16 tests).
Agent B: create KeywordScore ORM model so write_keyword_score() can leave sidecar path."

### Task 21: Post SCRUM-231 (E10 Integration) comment with recommendations-only evidence
Comment: "Cycle 021 Agent A: run_recommendations() Stage 13 is now callable.
Dry-run execution confirmed via recommendations-only CLI mode. This advances SCRUM-231
end-to-end pipeline evidence — the scoring → ranking → recommendations pipeline
is now triggerable from CLI. Keep In Review pending real-data E2E run."

### Task 22: Read E05 spec AC for SCRUM-178 (eligibility) and SCRUM-179 (skip logic)
Verify the run_recommendations_stage() function satisfies the spec's gating and skip-logic
AC bullets. Document any gaps in your report.

### Task 23: Create Agent A report at docs/cycle_reports/CYCLE_021_AGENT_A.md
Sections: Preflight, PR #24 merge evidence, branch SHA, SCRUM-509 Done, SCRUM-510 created,
run_recommendations() design, CLI mode change in run.py, codecov gap analysis (files/lines),
new test count (+16), validation block, Jira comments, handoff.

### Task 24: Commit and finalize
Final commit: all scoped files only. No generated artifacts. No PM Pack zip.
Ensure cycle/021/integration is pushed to origin after all files are committed.

## FILES CREATED THIS CYCLE (Agent A)
| Action | File |
|---|---|
| CREATE | src/recommendations/run.py |
| MODIFY | run.py |
| MODIFY | tests/unit/test_scoring_pipeline.py |
| MODIFY | tests/unit/test_recommendations.py |
| MODIFY | docs/jira/ACTIVE_STORY_DOD_LEDGER.md |
| CREATE | docs/cycle_reports/CYCLE_021_AGENT_A.md |

## COMMIT INSTRUCTIONS
git add src/recommendations/run.py run.py
git add tests/unit/test_scoring_pipeline.py tests/unit/test_recommendations.py
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_021_AGENT_A.md
git commit -m "feat(recommendations): run_recommendations CLI and coverage patch gap [Agent A Cycle 021]"
====================================================================
END OF AGENT A PROMPT
====================================================================
