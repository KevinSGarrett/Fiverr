====================================================================
FIVERR 24/7 AUTONOMOUS RUNNER — CYCLE 077 AGENT B
Policy v4.5 / POST_CYCLE_PM_REVIEW_v4
Prerequisite: AGENT_COMPLETE in docs/cycle_reports/CYCLE_077_AGENT_A.md
Runs CONCURRENTLY with Agent E after Agent A completes.
====================================================================

AGENT B ROLE
B is the quality, Go-Live execution, and real dispatch agent. B raises all
coverage to final production targets, executes Go-Live Stages 2 and 3 (the
first real Cursor agent dispatches), fixes BUG-011, completes GJCI-032
(auto-merge), and produces evidence for DOD-008, DOD-009, DOD-010, DOD-011.

NEVER-BREAK RULES
1. data/cycle037_live.db NEVER modify
2. SMALL tasks do not count toward 55-task floor
3. Stage 2 and Stage 3 dispatches use REAL Cursor CLI — not dry-run
4. No src/ changes that touch scoring logic — coverage only

====================================================================

TASK 1 — PREFLIGHT + COVERAGE FINAL PRODUCTION PASS (LARGE, ~90 min)
Deliverable: ALL automation/ and src/ modules at >=90% combined; no regressions.

  1.  `git checkout cycle/077/integration && git pull origin cycle/077/integration`
  2.  Confirm AGENT_COMPLETE in CYCLE_077_AGENT_A.md.
  3.  Run `python automation/ai_cycle_controller.py brain-check` — PASS required.
  4.  Run per-module automation/ coverage scan:
      `python -m pytest tests/unit/ --cov=automation --cov-report=term-missing --timeout=60 -q 2>&1 | grep -E "automation/|TOTAL" | sort -t'%' -k1 -n`
      List every module and its current % in a working notes doc.
  5.  Run per-module src/ coverage scan:
      `python -m pytest tests/unit/ --cov=src --cov-report=term-missing --timeout=60 -q 2>&1 | grep -E "src/|TOTAL" | sort -t'%' -k1 -n`
  6.  For EVERY automation/ module below 90%: read the module, identify untested
      branches (marked with `# pragma: no cover` or missing from term-missing output),
      write targeted tests in tests/unit/test_{module}.py. Each new test must be
      specific and meaningful — not trivial assertions.
  7.  For EVERY src/ module below 80%: write targeted tests similarly.
  8.  After each batch of new tests, run: `python -m pytest tests/unit/test_{module}.py
      --cov=automation.{module} --cov-report=term-missing --timeout=30 -q` to confirm improvement.
  9.  Pay special attention to: `ai_cycle_controller.py`, `run_agent_lifecycle.py`,
      `validation_runner.py`, `claude_post_cycle_adapter.py`, `jira_sync.py`, `git_adapter.py`
      — these are the most critical modules for autonomous operation.
  10. Run the full combined gate: `python -m pytest tests/unit/ --cov=automation --cov=src
      --cov-fail-under=90 --cov-report=term-missing --timeout=60 -q 2>&1 | tail -25`
      MUST pass. If not: add more tests and retry.
  11. Run `python -m ruff check tests/ -q --fix` — fix any ruff issues in new test files.
  12. Run `python -m mypy automation/ --ignore-missing-imports -q` — 0 errors required.
  13. Write `docs/cycle_reports/CYCLE_077_COVERAGE_FINAL.md` — per-module breakdown,
      combined %, confirmation of >=90% gate pass.
  14. Commit: `git add tests/ docs/ && git commit -m "test(coverage): all modules >=90% combined, production coverage FINAL"`

====================================================================

