# CYCLE 077 AGENT C PROMPT
# Branch: cycle/077/integration
# Prerequisite: AGENT_COMPLETE confirmed in BOTH CYCLE_077_AGENT_B.md AND CYCLE_077_AGENT_E.md
# Agent C runs THIRD — integration verification after B+E complete.

---

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight, read B+E reports
- Task 2 (LARGE): 75 min — Full integration verification: CI, coverage, V-1 evidence, stage 2/3 results
- Task 3 (LARGE): 70 min — Go-Live Stage 4: forced repair loop test
- Task 4 (MEDIUM): 45 min — Go-Live Stage 5: auto-merge trial (dry-run + live)
- Task 5 (MEDIUM): 35 min — Resolve all NEEDS_EVIDENCE items
- Task 6 (MEDIUM): 25 min — Jira transitions + evidence comments
- Task 7 (SMALL): 15 min — Commit, push, cycle report
Total estimated: ~4 hr 40 min

---

## Context

Agents B and E have completed. Coverage is ≥90%, CI is green, V-1/V-2/V-3 PASS, TierD-2 cap removed, Go-Live Stages 2 and 3 PASS. You are responsible for: (1) verifying the full integration is consistent, (2) executing Go-Live Stage 4 (forced repair), and (3) executing Go-Live Stage 5 (auto-merge trial), and (4) resolving all NEEDS_EVIDENCE items in the checklist.

---

## Task 1 (SMALL, ~15 min): Preflight

Sub-steps:
1. Confirm AGENT_COMPLETE in `docs/cycle_reports/CYCLE_077_AGENT_B.md`.
2. Confirm AGENT_COMPLETE in `docs/cycle_reports/CYCLE_077_AGENT_E.md`.
3. `git checkout cycle/077/integration && git pull origin cycle/077/integration`.
4. Run brain-check: `python automation/ai_cycle_controller.py brain-check` — must PASS.
5. Read Agent B report for coverage results and Stage 2/3 outcomes.
6. Read Agent E report for V-1/V-2/V-3 outcomes and Score 2 new value.
7. Verify `data/live_validation_evidence.json` exists and shows v1_status=PASS.

---

## Task 2 (LARGE, ~75 min): Full Integration Verification

Deliverable: `docs/validation/CYCLE_077_INTEGRATION_VERIFICATION.md` with all checks PASS.

Sub-steps:
1. Run the complete test suite: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing --cov-fail-under=90 --timeout=60 -q 2>&1 | tail -20`. Document result.
2. Run `python -m ruff check automation/ src/ tests/ -q` — must be 0 errors.
3. Run `python -m mypy automation/ --ignore-missing-imports -q` — must be 0 errors.
4. Run `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS.
5. Verify V-1 evidence schema: `python -c "from automation.live_validation_writer import validate_schema; validate_schema('data/live_validation_evidence.json'); print('PASS')"`.
6. Verify TierD-2 tracker is consistent: `python -c "import json; d=json.load(open('PM_Pack/06_state/TIERD2_TRACKER.json')); print('cap:', d.get('cap_status'), 'score2:', d.get('score2_new'))"`.
7. Check the latest CI run: `gh run list --workflow=ci.yml --limit 1 --json status,conclusion` — must show `completed/success`.
8. Run the merge gate dry-run: `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077` — capture full output.
9. For any merge gate FAIL items: diagnose and fix the specific issue.
10. Verify all ADRs are present: `ls docs/architecture/ | grep ADR | wc -l` — must be ≥15.
11. Verify all runbooks are present: `ls docs/runbooks/ | wc -l` — must be ≥15.
12. Verify BRAIN_REGISTRY has 44+ entries: `python -c "import yaml; r=yaml.safe_load(open('PM_Pack/automation/BRAIN_REGISTRY.yml')); print(sum(len(v) for v in r.get('load_order',{}).values()))"`.
13. Write `docs/validation/CYCLE_077_INTEGRATION_VERIFICATION.md` with all 12 check results.
14. Commit: `git add docs/validation/ && git commit -m "docs(validation): Cycle 077 full integration verification"`.

---

## Task 3 (LARGE, ~70 min): Go-Live Stage 4 — Forced Repair Loop Test

Deliverable: `OPS-033` moved to DONE; `docs/validation/GO_LIVE_STAGE_4_EVIDENCE.md` written with PASS.

