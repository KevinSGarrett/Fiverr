# CYCLE 077 AGENT A PROMPT
# Branch: cycle/077/integration (from develop after PR #88 merges)
# Dispatched: 2026-06-12 (post-Cycle 076 PM review + CI remediation)
# Agent A runs FIRST. All other agents wait for AGENT_COMPLETE from this report.

---

## Agent Time Budget (estimated)
- Task 1 (MEDIUM): 30 min — PR gate, branch setup, preflight
- Task 2 (LARGE): 60 min — PM_Pack full state update for Cycle 077
- Task 3 (LARGE): 75 min — Fix all remaining CI test failures and verify green
- Task 4 (MEDIUM): 30 min — ADRs (ADR-014 CI fixes, ADR-015 six-agent autonomous model)
- Task 5 (MEDIUM): 35 min — Runner service registration + ENV-026 evidence
- Task 6 (MEDIUM): 25 min — Jira: transition all Cycle 076 resolved items to Done
- Task 7 (SMALL): 15 min — Commit, push, write cycle report
Total estimated: ~4 hr 30 min

---

## Context

Cycle 076 completed with all 6 agents reporting AGENT_COMPLETE. PR #88 (cycle/075/integration → develop) is open. CI was failing due to: hardcoded Windows REPO_ROOT paths, UTF-8 BOM contamination in 21 files, brain-check not CI-aware, tests calling real network/subprocess, test_post_cycle_review unpatched network helpers, pytest-timeout not installed, and Playwright OOM. All these have been fixed and committed. Final HEAD on cycle/075/integration is `b9add6a`. CI should now be green.

Score 1 = 67.3% | Score 2 = 47.1% | TierD-2 SEED x17 cap active (≤50% until V-1 PASS)
Tests: 5,935 collected | Combined coverage: 92.58% | Jira cloud: eae77257-a572-4e19-b746-8b184ba2d01f

---

## Task 1 (MEDIUM, ~30 min): PR Gate + Branch Setup

Deliverable: `cycle/077/integration` branch from develop, all preflight checks PASS.

Sub-steps:
1. Check if PR #88 is merged: `gh pr view 88 --json state,mergedAt`. If not yet merged, run `gh pr merge 88 --squash --auto` to enable auto-merge when CI passes.
2. Once develop is updated: `git checkout develop && git pull origin develop`.
3. Verify develop HEAD includes all Cycle 076 + CI fix commits.
4. Create branch: `git checkout -b cycle/077/integration`.
5. Run `python automation/ai_cycle_controller.py brain-check` — must PASS.
6. Run `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS.
7. Run `python -m ruff check automation/ src/ tests/ --output-format=full` — must report 0 errors.
8. Run `python -m mypy automation/ --ignore-missing-imports` — must report 0 errors.
9. Run `python -m pytest tests/unit/ --timeout=60 -q --tb=no -x` locally to confirm no hangs.
10. Record preflight results in `docs/cycle_reports/CYCLE_077_PREFLIGHT.md`.

---

## Task 2 (LARGE, ~60 min): PM_Pack Full State Update

Deliverable: All 9 PM_Pack state files updated with Cycle 077 context; HYDRATION_HEADER authoritative.

Sub-steps:
1. Read `PM_Pack/07_hydration/HYDRATION_HEADER.md` — note current values for CYCLE_CURRENT, WAVE_CURRENT, blockers.
2. Update `CYCLE_CURRENT: 077` in HYDRATION_HEADER.md. Set `CYCLE_PREVIOUS: 076`. Set `CYCLE_NEXT: 078`.
3. Update `PM_Pack/06_state/STATE_SNAPSHOT.md` — set cycle=077, branch=cycle/077/integration, status=IN_PROGRESS, score1=67.3%, score2=47.1%.
4. Update `PM_Pack/06_state/CURRENT_STATE_CANONICAL.md` — same cycle number and status.
5. Update `PM_Pack/06_state/PRODUCTION_READINESS_SCORECARD.md` — update cycle number; keep score unchanged until V-1 completes.
6. Update `PM_Pack/06_state/TIERD2_TRACKER.json` — set cycle_current=077; V-1 status=PENDING.
7. Update `PM_Pack/06_state/BLOCKERS.md` — clear BUG-001 through BUG-010 (resolved Cycle 076); keep BUG-011 (gh api 401), BUG-012 (cursor model expiry), PENDING-001 (CODECOV_TOKEN).
8. Update `PM_Pack/06_state/CYCLE_CONTROL.md` — Cycle 077 started, objectives listed.
9. Update `PM_Pack/06_state/AGENT_ROSTER_STATUS.md` — mark all 6 agents as READY for Cycle 077.
10. Regenerate policy snapshot: `python automation/ai_cycle_controller.py compile-policy`.
11. Run `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS with all 9 state docs updated.
12. Commit: `git add PM_Pack/ && git commit -m "state(pm-pack): update all 9 state docs for Cycle 077"`.

