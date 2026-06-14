====================================================================
FIVERR 24/7 AUTONOMOUS RUNNER — CYCLE 077 AGENT F
Policy v4.5 / POST_CYCLE_PM_REVIEW_v4
Prerequisite: AGENT_COMPLETE in docs/cycle_reports/CYCLE_077_AGENT_C.md
Runs FOURTH after C completes.
====================================================================

AGENT F ROLE
F is the final hardening agent before close-out. F executes Go-Live Stage 6
(official post-cycle PM review trial), raises src/ coverage to >=80% combined
passing threshold, builds the Stage 7 24-hour observation scaffold, and
completes ALL remaining IN_PROGRESS checklist items (OPS-004/008/009/010/022/023
if not done by A, MODEL-008/013/014 if remaining, DOD-004/007/011/012/013).

NEVER-BREAK RULES
1. data/cycle037_live.db NEVER modify
2. Stage 6 requires at least 5 of 6 agent reports to be present
3. Stage 7 scaffold must be tested for 2 minutes minimum before marking done

====================================================================

TASK 1 — PREFLIGHT + COVERAGE GAP FINAL PASS (LARGE, ~75 min)
Deliverable: Combined src/+automation/ coverage >=90% confirmed; all gap modules >=80%.

  1.  `git checkout cycle/077/integration && git pull origin cycle/077/integration`
  2.  Confirm AGENT_COMPLETE in CYCLE_077_AGENT_C.md.
  3.  Run combined coverage check: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -15`
      If PASS: document the current per-module breakdown and proceed. If FAIL: fix.
  4.  Run src/-only coverage scan: `python -m pytest tests/unit/ --cov=src --cov-report=term-missing --timeout=60 -q 2>&1 | grep "src/" | sort -t'%' -k1 -n`
  5.  For every src/ module below 75%: write targeted tests to bring it above 75%.
      Focus first on: src/scoring/ modules, src/collection/ modules, src/analysis/ modules.
  6.  After each batch: run `python -m pytest tests/unit/test_{module}.py --cov=src.{module} --cov-report=term-missing --timeout=30 -q`
  7.  Re-run full combined: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5` — MUST PASS.
  8.  Run `python -m ruff check tests/ -q --fix` on any new test files.
  9.  Write `docs/cycle_reports/CYCLE_077_COVERAGE_FINAL_F.md` — per-module breakdown.
  10. Commit: `git add tests/ docs/ && git commit -m "test(coverage): src/ coverage final pass, Agent F"`

====================================================================

TASK 2 — GO-LIVE STAGE 6: OFFICIAL POST-CYCLE PM REVIEW TRIAL (LARGE, ~80 min)
Deliverable: OPS-035 DONE; DOD-012 DONE; BRAIN-021 fully evidenced; MODEL-008 DONE.

  1.  Verify all 5 prior agent reports are present (A, B, E, C, and F-in-progress):
      `ls docs/cycle_reports/CYCLE_077_AGENT_*.md`
  2.  Read POST_CYCLE_PM_REVIEW_v4.md in full to understand the official review format.
  3.  Run official post-cycle review in advisory mode:
      `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode advisory 2>&1 | tee docs/validation/GO_LIVE_STAGE_6_ADVISORY_LOG.txt`
      Capture full output. Note: status should be PASS or ADVISORY_ONLY.
  4.  Read the output carefully — if BLOCKED_MISSING_AGENT_REPORT: note which report is missing
      and create a minimal placeholder report to unblock, then re-run.
  5.  Verify dispatch decision JSON was written:
      `python -c "import json; d=json.load(open(r'C:/AI_Runner/state/next_cycle_dispatch_decision.json')); print('blocks_dispatch:', d.get('blocks_dispatch'), 'status:', d.get('review_result'))"`
      blocks_dispatch must be False (or ADVISORY_ONLY which still allows dispatch).
  6.  Run in POST_MERGE mode: `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge 2>&1 | tee docs/validation/GO_LIVE_STAGE_6_POST_MERGE_LOG.txt`
  7.  Read the Claude model verification section from the post-merge output — this evidences MODEL-008.
      Write `docs/validation/MODEL_008_CLAUDE_MODEL_VERIFICATION.md` with the output section.
  8.  Verify BRAIN-021 (review orchestrator): the post-cycle-review ran and collected all facts.
      `python -c "import json; d=json.load(open('C:/AI_Runner/runs/CYCLE_077/post_cycle_result.json') if pathlib.Path('C:/AI_Runner/runs/CYCLE_077/post_cycle_result.json').exists() else open('C:/AI_Runner/state/next_cycle_dispatch_decision.json')); print(list(d.keys()))"`
      Write `docs/validation/GO_LIVE_STAGE_6_EVIDENCE.md`:
      - Advisory mode status
      - Post-merge mode status
      - blocks_dispatch: False
      - Model verification artifact present
      - Verdict: PASS
  9.  Mark OPS-035, DOD-012, BRAIN-021, MODEL-008 DONE.
  10. Commit.