Sub-steps:
1. Create a test branch: `git checkout -b test/stage4-repair-$(date +%Y%m%d) && git push origin test/stage4-repair-$(date +%Y%m%d)`.
2. Deliberately introduce a minor simulated failure: write a file `C:\AI_Runner\state\test_repair_trigger.json` with content `{"force_repair": true, "reason": "stage4_test"}`.
3. Run the repair loop: `python automation/ai_cycle_controller.py repair --trigger C:\AI_Runner\state\test_repair_trigger.json --live 2>&1 | tee docs/validation/GO_LIVE_STAGE_4_REPAIR_LOG.txt`.
4. Verify the repair loop detected the trigger and ran the appropriate remediation steps.
5. Verify the repair loop wrote its result to `C:\AI_Runner\runs\repair_*.json`.
6. Verify no destructive actions were taken (no commits to main, no PR merges).
7. Clean up: `rm C:\AI_Runner\state\test_repair_trigger.json`.
8. Run the notification router to confirm alerts were queued: `python -c "from automation.notification_router import get_pending_notifications; print(get_pending_notifications())"`.
9. Write `docs/validation/GO_LIVE_STAGE_4_EVIDENCE.md` with: trigger used, repair actions taken, outcome, notifications queued.
10. Clean up test branch and commit evidence.

---

## Task 4 (MEDIUM, ~45 min): Go-Live Stage 5 — Auto-Merge Trial

Deliverable: `OPS-034` moved to DONE; `docs/validation/GO_LIVE_STAGE_5_EVIDENCE.md` written.

Sub-steps:
1. Check merge gate: `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077 2>&1 | tail -20`. Note the verdict.
2. If merge gate returns PASS or CONDITIONAL_GO: enable auto-merge on PR #88 (if not already merged): `gh pr merge 88 --squash --auto`.
3. If PR #88 is already merged: create a new test PR from cycle/077/integration to develop to test the auto-merge mechanism: `gh pr create --base develop --head cycle/077/integration --title "test: Stage 5 auto-merge trial" --body "Stage 5 Go-Live test"`.
4. Enable auto-merge: `gh pr merge {PR_NUMBER} --squash --auto`.
5. Wait for CI to pass (poll `gh run list --workflow=ci.yml --limit 1 --json status,conclusion` every 60 seconds).
6. Once CI passes, verify auto-merge triggered and completed: `gh pr view {PR_NUMBER} --json state,mergedAt`.
7. If auto-merge succeeded: PASS. If failed: diagnose why and fix the auto-merge configuration.
8. Write `docs/validation/GO_LIVE_STAGE_5_EVIDENCE.md` with: PR number, CI run ID, merge timestamp, verdict.
9. If Stage 5 required a test PR: clean up by checking if develop was updated correctly.
10. Commit evidence.

---

## Task 5 (MEDIUM, ~35 min): Resolve All NEEDS_EVIDENCE Items

Deliverable: All NEEDS_EVIDENCE checklist items moved to DONE with evidence files.

Sub-steps:
1. Run `grep -r "NEEDS_EVIDENCE" docs/ PM_Pack/` to identify all outstanding items.
2. For `GJCI-028` (In Review transitions): verify from Cycle 076 Agent D report that 4 stories were transitioned. Write `docs/validation/GJCI_028_EVIDENCE.md`.
3. For `SEC-007` (subscription preflight PASS): run `python -c "from automation.claude_sub_gate import verify_subscription_preflight; print(verify_subscription_preflight())"`. Write `docs/validation/SEC_007_EVIDENCE.md`.
4. For `CLAUDE-SUB-007` (Claude billing confirmed): verify from `C:\AI_Runner\state\claude_model_state.json`. Write `docs/validation/CLAUDE_SUB_007_EVIDENCE.md`.
5. For any GJCI items with missing evidence: capture the evidence now and write the corresponding evidence file.
6. Verify `ENV-028` (runner smoke PASS): `gh run list --workflow=runner-smoke.yml --limit 1 --json status,conclusion`. Write `docs/validation/ENV_028_EVIDENCE.md`.
7. Commit all evidence files: `git add docs/validation/ && git commit -m "docs(evidence): resolve all NEEDS_EVIDENCE checklist items"`.

---

## Task 6 (MEDIUM, ~25 min): Jira Transitions

Sub-steps:
1. Transition all stories covered by Tasks 2-5 to Done.
2. Stories: "Go-Live Stage 4 forced repair", "Go-Live Stage 5 auto-merge", all NEEDS_EVIDENCE items.
3. Post evidence file paths as comments on each story.
4. Write `docs/cycle_reports/CYCLE_077_AGENT_C_JIRA.md`.

---

## Task 7 (SMALL, ~15 min): Commit, Push, Cycle Report

Sub-steps:
1. Final `git status` — clean.
2. `git push origin cycle/077/integration`.
3. Write `docs/cycle_reports/CYCLE_077_AGENT_C.md`:
   - Integration verification: all 12 checks PASS/FAIL
   - Merge gate dry-run: PASS/CONDITIONAL_GO/FAIL
   - Go-Live Stage 4: PASS/FAIL
   - Go-Live Stage 5: PASS/FAIL
   - NEEDS_EVIDENCE items resolved: N
   - AGENT_COMPLETE
4. Commit and push.

---

## Validation (R-092 Tier 1)
```
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077
```

---

## END OF PROMPT

AGENT_COMPLETE is written at the end of `docs/cycle_reports/CYCLE_077_AGENT_C.md`.
Agent F may proceed after Agent C reports AGENT_COMPLETE.