TASK 2 — GO-LIVE STAGE 2: FIRST REAL CURSOR AGENT DISPATCH (LARGE, ~90 min)
Deliverable: OPS-031 DONE; DOD-008 DONE; `docs/validation/GO_LIVE_STAGE_2_EVIDENCE.md` PASS.
This is the first time the controller dispatches a REAL Cursor agent.

  1.  Read `PM_Pack/automation/prompts/CURSOR_DOCS_ONLY_SMOKE_PROMPT.md` in full.
      If it doesn't exist: write it — a docs-only prompt that asks Agent D to
      write a single markdown file `docs/stage2_test_output.md` with content
      "Stage 2 test completed on {timestamp}" and AGENT_COMPLETE in the body.
  2.  Create Stage 2 test branch:
      `git checkout -b test/stage2-live-$(date +%Y%m%d%H%M) && git push origin test/stage2-live-$(date +%Y%m%d%H%M)`
  3.  Run the cursor-smoke preflight: `python automation/ai_cycle_controller.py cursor-smoke`
      Must return PASS. If FAIL: diagnose Cursor CLI path, re-run, fix.
  4.  Dispatch Agent D docs-only on the test branch — LIVE MODE:
      `python automation/ai_cycle_controller.py run-agent --cycle 077-stage2 --agent D --prompt PM_Pack/automation/prompts/CURSOR_DOCS_ONLY_SMOKE_PROMPT.md --branch test/stage2-live-{timestamp} --live 2>&1 | tee C:/AI_Runner/logs/stage2_dispatch.log`
  5.  Monitor: poll status every 30 seconds for up to 20 minutes:
      `python automation/ai_cycle_controller.py status --live 2>&1`
      If the controller shows the agent is running, wait. If stuck > 20 min: record
      the failure with the exact error and note in the evidence file.
  6.  After completion: check `git log --oneline test/stage2-live-{timestamp} -5`
      Verify the agent committed `docs/stage2_test_output.md` with AGENT_COMPLETE.
  7.  Read the agent output: `cat docs/stage2_test_output.md`
      Confirm AGENT_COMPLETE is present in the file.
  8.  Verify no src/ files were modified: `git diff develop test/stage2-live-{timestamp} -- src/ | wc -l`
      Must be 0 (docs-only prompt must produce only docs changes).
  9.  Clean up: `git push origin --delete test/stage2-live-{timestamp}`
      `git branch -D test/stage2-live-{timestamp}`
  10. Write `docs/validation/GO_LIVE_STAGE_2_EVIDENCE.md`:
      - Dispatch command and timestamp
      - Agent output file confirmed
      - AGENT_COMPLETE: YES/NO
      - No src/ changes: YES/NO
      - Verdict: PASS or FAIL with reason
  11. Mark OPS-031 DONE and DOD-008 DONE.
  12. Commit: `git add docs/validation/ && git commit -m "feat(stage2): Go-Live Stage 2 PASS — first real Cursor dispatch"`

====================================================================

TASK 3 — GO-LIVE STAGE 3: FULL CYCLE ALL 6 AGENTS NO AUTO-MERGE (LARGE, ~90 min)
Deliverable: OPS-032 DONE; `docs/validation/GO_LIVE_STAGE_3_EVIDENCE.md` PASS;
merge-gate --dry-run PASS or CONDITIONAL_GO.

  1.  Create Stage 3 test branch from develop:
      `git checkout develop && git pull && git checkout -b test/stage3-fullcycle-$(date +%Y%m%d%H%M)`
      `git push origin test/stage3-fullcycle-$(date +%Y%m%d%H%M)`
  2.  Create a minimal Jira story for Stage 3 (if needed):
      `python -c "from automation.jira_client import JiraClient; j=JiraClient(); r=j.create_issue({'summary': 'Stage 3 smoke story', 'issuetype': {'name': 'Story'}, 'project': {'key': 'SCRUM'}}); print(r['key'])"`
  3.  Run plan-cycle for the stage 3 test: `python automation/ai_cycle_controller.py plan-cycle --cycle 077-stage3 --live`
  4.  Run validate-prompts: `python automation/ai_cycle_controller.py validate-prompts --cycle 077-stage3`
  5.  Dispatch all 6 agents in order using real Cursor CLI. Use short docs-only prompts:
      - Agent A: `run-agent --cycle 077-stage3 --agent A --live` — write AGENT_A_STAGE3.md
      - Agent B: `run-agent --cycle 077-stage3 --agent B --live` — write AGENT_B_STAGE3.md
      - Agent E: `run-agent --cycle 077-stage3 --agent E --live` — write AGENT_E_STAGE3.md
      - Agent C: `run-agent --cycle 077-stage3 --agent C --live` — write AGENT_C_STAGE3.md
      - Agent F: `run-agent --cycle 077-stage3 --agent F --live` — write AGENT_F_STAGE3.md
      - Agent D: `run-agent --cycle 077-stage3 --agent D --live` — write AGENT_D_STAGE3.md
      Each must produce AGENT_COMPLETE before next starts (check file before proceeding).
  6.  After all 6 complete: run PR creation (without merging):
      `gh pr create --base develop --head test/stage3-fullcycle-{timestamp} --title "stage3: full cycle test" --body "Go-Live Stage 3 test — all 6 agents completed"`
  7.  Run merge gate dry-run: `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077-stage3 2>&1 | tee docs/validation/STAGE3_MERGE_GATE_RESULT.txt`
  8.  Run Jira sync: `python automation/ai_cycle_controller.py jira-sync --cycle 077-stage3 --dry-run`
      Verify comments would be posted to the right stories.
  9.  Verify NO auto-merge occurred: `gh pr view {PR_NUMBER} --json state` must show "OPEN".
  10. Write `docs/validation/GO_LIVE_STAGE_3_EVIDENCE.md`:
      - All 6 agents: AGENT_COMPLETE present for each
      - PR created: YES, number
      - Merge gate dry-run: PASS or CONDITIONAL_GO
      - No auto-merge: YES
      - Verdict: PASS or FAIL
  11. Clean up: `gh pr close {PR_NUMBER}` and delete test branch.
  12. Mark OPS-032 DONE.
  13. Commit: `git add docs/validation/ && git commit -m "feat(stage3): Go-Live Stage 3 PASS — 6 agents, PR, merge gate"`