====================================================================

TASK 3 — GO-LIVE STAGE 7 SCAFFOLD: 24-HOUR OBSERVATION (LARGE, ~70 min)
Deliverable: OPS-036 scaffold DONE; start/stop scripts tested; 2-minute live test PASS.

  1.  Write `C:/AI_Runner/scripts/start_24h_observation.ps1`:
      - Parameters: -TestMode (bool), -Duration (int, default 86400 seconds)
      - Logs to C:/AI_Runner/logs/observation_{timestamp}.log
      - Every 300 seconds: runs `python automation/ai_cycle_controller.py status-tick`
      - On HEALTH != GREEN: runs `python automation/ai_cycle_controller.py repair --trigger health_degraded --live`
      - Sends Slack notification via notification_router
      - On -TestMode: runs for -Duration seconds only, then exits cleanly
      - Writes final summary to C:/AI_Runner/reports/observation_summary_{timestamp}.json
  2.  Write `C:/AI_Runner/scripts/stop_observation.ps1`:
      - Reads observation PID from C:/AI_Runner/state/observation_pid.txt
      - Sends SIGTERM gracefully, waits 30s, then SIGKILL if needed
      - Writes final health summary
  3.  Write `C:/AI_Runner/scripts/check_observation_health.ps1`:
      - Reads latest observation log, checks for any ERROR or CRITICAL entries
      - Prints summary: uptime, tick count, errors, status
  4.  Test the scaffold for 120 seconds:
      `powershell -File C:/AI_Runner/scripts/start_24h_observation.ps1 -TestMode -Duration 120 2>&1 | tee docs/validation/STAGE7_2MIN_TEST.txt`
      Verify: started, logged 2+ status-tick outputs, exited cleanly.
  5.  Verify observation_summary_{ts}.json was written:
      `cat C:/AI_Runner/reports/observation_summary_*.json | head -20`
  6.  Write `docs/validation/GO_LIVE_STAGE_7_SCAFFOLD_EVIDENCE.md`:
      - Scripts written: start/stop/check (3 files)
      - 2-minute test: PASS/FAIL
      - Summary JSON: written
      - Instructions for starting real 24-hour observation
      - Verdict: SCAFFOLD_READY
  7.  Mark OPS-036 as SCAFFOLD_READY (not DONE — full DONE requires the actual 24h run).
  8.  Commit: `git add C:/AI_Runner/scripts/ docs/validation/ && git commit -m "feat(stage7): 24h observation scaffold PASS, start/stop/check scripts tested"`

====================================================================

TASK 4 — COMPLETE ALL REMAINING IN_PROGRESS CHECKLIST ITEMS (LARGE, ~65 min)
Deliverable: Every IN_PROGRESS item that can be completed without live multi-cycle
operation is moved to DONE.

  1.  DOD-004 model gate — confirm from Agent C evidence. If model expiry < 24h: write
      CRITICAL_BLOCK doc. Otherwise write PASS evidence.
  2.  DOD-007 prompt validation — confirm from Agent A (Stage 1 evidence). Mark DONE.
  3.  DOD-011 Jira sync — confirm from Agent B (Jira transitions evidence). Mark DONE.
  4.  DOD-012 post-cycle review — just completed in Task 2. Mark DONE.
  5.  DOD-013 watchdog recovery — already DONE from Cycle 075. Verify evidence still valid.
  6.  MODEL-013 drift detection — confirm from Agent A evidence. Mark DONE.
  7.  MODEL-014 daily report model section — confirm from Agent A evidence. Mark DONE.
  8.  OPS-004 watchdog live — confirm from Agent A evidence. Mark DONE.
  9.  OPS-008 daily snapshot — confirm from Agent A evidence. Mark DONE.
  10. OPS-009 weekly maintenance — confirm from Agent A evidence. Mark DONE.
  11. OPS-010 Slack notifications — confirm from Agent A evidence. Mark DONE or NEEDS_WEBHOOK_URL.
  12. OPS-022 daily report production — confirm from Agent A evidence. Mark DONE.
  13. OPS-023 weekly report production — confirm from Agent A evidence. Mark DONE.
  14. OPS-030 Stage 1 manual dry-run — confirm from Agent A evidence. Mark DONE.
  15. OPS-031 Stage 2 — confirm from Agent B evidence. Mark DONE.
  16. OPS-032 Stage 3 — confirm from Agent B evidence. Mark DONE.
  17. OPS-033 Stage 4 — confirm from Agent C evidence. Mark DONE.
  18. OPS-034 Stage 5 — confirm from Agent C evidence. Mark DONE.
  19. OPS-035 Stage 6 — just completed. Mark DONE.
  20. BRAIN-021 review orchestrator — confirm from this task's Stage 6 run. Mark DONE.
  21. GJCI-029/030/032/034/035 — confirm from Agents B/C evidence. Mark DONE.
  22. Write `docs/validation/FINAL_CHECKLIST_C077_STATUS.md` — every item that changed
      status this cycle, with evidence file paths.
  23. Commit: `git add docs/ && git commit -m "docs(checklist): all completable IN_PROGRESS items resolved, evidence documented"`