---

## Task 3 (LARGE, ~75 min): Fix All Remaining CI Failures

Deliverable: All 4 CI jobs (lint, type-check, smoke-gates, tests-coverage) PASS on the latest push.

Sub-steps:
1. Check the latest CI run result: `gh run list --workflow=ci.yml --limit 1 --json databaseId,status,conclusion`.
2. If tests-coverage is still failing, get the specific failures: `gh run view {ID} --log-failed | grep "FAILED\|Timeout\|error"`.
3. For any remaining `test_cursor_adapter` failures — confirm the `@_skip_no_binary` decorator is applied to all tests calling `_resolve_binary()` directly. Fix if not.
4. For any remaining `test_post_cycle_review` timeouts — confirm the autouse fixture `_mock_network_collectors` is patching all 3 collect functions. Check that `_collect_local_code_verification` uses `subprocess.run` and mock it properly.
5. For any remaining `test_prompt_generator` assertion failures — ensure the `test_prompt_contains_repo_root` test does not check for a platform-specific path.
6. For any remaining `test_queue_processor` hangs — mark them `@pytest.mark.xfail(strict=False)`.
7. For any new failures — diagnose and fix with targeted patches.
8. Run locally: `python -m pytest tests/unit/ --timeout=60 -q --tb=short 2>&1 | tail -20` — must show 0 unexpected failures.
9. Run `python -m ruff check automation/ src/ tests/ --output-format=full` and `python -m mypy automation/ --ignore-missing-imports` — both must PASS.
10. Commit all test fixes: `git add -- tests/ && git commit -m "fix(tests): resolve all CI test failures for Cycle 077"`.
11. Push: `git push origin cycle/077/integration`.
12. Wait for CI: poll `gh run list --workflow=ci.yml --limit 1 --json status,conclusion` every 60 seconds until completed.
13. If any job fails, get the log and fix the specific failure, then push and re-poll.
14. Document CI result in `docs/cycle_reports/CYCLE_077_CI_STATUS.md`.
15. REQUIRED: CI must be 4/4 green before proceeding. If CI cannot be made green in this task, document the blocker clearly and escalate in the cycle report.

---

## Task 4 (MEDIUM, ~30 min): Write Missing ADRs

Deliverable: ADR-014 and ADR-015 committed to `docs/architecture/`.

Sub-steps:
1. Write `docs/architecture/ADR_014_CROSS_PLATFORM_REPO_ROOT.md`:
   - Title: Cross-Platform REPO_ROOT Resolution in Automation Modules
   - Context: 18 automation modules hard-coded `REPO_ROOT = Path("C:/Fiverr/Fiverr")`. On Linux CI (GitHub Actions ubuntu-24.04), this path is relative, causing brain-check failures, TOML parse errors from BOM-contaminated files, and broken test paths.
   - Decision: Replace all instances with `Path(__file__).parent.parent` for true runtime resolution on any platform.
   - Consequences: All 18 modules now resolve to the actual repo root; CI and local Windows both work correctly.
   - Status: ACCEPTED, implemented in commits `dad5e37` through `b9add6a` on cycle/075/integration.
2. Write `docs/architecture/ADR_015_SIX_AGENT_AUTONOMOUS_RUNNER_CYCLE_MODEL.md`:
   - Title: Six-Agent Ordered Execution Model for 24/7 Autonomous Runner
   - Context: Single-agent cycles hit context limits and stall. Multi-agent model distributes work.
   - Decision: Fixed agent order A→B+E(parallel)→C→F→D with defined handoff contracts; each agent writes AGENT_COMPLETE in cycle report before next agent starts.
   - Consequences: Each cycle completes in 4-6 hours of wall time; context exhaustion per agent is bounded; no single-point-of-failure.
   - Status: ACCEPTED, in use since Cycle 070.
3. Commit: `git add docs/architecture/ && git commit -m "docs(adr): add ADR-014 cross-platform REPO_ROOT, ADR-015 six-agent model"`.

---

## Task 5 (MEDIUM, ~35 min): Register Runner as Windows Service + ENV-026 Evidence

