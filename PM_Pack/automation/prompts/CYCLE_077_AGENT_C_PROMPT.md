====================================================================
FIVERR 24/7 AUTONOMOUS RUNNER — CYCLE 077 AGENT C
Policy v4.5 / POST_CYCLE_PM_REVIEW_v4
Prerequisite: AGENT_COMPLETE in CYCLE_077_AGENT_B.md AND CYCLE_077_AGENT_E.md
Runs THIRD after B+E complete.
====================================================================

AGENT C ROLE
C is the integration verification and Go-Live Stage 4+5 agent. C verifies
that everything B+E produced is consistent and correct, executes Stage 4
(forced repair) and Stage 5 (auto-merge trial), resolves ALL remaining
NEEDS_EVIDENCE items, and confirms DOD items 003-010 are complete.

NEVER-BREAK RULES
1. data/cycle037_live.db NEVER modify
2. Stage 4 deliberately introduces a controlled failure — clean up fully after

====================================================================

TASK 1 — PREFLIGHT + FULL INTEGRATION VERIFICATION (LARGE, ~70 min)
Deliverable: All integration checks document PASS; DOD-003 through DOD-007 confirmed.

  1.  `git checkout cycle/077/integration && git pull origin cycle/077/integration`
  2.  Confirm AGENT_COMPLETE in both CYCLE_077_AGENT_B.md and CYCLE_077_AGENT_E.md.
  3.  Run full test suite: `python -m pytest tests/unit/ --cov=automation --cov=src
      --cov-fail-under=90 --timeout=60 -q 2>&1 | tail -25` — must PASS.
  4.  Run `python -m ruff check automation/ src/ tests/ -q` — 0 errors.
  5.  Run `python -m mypy automation/ --ignore-missing-imports -q` — 0 errors.
  6.  Run `python automation/ai_cycle_controller.py brain-check` — PASS.
  7.  Run `python automation/ai_cycle_controller.py pm-pack-audit` — PASS.
  8.  Read `data/live_validation_evidence.json` — confirm v1_status=PASS, v2_status=PASS,
      v3_status=PASS. Read TIERD2_TRACKER.json — confirm cap_status=REMOVED.
  9.  Read CYCLE_077_AGENT_B.md — note Stage 2/3 results and coverage final %.
  10. Read CYCLE_077_AGENT_E.md — note Score 2 new value and V-stage outcomes.
  11. Verify all 15 ADRs exist: `ls docs/architecture/ADR_*.md | wc -l` — must be >= 15.
  12. Verify all 15 runbooks exist and are >= 200 words:
      `python -c "import pathlib; [print(p.name, p.stat().st_size) for p in sorted(pathlib.Path('docs/runbooks').glob('*.md'))]"`
  13. Check latest CI run: `gh run list --workflow=ci.yml --limit 1 --json status,conclusion`
      If FAIL: diagnose and fix before continuing.
  14. Run merge gate dry-run: `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077 2>&1 | tee docs/validation/CYCLE_077_MERGE_GATE_DRY_RUN.txt`
  15. Verify DOD-003 (repo/path gate): `python -c "from automation.ai_cycle_controller import verify_repo_path; verify_repo_path(); print('DOD-003 PASS')"`
  16. Write `docs/validation/CYCLE_077_INTEGRATION_VERIFICATION.md` with all 15 check results.
  17. Commit.

====================================================================

TASK 2 — GO-LIVE STAGE 4: FORCED REPAIR LOOP LIVE TEST (LARGE, ~70 min)
Deliverable: OPS-033 DONE; DOD-009 confirmed; repair fires, detects, recovers.

  1.  Introduce a controlled lint failure in a non-critical test file:
      `echo "import os,sys,re,pathlib  #noqa  extra_comma,," >> tests/unit/test_repair_trigger_stage4.py`
      Run ruff to confirm it fails: `python -m ruff check tests/unit/test_repair_trigger_stage4.py`
  2.  Trigger the repair loop explicitly:
      `python automation/ai_cycle_controller.py repair --trigger lint_fail --target tests/unit/test_repair_trigger_stage4.py --live 2>&1 | tee C:/AI_Runner/logs/stage4_repair.log`
  3.  Verify repair loop ran and fixed the file:
      - Check log shows repair actions taken
      - Run ruff on file again — should now pass
      - Verify no unsafe actions in log (no commits to main, no PR merges)
  4.  Check incident file was written:
      `ls C:/AI_Runner/reports/incidents/ -t | head -1` — verify a new incident.json exists.
      Read it: `cat C:/AI_Runner/reports/incidents/{newest}.json`
  5.  Test a second repair scenario — stale lock:
      `python -c "import json, pathlib, datetime; lock=pathlib.Path(r'C:/AI_Runner/state/test_repair_lock.json'); lock.write_text(json.dumps({'created_at': '2026-06-01T00:00:00', 'cycle': 77, 'agent': 'A'}))"`
      `python automation/ai_cycle_controller.py repair --trigger stale_lock --live 2>&1 | tail -10`
      Verify lock is detected and archived (not deleted).
  6.  Test coverage failure repair: `python automation/ai_cycle_controller.py repair --trigger coverage_fail --cycle 077 --live 2>&1 | tail -10`
  7.  Clean up: remove test_repair_trigger_stage4.py and test lock file.
  8.  Run `python automation/ai_cycle_controller.py recover` — verify it reports clean state.
  9.  Write `docs/validation/GO_LIVE_STAGE_4_EVIDENCE.md`: all 3 repair scenarios, results.
  10. Mark OPS-033 and DOD-009 DONE. Commit.