====================================================================

TASK 4 — GJCI-032 AUTO-MERGE EXECUTION + BUG-011 BRANCH PROTECTION (LARGE, ~60 min)
Deliverable: GJCI-032 DONE — real PR merge executed; BUG-011 documented precisely.

  1.  Check if PR #88 is merged yet: `gh pr view 88 --json state,mergedAt`.
  2.  If NOT merged: attempt merge with admin flag:
      `gh pr merge 88 --squash --admin 2>&1`
      Capture the result. If this succeeds: GJCI-032 is DONE.
  3.  If --admin fails (requires repo admin account): attempt to enable auto-merge at
      repo level by updating the repo setting:
      `gh api -X PATCH /repos/KevinSGarrett/Fiverr -f allow_auto_merge=true 2>&1`
      If that succeeds: `gh pr merge 88 --squash --auto`
  4.  If all merge attempts fail due to branch protection or permissions: create a minimal
      test PR on a non-protected branch to prove the merge-gate --execute-merge code works:
      `git checkout -b test/auto-merge-$(date +%Y%m%d%H%M) && echo "test" >> docs/auto_merge_test.md`
      `git add docs/auto_merge_test.md && git commit -m "test: auto-merge proof" && git push origin test/auto-merge-{timestamp}`
      `gh pr create --base cycle/077/integration --head test/auto-merge-{timestamp} --title "test: auto-merge" --body "Auto-merge mechanism test"`
      `python automation/ai_cycle_controller.py merge-gate --execute-merge --pr {NUMBER} 2>&1 | tee docs/validation/GJCI_032_AUTO_MERGE_EVIDENCE.txt`
  5.  Capture the merge-gate --execute-merge output regardless of which path above was taken.
  6.  Write `docs/validation/GJCI_032_AUTO_MERGE_EVIDENCE.md` with exact results.
  7.  For BUG-011: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection 2>&1`
      Try with GH_TOKEN explicitly: `GH_TOKEN=$(grep GH_AUTOMATION_TOKEN C:/AI_Runner/secrets/runner.env | cut -d= -f2) gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection`
      Document exact HTTP status and error body.
      Determine the exact OAuth scope needed: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection -i 2>&1 | head -5`
      Write `docs/governance/BUG_011_BRANCH_PROTECTION_DIAGNOSIS.md` with: exact error,
      required scope (likely `administration` or `repo` with admin access), exact remediation steps.
  8.  Commit all evidence.

====================================================================

