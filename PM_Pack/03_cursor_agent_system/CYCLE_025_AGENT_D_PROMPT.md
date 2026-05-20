====================================================================
AGENT D — CYCLE 025 PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System | Branch: cycle/025/integration
- Python 3.11+ | asyncio | Click

## ⚠️ MANDATORY MERGE GATE — BOTH RULES APPLY EVERY PR

RULE G-001: codecov/patch ≥ 90% — HARD BLOCKER. Add tests, push, re-check, confirm PASS.
RULE G-003: Codex threads — run GraphQL query, classify ALL threads, fix VALID_FIXED with
  regression test, reply ALL threads with disposition format, resolve ALL manually.
RULE G-004: Fill the COMPLETE merge gate checklist. ALL items PASS/YES before merge.

## YOUR ROLE
Agent D owns: (1) collection orchestrator ("collect-only" CLI mode in run.py that wires
all the Cycle 024-025 collection pieces together into a runnable dry_run pipeline),
(2) patch coverage audit for all new collection/scheduler modules, (3) PR #29 with full
merge gate checklist.

The "collect-only" mode must run a complete dry_run pass: Workflow 1 → Workflow 2 stub →
Workflow 3 stub → Workflow 4 stub → Workflow 5 stub, using the CheckpointManager to write
stubs, QueueProcessor for job sequencing, and PacingManager for delay simulation.
It must complete without error and print a summary. This is the first time all Cycle 024-025
pieces are wired together end-to-end (in dry_run mode).

## GIT INSTRUCTIONS
1. Ensure on: cycle/025/integration. Pull latest.
2. Read ALL A/B/C handoffs.
3. Commit: feat(collection): collect-only orchestrator and patch coverage [Agent D Cycle 025]
4. gh pr create --base develop --head cycle/025/integration
   --title "feat(cycle-025): CheckpointManager, retry handler, Workflows 4-5, collect-only mode"
5. After CI settles: verify ALL checks. Handle Codex. Fill checklist.

## MANDATORY POWERSHELL PREFLIGHT
  Get-Location; git branch --show-current; git log --oneline -12; git worktree list
  python -m pytest -q --cov=src --cov-fail-under=90
Pass: all tests pass, coverage ≥ 90%.

## TASKS

### Task 1: Read all handoffs + run full suite
Read all 3 cycle reports. Run full validation block. Record count and coverage.

### Task 2: Read E02 orchestrator story key before coding
Query SCRUM-17 children. Find a story for collection orchestration or collect-only mode.
If no exact match, use S2.1 "Session Manager" story as the vehicle (Workflow 1 is stage 1).
Transition story to In Progress. Post planning comment.

### Task 3: Create src/collection/orchestrator.py — collection orchestrator
This is the new orchestrator that wires all Cycle 024-025 pieces together:

async def run_collection_pipeline(
  run_id: str,
  db,
  config: dict,
  session_manager,
  dry_run: bool = True,
) -> dict:
  """
  Runs the complete collection pipeline (Stages 1-5) in dry_run mode.
  In real mode (dry_run=False): raises NotImplementedError until Playwright wiring is done.
  Returns a summary dict with per-stage results.
  """
  from src.collection.checkpoint import CheckpointManager
  from src.collection.pacing import PacingManager
  from src.collection.workflows.niche_init import run_niche_initialization
  from src.collection.workflows.keyword_expansion import run_keyword_expansion
  from src.collection.workflows.fiverr_search import run_fiverr_search_collection
  from src.collection.workflows.gig_detail import run_gig_detail_collection
  from src.collection.workflows.seller_profile import run_seller_profile_collection

  pacing = PacingManager(config)
  checkpoint_mgr = CheckpointManager(run_id, data_dir="data")
  summary = {
    "run_id": run_id,
    "dry_run": dry_run,
    "stages_run": [],
    "niches_initialized": 0,
    "keywords_queued": 0,
    "search_jobs_run": 0,
    "gig_detail_jobs_run": 0,
    "seller_profile_jobs_run": 0,
    "errors": [],
  }

  # Stage 1: Niche Initialization
  try:
    stage1_result = await run_niche_initialization(config, db, run_id, dry_run=dry_run)
    summary["niches_initialized"] = stage1_result.get("niches_processed", 0)
    summary["stages_run"].append("stage01_niche_init")
    checkpoint_mgr.write("stage01", "all_niches", {"niches_processed": summary["niches_initialized"]})
  except Exception as e:
    summary["errors"].append(f"Stage 1 error: {str(e)}")

  # Stage 2: Keyword Expansion stubs (dry run)
  for niche_spec in stage1_result.get("niche_specs", []) if "stage1_result" in dir() else []:
    try:
      stage2_result = await run_keyword_expansion(
        niche_spec["niche_id"], niche_spec.get("seeds", []),
        niche_spec.get("depth", "standard"), run_id, db,
        session_manager, pacing, dry_run=dry_run
      )
      summary["keywords_queued"] += stage2_result.get("keywords_queued", 0)
    except Exception as e:
      summary["errors"].append(f"Stage 2 error ({niche_spec.get('niche_id')}): {str(e)}")
  summary["stages_run"].append("stage02_keyword_expansion")

  # Stages 3-5: Run stub workflows for any queued keywords
  # In dry_run mode: run one representative call to confirm interface
  if dry_run:
    try:
      await run_fiverr_search_collection(
        keyword_id=0, keyword_text="_dry_run_test_",
        niche_id="dry_run", depth="standard",
        run_id=run_id, db=db, session_manager=session_manager,
        pacing_manager=pacing, dry_run=True,
      )
      summary["search_jobs_run"] = 0
      summary["stages_run"].append("stage03_fiverr_search")
    except Exception as e:
      summary["errors"].append(f"Stage 3 smoke error: {str(e)}")

    try:
      await run_gig_detail_collection(
        gig_url="https://dry-run-test.invalid/", keyword_id=0,
        niche_id="dry_run", depth="standard", run_id=run_id,
        db=db, session_manager=session_manager, pacing_manager=pacing,
        checkpoint_manager=checkpoint_mgr, dry_run=True,
      )
      summary["gig_detail_jobs_run"] = 0
      summary["stages_run"].append("stage04_gig_detail")
    except Exception as e:
      summary["errors"].append(f"Stage 4 smoke error: {str(e)}")

    try:
      await run_seller_profile_collection(
        seller_username="_dry_run_test_", niche_id="dry_run",
        run_id=run_id, db=db, session_manager=session_manager,
        pacing_manager=pacing, checkpoint_manager=checkpoint_mgr, dry_run=True,
      )
      summary["seller_profile_jobs_run"] = 0
      summary["stages_run"].append("stage05_seller_profile")
    except Exception as e:
      summary["errors"].append(f"Stage 5 smoke error: {str(e)}")
  else:
    raise NotImplementedError(
      "Real collection (dry_run=False) not yet implemented. "
      "Set dry_run=True or await Playwright wiring in Cycle 026."
    )

  return summary

### Task 4: Wire "collect-only" mode into run.py
Find AVAILABLE_MODES and run_pipeline() in run.py. Add "collect-only":
  if mode == "collect-only":
    import asyncio
    from src.collection.orchestrator import run_collection_pipeline
    # Use a placeholder run_id and minimal config for smoke
    import uuid
    result = asyncio.run(run_collection_pipeline(
      run_id=str(uuid.uuid4()),
      db={},  # dict proxy for smoke
      config=config if isinstance(config, dict) else {},
      session_manager=None,
      dry_run=True,
    ))
    click.echo(f"Collection dry run complete: {result}")

Test: python run.py collect-only → must not crash and must print summary dict.

### Task 5: Run comprehensive patch coverage audit
  python -m pytest -q --cov=src.collection.checkpoint --cov-report=term-missing
  python -m pytest -q --cov=src.scheduler.retry_handler --cov-report=term-missing
  python -m pytest -q --cov=src.scheduler.exceptions --cov-report=term-missing
  python -m pytest -q --cov=src.collection.workflows --cov-report=term-missing
  python -m pytest -q --cov=src.collection.orchestrator --cov-report=term-missing
