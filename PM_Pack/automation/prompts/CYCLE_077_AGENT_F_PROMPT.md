# CYCLE 077 AGENT F PROMPT
# Branch: cycle/077/integration
# Prerequisite: AGENT_COMPLETE confirmed in docs/cycle_reports/CYCLE_077_AGENT_C.md
# Agent F runs FOURTH — final hardening pass + Go-Live Stages 6/7 preparation.

---

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight, read Agent C report
- Task 2 (LARGE): 75 min — Go-Live Stage 6: post-cycle review trial (official PM review)
- Task 3 (LARGE): 70 min — Raise src/ coverage + complete final quality pass
- Task 4 (MEDIUM): 50 min — Go-Live Stage 7 setup: 24-hour observation scaffolding
- Task 5 (MEDIUM): 40 min — Complete remaining IN_PROGRESS and BLOCKED checklist items
- Task 6 (MEDIUM): 25 min — Jira transitions
- Task 7 (SMALL): 15 min — Commit, push, cycle report
Total estimated: ~4 hr 50 min

---

## Context

Agent C has completed: Go-Live Stages 2-5 PASS, integration verified, all NEEDS_EVIDENCE resolved. You are the final hardening agent before Agent D's post-cycle close-out. Your primary goals are: (1) Go-Live Stage 6 (official post-cycle PM review trial), (2) raise src/ coverage to ≥90%, and (3) complete all remaining IN_PROGRESS and BLOCKED checklist items that can be resolved programmatically.

---

## Task 1 (SMALL, ~15 min): Preflight

Sub-steps:
1. Confirm AGENT_COMPLETE in `docs/cycle_reports/CYCLE_077_AGENT_C.md`.
2. `git checkout cycle/077/integration && git pull origin cycle/077/integration`.
3. `python automation/ai_cycle_controller.py brain-check` — must PASS.
4. Read Agent C report for Stage 4/5 outcomes and any remaining blockers.
5. Run `grep -rn "IN_PROGRESS\|BLOCKED\|NEEDS_EVIDENCE" docs/` to catalog remaining items.

---

## Task 2 (LARGE, ~75 min): Go-Live Stage 6 — Official Post-Cycle PM Review Trial

Deliverable: `OPS-035` moved to DONE; `docs/validation/GO_LIVE_STAGE_6_EVIDENCE.md` written with PASS.

Sub-steps:
1. Read `PM_Pack/01_pm_instructions/POST_CYCLE_PM_REVIEW_v4.md` to understand the official review process.
2. Verify all 6 agent reports exist in `docs/cycle_reports/`: CYCLE_077_AGENT_A.md through E.md (F is being written now — use the C report as the prior complete agent).
3. Run the official post-cycle review in advisory mode: `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode advisory 2>&1 | tee docs/validation/GO_LIVE_STAGE_6_REVIEW_LOG.txt`.
4. Read the review output: check for `status=PASS`, `status=ADVISORY_ONLY`, or `status=BLOCKED_*`.
5. If status=ADVISORY_ONLY: note the advisory items. The review passes for Stage 6 purposes if ADVISORY_ONLY (no hard blocks).
6. If status=BLOCKED_*: diagnose the blocking condition. Fix if possible (e.g., missing agent report, missing dispatch decision JSON).
7. Verify the review wrote `C:\AI_Runner\state\next_cycle_dispatch_decision.json`: `python -c "import json; d=json.load(open(r'C:\AI_Runner\state\next_cycle_dispatch_decision.json')); print('blocks_dispatch:', d.get('blocks_dispatch'))"`.
8. Run the review a second time in POST_MERGE mode to confirm it works for the final integration: `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge 2>&1 | tail -10`.
9. Write `docs/validation/GO_LIVE_STAGE_6_EVIDENCE.md` with: review mode, status, blocks_dispatch value, advisory items, overall verdict.
10. Commit evidence.

---

## Task 3 (LARGE, ~70 min): Raise src/ Coverage + Final Quality Pass

Deliverable: All src/ modules ≥80% coverage; combined automation+src ≥90%; 0 ruff/mypy errors.