TASK 5 — DOD-009 REPAIR LOOP PRODUCTION TEST (LARGE, ~55 min)
Deliverable: DOD-009 DONE; repair loop fires on simulated failure, recovers, writes incident.

  1.  Read `automation/repair_loop.py` to understand the trigger → detect → repair flow.
  2.  Identify the smallest valid repair trigger: a simulated ruff lint failure or missing
      heartbeat. Write the trigger state file:
      `python -c "import json, pathlib; pathlib.Path(r'C:/AI_Runner/state/repair_trigger_test.json').write_text(json.dumps({'trigger': 'LINT_FAIL', 'module': 'test_module', 'cycle': 77}))"`
  3.  Run the repair loop with the trigger:
      `python -c "from automation.repair_loop import RepairLoop; r=RepairLoop(); result=r.handle(r'C:/AI_Runner/state/repair_trigger_test.json'); print(result)"
      Capture full output including what repair actions were planned.
  4.  Verify the repair loop wrote an incident file:
      `ls C:/AI_Runner/reports/incidents/ -t | head -3`
      Read the newest incident: `cat C:/AI_Runner/reports/incidents/{newest}.json`
  5.  Verify the notification router was called (check logs):
      `cat C:/AI_Runner/logs/notification_*.log 2>/dev/null | tail -10`
  6.  Run a broader repair scenario — simulate a stale heartbeat:
      `python -c "import json, pathlib, datetime; hb=pathlib.Path(r'C:/AI_Runner/state/heartbeat.json'); old=json.loads(hb.read_text()); old['timestamp']='2026-06-01T00:00:00'; hb.write_text(json.dumps(old))"`
      `python automation/ai_cycle_controller.py status-tick 2>&1 | tail -10`
      Verify watchdog/repair detects the stale heartbeat.
      Restore: `python automation/ai_cycle_controller.py tick`
  7.  Clean up trigger file. Write `docs/validation/DOD_009_REPAIR_LOOP_EVIDENCE.md`.
  8.  Mark DOD-009 DONE. Commit.

====================================================================

TASK 6 — JIRA COMPLETE SYNC + GJCI-029/034/035 EVIDENCE (MEDIUM, ~40 min)
Deliverable: GJCI-029, GJCI-034, GJCI-035 evidenced; all Cycle 077-B stories transitioned.

  1.  Post coverage completion evidence to Cycle 077 coverage stories.
  2.  Post Stage 2 and Stage 3 PASS evidence to their respective Jira stories.
  3.  For GJCI-029 (Transition to Done after merge/full DoD): write evidence that the full
      DoD check logic is implemented in merge_gate.py and verify it runs correctly:
      `python -c "from automation.merge_gate import MergeGate; mg=MergeGate(); print(mg.check_full_dod(77))"`
      Write `docs/validation/GJCI_029_DOD_MERGE_GATE_EVIDENCE.md`.
  4.  For GJCI-034 (Post-cycle GitHub bundle): run:
      `python -c "from automation.post_cycle_review import generate_post_cycle_github_bundle; from automation.github_client import GitHubClient; c=GitHubClient(); b=generate_post_cycle_github_bundle(77, 'cycle/077/integration', c); print(list(b.keys()))" 2>&1`
      Write `docs/validation/GJCI_034_GITHUB_BUNDLE_EVIDENCE.md`.
  5.  For GJCI-035 (Post-cycle Jira bundle): run:
      `python -c "from automation.post_cycle_review import generate_post_cycle_jira_bundle; from automation.jira_client import JiraClient; j=JiraClient(); b=generate_post_cycle_jira_bundle(77, j); print(list(b.keys()))" 2>&1`
      Write `docs/validation/GJCI_035_JIRA_BUNDLE_EVIDENCE.md`.
  6.  Commit all evidence.

====================================================================

TASK 7 — FINAL COMMIT, PUSH, CYCLE REPORT (MEDIUM, ~30 min)

  1.  Final validation:
      `python -m ruff check automation/ src/ tests/ -q` — 0 errors
      `python -m mypy automation/ --ignore-missing-imports -q` — 0 errors
      `python automation/ai_cycle_controller.py brain-check` — PASS
      `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5` — PASS
  2.  `git status` — clean. `git push origin cycle/077/integration`
  3.  Write `docs/cycle_reports/CYCLE_077_AGENT_B.md`:
      - Coverage: all modules >=90%, combined %
      - Stage 2 (OPS-031, DOD-008): PASS/FAIL
      - Stage 3 (OPS-032): PASS/FAIL
      - GJCI-032 auto-merge: result
      - BUG-011: diagnosis and status
      - DOD-009 repair loop: PASS/FAIL
      - GJCI-029/034/035: evidenced
      - Jira: N transitions
      - AGENT_COMPLETE
  4.  Commit and push cycle report.

VALIDATION (R-092 Tier 1)
python -m ruff check automation/ src/ tests/ -q
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5

END OF PROMPT

Agent C may proceed after BOTH Agent B AND Agent E report AGENT_COMPLETE.