====================================================================

TASK 3 — GO-LIVE STAGE 5: AUTO-MERGE MECHANISM PROOF (LARGE, ~65 min)
Deliverable: OPS-034 DONE; GJCI-032 auto-merge mechanism fully evidenced.

  1.  Check merge gate result from CYCLE_077_MERGE_GATE_DRY_RUN.txt — note verdict.
  2.  Attempt to enable auto-merge at repo settings level:
      `gh api -X PATCH /repos/KevinSGarrett/Fiverr -f allow_auto_merge=true 2>&1`
      If success: `gh pr merge 88 --squash --auto` — then poll:
      `gh run list --workflow=ci.yml --limit 1 --json status,conclusion` every 60s.
  3.  If auto-merge not available: use admin merge via controller:
      `python automation/ai_cycle_controller.py merge-gate --execute-merge --pr 88 --admin 2>&1 | tee docs/validation/STAGE5_MERGE_EXECUTION.txt`
  4.  If that also fails (branch protection): create a test PR on a less-protected branch:
      `git checkout -b test/stage5-auto-merge-$(date +%Y%m%d%H%M)`
      `echo "# Stage 5 test" > docs/stage5_test.md && git add docs/stage5_test.md`
      `git commit -m "test: Stage 5 auto-merge proof" && git push origin test/stage5-auto-merge-{ts}`
      `gh pr create --base cycle/077/integration --head test/stage5-auto-merge-{ts} --title "stage5 proof" --body "Stage 5 auto-merge mechanism proof"`
      `python automation/ai_cycle_controller.py merge-gate --execute-merge --pr {NUMBER} 2>&1 | tee docs/validation/STAGE5_MERGE_EXECUTION.txt`
  5.  Verify the merge completed: `gh pr view {NUMBER} --json state,mergedAt`
  6.  Verify CI ran on the merged branch: `gh run list --branch cycle/077/integration --limit 1 --json status,conclusion`
  7.  Write `docs/validation/GO_LIVE_STAGE_5_EVIDENCE.md`: merge command used, PR number,
      merge timestamp, CI result, verdict PASS/FAIL.
  8.  Mark OPS-034 DONE. Commit evidence.

====================================================================

TASK 4 — RESOLVE ALL REMAINING NEEDS_EVIDENCE ITEMS (LARGE, ~60 min)
Deliverable: GJCI-029, SEC-007 (confirm still valid), ENV-028 confirmed live.

  1.  GJCI-029 (Transition to Done after full DoD): run merge_gate DoD check:
      `python -c "from automation.merge_gate import MergeGate; mg=MergeGate(); result=mg.check_all_dod_requirements(77); print(result)"`
      Write `docs/validation/GJCI_029_FULL_DOD_CHECK_EVIDENCE.md`.
  2.  SEC-007 (no secrets in artifacts): run the Cycle 077 secret scan:
      `python -c "from automation.secret_guard import scan_all_outputs; result=scan_all_outputs('docs/cycle_reports/'); print('SEC-007:', result)"`
      Write `docs/validation/CYCLE_077_SEC007_VERIFICATION.md`.
  3.  CLAUDE-SUB-007 (subscription billing confirmed): verify billing_mode in claude_model_state.json:
      `python -c "import json; d=json.load(open(r'C:/AI_Runner/state/claude_model_state.json')); print('billing_mode:', d.get('billing_mode'))"`
      Write `docs/validation/CLAUDE_SUB007_C077_VERIFICATION.md`.
  4.  ENV-028 (runner smoke passed): check GitHub Actions for latest runner-smoke.yml run:
      `gh run list --workflow=runner-smoke.yml --limit 1 --json status,conclusion`
      If more than 7 days old: trigger a new run:
      `gh workflow run runner-smoke.yml --ref cycle/077/integration`
      Wait for completion. Write `docs/validation/ENV_028_C077_RUNNER_SMOKE_EVIDENCE.md`.
  5.  DOD-005 (brain-check PASS): already confirmed in Task 1. Write `docs/validation/DOD_005_C077_EVIDENCE.md`.
  6.  DOD-006 (Jira inventory dry-run): `python automation/ai_cycle_controller.py jira-inventory --dry-run 2>&1 | tail -10`
      Write `docs/validation/DOD_006_C077_JIRA_INVENTORY_EVIDENCE.md`.
  7.  DOD-003 (repo/path gate): already confirmed in Task 1. Write `docs/validation/DOD_003_C077_EVIDENCE.md`.
  8.  DOD-010 (PR lifecycle): read Stage 2, 3, 5 evidence to confirm full lifecycle works.
      Write `docs/validation/DOD_010_PR_LIFECYCLE_EVIDENCE.md` summarizing all 3 stages.
  9.  BRAIN-021 (review orchestrator): already evidenced by Agent E. Verify evidence file exists.
      Run once more: `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode advisory 2>&1 | tail -5`
  10. MODEL-013 (drift detection): already evidenced by Agent A. Verify evidence file exists.
  11. Commit all evidence: `git add docs/validation/ && git commit -m "docs(evidence): all NEEDS_EVIDENCE items resolved, DOD-003/005/006/010 confirmed"`