Document uncovered lines per file.

### Task 6: Add targeted patch gap tests
For any uncovered lines, add tests to existing test files.
Also add orchestrator tests to tests/unit/test_collection_orchestrator.py (minimum 10):
- test_run_collection_dry_run_returns_summary — returns dict with run_id
- test_run_collection_dry_run_stages_run — all 5 stage keys in stages_run
- test_run_collection_dry_run_no_errors — errors list is empty
- test_run_collection_raises_without_dry_run — dry_run=False → NotImplementedError
- test_collect_only_cli_smoke — python run.py collect-only → no crash
- test_run_collection_niches_processed — niches_initialized field present
- test_run_collection_stages_list — stages_run is non-empty list
- test_orchestrator_checkpoint_written — checkpoint file created in data/ for dry run
- test_orchestrator_handles_stage1_error — Stage 1 exception → in errors list, continues
- test_orchestrator_session_manager_none — session_manager=None → no crash (dry_run path)
Minimum 10 tests.

### Task 7: Run full validation block
All 6 commands plus:
  python run.py collect-only
Target: ≥ 1337 tests. Coverage ≥ 90%.

### Task 8: Board reconciliation
SCRUM-513 Done, SCRUM-514 In Progress, SCRUM-17 In Progress.
All E02 story keys In Progress. SCRUM-19/20/21/22/24/25 In Progress. SCRUM-231 In Review.

### Task 9: Post SCRUM-17 (E02 epic) collect-only smoke evidence
Post: "Cycle 025: python run.py collect-only executes dry-run pipeline (Stages 1-5).
  All workflow stubs callable. CheckpointManager writes stage01 checkpoint. No real
  Playwright. Next cycle (026): wire real Workflow 3 Playwright navigation."

### Task 10: Commit before PR creation
Message: feat(collection): collect-only orchestrator and patch coverage [Agent D Cycle 025]

### Task 11: Create PR #29
gh pr create --base develop --head cycle/025/integration \
  --title "feat(cycle-025): CheckpointManager, retry handler, Workflows 4-5, collect-only mode"
PR body: all deliverables, Jira keys, test count, validation, AC/DoD table, guardrails.

### Task 12: Monitor ALL CI checks — codecov/patch HARD BLOCKER
Wait for all checks. codecov/patch MUST show SUCCESS. If FAILURE: add tests, push, re-check.

### Task 13: ⚠️ MANDATORY CODEX DISPOSITION QUERY
Run the exact query for PR #29 number. Document raw result and thread count.
If 0: "Codex confirmed 0 threads." If any: classify, fix VALID_FIXED + regression test,
reply ALL, resolve ALL.

### Task 14: ⚠️ FILL MANDATORY MERGE GATE CHECKLIST
```
MERGE GATE CHECKLIST — Cycle 025 PR #29
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
[ ] PR #29 is ready to merge: [YES/NO]
[ ] Blockers if NO: [list or N/A]
```

### Tasks 15-22: Final cleanup
15. Final SHA freeze. Match to PR head.
16. Confirm all 4 agent reports present.
17. Update ACTIVE_STORY_DOD_LEDGER.md.
18. Create docs/cycle_reports/CYCLE_025_AGENT_D.md.
19. Post SCRUM-514 final steward summary.
20. Artifact hygiene. 21. No-main check.
22. State: "PR #29 is ready to merge when approved." or list blockers.

## COMMIT INSTRUCTIONS
git add src/collection/orchestrator.py run.py
git add tests/unit/test_collection_orchestrator.py tests/unit/
git add docs/jira/ACTIVE_STORY_DOD_LEDGER.md docs/cycle_reports/CYCLE_025_AGENT_D.md
git commit -m "feat(collection): collect-only orchestrator and patch coverage [Agent D Cycle 025]"
====================================================================
END OF AGENT D PROMPT
====================================================================