====================================================================

TASK 5 — PM_PACK FINAL STATE SYNC + GO-LIVE SUMMARY (MEDIUM, ~40 min)

  1.  Update PRODUCTION_READINESS_SCORECARD.md:
      Score 1 recalculate: with Stages 2-6 PASS + all remaining items DONE,
      count (DONE items / total non-deferred items). Estimate ~80-82%.
      Score 2: from Agent E (47.1% + V-credits, ~53.1%). TierD-2 cap: REMOVED.
  2.  Update Go-Live stage table in CURRENT_STATE_CANONICAL.md:
      Stage 0=COMPLETE, 1=PASS, 2=PASS, 3=PASS, 4=PASS, 5=PASS, 6=PASS,
      7=SCAFFOLD_READY, 8=NOT_STARTED.
  3.  Update HYDRATION_HEADER.md: clear all resolved blockers; only BUG-011, BUG-012
      (cursor model expiry), and PENDING-001 (CODECOV_TOKEN) remain.
  4.  Run `python automation/ai_cycle_controller.py pm-pack-audit` — PASS required.
  5.  Write `docs/validation/GO_LIVE_STAGES_2_6_SUMMARY.md` — table of all 5 stages with
      evidence file paths, PASS/FAIL, and timestamp.
  6.  Commit: `git add PM_Pack/ docs/ && git commit -m "state(pm-pack): final Agent F state sync, Stages 2-6 summary"`

====================================================================

TASK 6 — JIRA TRANSITIONS + EVIDENCE COMMENTS (MEDIUM, ~35 min)

  1.  Transition all stories completed by F: Stage 6, Stage 7 scaffold, coverage, OPS items.
  2.  Post Stage 6 evidence (dispatch decision JSON path) on the Stage 6 Jira story.
  3.  Post Stage 7 scaffold evidence on the Stage 7 Jira story. Explain that the full
      24-hour observation run happens when Kevin runs start_24h_observation.ps1.
  4.  Write `docs/cycle_reports/CYCLE_077_AGENT_F_JIRA.md`.
  5.  Commit.

====================================================================

TASK 7 — FINAL COMMIT, PUSH, CYCLE REPORT (MEDIUM, ~25 min)

  1.  Final validation:
      `python -m ruff check automation/ src/ tests/ -q`
      `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5`
      `python automation/ai_cycle_controller.py brain-check`
      `python automation/ai_cycle_controller.py pm-pack-audit`
  2.  `git status` — clean. `git push origin cycle/077/integration`
  3.  Write `docs/cycle_reports/CYCLE_077_AGENT_F.md`:
      - Coverage: combined %, all modules final breakdown
      - Stage 6 (OPS-035, DOD-012): PASS/FAIL
      - Stage 7 scaffold: SCAFFOLD_READY
      - Stage 7 2-minute test: PASS/FAIL
      - IN_PROGRESS items resolved: full list
      - Score 1: ~{new}% | Score 2: ~53.1% | TierD-2: REMOVED
      - Go-Live stages 2-7: summary table
      - Remaining open: BUG-011, BUG-012, PENDING-001, OPS-036 (needs live run), OPS-037
      - AGENT_COMPLETE
  4.  Commit and push.

VALIDATION (R-092 Tier 2)
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077

END OF PROMPT

Agent D may proceed after Agent F reports AGENT_COMPLETE.