====================================================================

TASK 5 — GJCI ITEMS 029-035 FINAL EVIDENCE + JIRA TRANSITIONS (MEDIUM, ~40 min)

  1.  For GJCI-030 (bug/rework tickets): create a test rework ticket to prove the mechanism:
      `python -c "from automation.jira_client import JiraClient; j=JiraClient(); r=j.create_issue({'summary': 'Test rework ticket from CI - Stage 5', 'issuetype': {'name': 'Bug'}, 'project': {'key': 'SCRUM'}, 'description': 'Created by Agent C to evidence GJCI-030 bug ticket creation'}); print(r['key'])"`
      Immediately transition it to Done. Write `docs/validation/GJCI_030_BUG_TICKET_EVIDENCE.md`.
  2.  Post evidence comments on all GJCI-029 through GJCI-035 Jira stories.
  3.  Transition all evidenced stories to Done.
  4.  Write `docs/cycle_reports/CYCLE_077_AGENT_C_JIRA.md`.
  5.  Commit.

====================================================================

TASK 6 — DOD-004 MODEL GATE EXPIRY CHECK + MODEL-014 DAILY REPORT VERIFY (MEDIUM, ~35 min)

  1.  Check cursor_model_state.json expiry: `python -c "import json; d=json.load(open(r'C:/AI_Runner/state/cursor_model_state.json')); print('verified_until:', d.get('verified_until'), 'status:', d.get('status'))"`
      If expiry is within 48 hours: write a CRITICAL warning to `docs/validation/DOD_004_MODEL_EXPIRY_WARNING.md`.
      Note: the actual re-verification must be done by Kevin manually — document exact steps.
  2.  Verify daily report model section (MODEL-014): read `docs/validation/MODEL_014_DAILY_REPORT_MODEL_SECTION.md`
      from Agent A. Confirm model section is present. If missing: re-run daily report:
      `python automation/ai_cycle_controller.py daily-report 2>&1 | grep -i "model" | head -10`
  3.  Check OPS-010 Slack notification status from Agent A's evidence:
      Read `docs/validation/` for OPS_010 evidence. If webhook is PENDING_CONFIGURATION:
      document exactly what Kevin needs to do to configure the Slack webhook.
  4.  Write `docs/validation/DOD_004_C077_MODEL_GATE_EVIDENCE.md` with current model gate status.
  5.  Commit.

====================================================================

TASK 7 — FINAL COMMIT, PUSH, CYCLE REPORT (MEDIUM, ~30 min)

  1.  Final validation:
      `python -m ruff check automation/ src/ tests/ -q` — 0 errors
      `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5`
      `python automation/ai_cycle_controller.py brain-check`
  2.  `git status` — clean. `git push origin cycle/077/integration`
  3.  Write `docs/cycle_reports/CYCLE_077_AGENT_C.md`:
      - Integration verification: all checks PASS
      - Stage 4 (OPS-033, DOD-009): PASS/FAIL
      - Stage 5 (OPS-034, GJCI-032): PASS/FAIL
      - NEEDS_EVIDENCE items resolved: list
      - DOD-003/005/006/010 confirmed
      - GJCI-029/030 evidenced
      - Model gate: current status
      - Jira: N transitions
      - AGENT_COMPLETE
  4.  Commit and push.

VALIDATION (R-092 Tier 1)
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077

END OF PROMPT

Agent F may proceed after Agent C reports AGENT_COMPLETE.