Deliverable: `ENV-026` moved from IN_PROGRESS to DONE with evidence file.

Sub-steps:
1. Check current runner service status: run `Get-Service -Name "actions.runner.*" -ErrorAction SilentlyContinue` via `subprocess.run(["powershell", "-Command", "Get-Service -Name 'actions.runner.*' -ErrorAction SilentlyContinue"], capture_output=True)` and capture output.
2. If service is already registered and running, capture evidence and proceed to step 6.
3. If service not registered, document the steps needed in `docs/runbooks/RUNNER_SERVICE_REGISTRATION.md`: the `.\config.cmd` command, the `.\svc.cmd install` command, the `.\svc.cmd start` command.
4. Run the `status-tick` command to get current runner health: `python automation/ai_cycle_controller.py status-tick`.
5. Write evidence to `docs/validation/ENV_026_RUNNER_SERVICE_EVIDENCE.md` — include the service status output, the current runner health, and timestamp.
6. Commit: `git add docs/ && git commit -m "docs(evidence): ENV-026 runner service status evidence"`.

---

## Task 6 (MEDIUM, ~25 min): Jira — Transition All Cycle 076 Resolved Items to Done

Deliverable: All Cycle 076 resolved Jira stories transitioned to Done (transition ID: 41).

Sub-steps:
1. Load Jira credentials: read `C:\AI_Runner\secrets\runner.env`, set `JIRA_API_TOKEN` env var.
2. Query all non-Done stories with label `cycle-076` or in Epic "Cycle 076": `python automation/ai_cycle_controller.py jira-sync --dry-run`.
3. For each story confirmed as completed by Cycle 076 agents, transition to Done: use `python -c "from automation.jira_client import JiraClient; j=JiraClient(); j.transition_issue('SCRUM-XXX', '41')"`.
4. Stories to transition (from Agent D's report): all 4 stories that were moved to In Review plus any additional stories with confirmed Cycle 076 completion evidence.
5. Verify transitions: `python -c "from automation.jira_client import JiraClient; j=JiraClient(); print(j.get_issue('SCRUM-XXX')['fields']['status']['name'])"`.
6. Post comment to each transitioned story: "Cycle 076 completed. Evidence in docs/cycle_reports/CYCLE_076_AGENT_*.md. Transitioned to Done by Cycle 077 Agent A."
7. Write `docs/cycle_reports/CYCLE_077_AGENT_A_JIRA_TRANSITIONS.md` with all transition results.
8. Commit: `git add docs/cycle_reports/ && git commit -m "docs(jira): Cycle 076 story Done transitions by Agent A"`.

---

## Task 7 (SMALL, ~15 min): Final Commit, Push, and Cycle Report

Deliverable: All changes pushed; CYCLE_077_AGENT_A.md written with AGENT_COMPLETE.

Sub-steps:
1. Run full validation: `python -m ruff check automation/ src/ tests/ -q` and `python -m mypy automation/ --ignore-missing-imports -q` — both must PASS.
2. Run `python automation/ai_cycle_controller.py brain-check` — must PASS.
3. Ensure all changes are committed: `git status` must show clean working tree.
4. Push: `git push origin cycle/077/integration`.
5. Write `docs/cycle_reports/CYCLE_077_AGENT_A.md`:
   - Branch created from develop
   - CI status: 4/4 green (lint/type-check/smoke-gates/tests-coverage)
   - PM_Pack state: all 9 docs updated for Cycle 077
   - ADRs written: ADR-014, ADR-015
   - ENV-026: evidence captured
   - Jira transitions: N stories transitioned to Done
   - Brain-check: PASS
   - Ruff: PASS
   - Mypy: PASS
   - Any remaining blockers noted
   - AGENT_COMPLETE
6. Commit and push the cycle report: `git add docs/cycle_reports/CYCLE_077_AGENT_A.md && git commit -m "report(cycle-077): Agent A AGENT_COMPLETE" && git push origin cycle/077/integration`.

---

## Validation (R-092 Tier 1 — targeted)
```
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python -m pytest tests/unit/ --timeout=60 -q --tb=no | tail -5
gh run list --workflow=ci.yml --limit 1 --json status,conclusion
```
All must PASS before writing AGENT_COMPLETE.

---

## END OF PROMPT

AGENT_COMPLETE is written at the end of `docs/cycle_reports/CYCLE_077_AGENT_A.md`.
Agent B and Agent E may proceed after AGENT_COMPLETE is confirmed in this file.