Sub-steps:
1. Run per-module src/ coverage: `python -m pytest tests/unit/ --cov=src --cov-report=term-missing --timeout=60 -q 2>&1 | grep "src/" | sort -k4 -n`.
2. Identify all src/ modules below 80% coverage.
3. For each src/ module below 80%: write targeted unit tests in `tests/unit/test_{module_name}.py`.
4. Focus on: `src/scoring/`, `src/collection/`, `src/analysis/` sub-modules with lowest coverage.
5. After each new test file, verify coverage improvement: `python -m pytest tests/unit/test_{module}.py --cov=src.{module} --cov-report=term-missing --timeout=30 -q`.
6. Run combined check: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10` — must PASS.
7. Run ruff on all new test files: `python -m ruff check tests/ -q --fix`.
8. Run mypy on automation/: `python -m mypy automation/ --ignore-missing-imports -q` — 0 errors.
9. Commit: `git add tests/ && git commit -m "test(coverage): raise src/ modules to >=80%, combined >=90%"`.

---

## Task 4 (MEDIUM, ~50 min): Go-Live Stage 7 — 24-Hour Observation Scaffolding

Deliverable: `OPS-036` setup complete; `C:\AI_Runner\scripts\start_24h_observation.ps1` written and tested; `docs/validation/GO_LIVE_STAGE_7_SCAFFOLD.md` written.

Sub-steps:
1. Write `C:\AI_Runner\scripts\start_24h_observation.ps1`:
   - Script that starts the runner in continuous mode
   - Logs to `C:\AI_Runner\logs\observation_{timestamp}.log`
   - Runs `python automation/ai_cycle_controller.py status-tick` every 5 minutes
   - Sends notification via `notification_router` on any HEALTH != GREEN
   - Runs for exactly 24 hours then exits cleanly
2. Write `C:\AI_Runner\scripts\stop_observation.ps1`:
   - Cleanly stops the observation run
   - Writes final health summary to `C:\AI_Runner\reports\observation_summary_{timestamp}.json`
3. Test the scaffolding for 2 minutes: `powershell -File C:\AI_Runner\scripts\start_24h_observation.ps1 -TestMode -Duration 120` — verify it starts, ticks, and logs correctly.
4. Write `docs/validation/GO_LIVE_STAGE_7_SCAFFOLD.md`:
   - Scripts written: start_24h_observation.ps1, stop_observation.ps1
   - Test run result (2-minute test)
   - Instructions for starting the real 24-hour observation
   - Verdict: SCAFFOLD_READY (full 24-hour run requires Kevin to start)
5. Commit scripts and evidence.

---

## Task 5 (MEDIUM, ~40 min): Complete Remaining IN_PROGRESS and BLOCKED Items

Deliverable: Maximum possible checklist items moved to DONE.

Sub-steps:
1. `ENV-026` (runner as Windows service): verify status from Agent A's work. If not done, complete it now.
2. `DOD-010` (PR lifecycle): if PR #88 is merged and CI passed on develop, mark as DONE and write evidence.
3. `DOD-012` (post-cycle review trial): covered by Task 2 (Stage 6). Mark DONE with evidence.
4. `DOD-015` (24h observation): SCAFFOLD_READY from Task 4. Mark as NEEDS_LIVE_EXECUTION with scaffold evidence.
5. `OPS-031/032/033/034/035`: covered by Stages 2-6. Write unified evidence doc `docs/validation/GO_LIVE_STAGES_2_THROUGH_6_SUMMARY.md`.
6. Verify `AUDIT-P1-014` (merge gate hardened): run `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077` and capture full output as evidence.
7. Verify `AUDIT-P1-015` (health/status truth model): run `python automation/ai_cycle_controller.py status-tick` and capture the JSON output as evidence.
8. Write `docs/validation/FINAL_CHECKLIST_STATUS_CYCLE_077.md` — list every item that changed status this cycle.
9. Commit all evidence and status files.

---

## Task 6 (MEDIUM, ~25 min): Jira Transitions

Sub-steps:
1. Transition all stories completed by Tasks 2-5 to Done.
2. Stories: "Go-Live Stage 6", "Go-Live Stage 7 scaffolding", coverage improvements, remaining IN_PROGRESS items.
3. Post evidence file paths as comments.
4. Write `docs/cycle_reports/CYCLE_077_AGENT_F_JIRA.md`.

---

## Task 7 (SMALL, ~15 min): Commit, Push, Cycle Report

Sub-steps:
1. Final `git status` — clean.
2. Final combined coverage check: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -5`.
3. `git push origin cycle/077/integration`.
4. Write `docs/cycle_reports/CYCLE_077_AGENT_F.md`:
   - Go-Live Stage 6: status and verdict
   - Coverage final state: combined %, per-module breakdown
   - Stage 7 scaffolding: SCAFFOLD_READY
   - Remaining checklist items resolved: N
   - Go-Live stages 2-6: all PASS/FAIL summary
   - AGENT_COMPLETE
5. Commit and push.

---

## Validation (R-092 Tier 2)
```
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077
```

---

## END OF PROMPT

AGENT_COMPLETE is written at the end of `docs/cycle_reports/CYCLE_077_AGENT_F.md`.
Agent D may proceed after Agent F reports AGENT_COMPLETE.
