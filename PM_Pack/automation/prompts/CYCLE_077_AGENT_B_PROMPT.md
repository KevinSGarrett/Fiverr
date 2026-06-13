# CYCLE 077 AGENT B PROMPT
# Branch: cycle/077/integration (already created by Agent A)
# Prerequisite: AGENT_COMPLETE confirmed in docs/cycle_reports/CYCLE_077_AGENT_A.md
# Agent B runs SECOND (concurrently with Agent E after Agent A completes).

---

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight, read Agent A report
- Task 2 (LARGE): 90 min — Fix full-suite coverage capture + raise all modules to ≥90%
- Task 3 (LARGE): 75 min — Execute Go-Live Stage 2: assisted docs-only Agent D test
- Task 4 (MEDIUM): 45 min — Go-Live Stage 3: full cycle dry-run smoke test
- Task 5 (MEDIUM): 30 min — Fix BUG-011: gh api 401 branch protection scope
- Task 6 (MEDIUM): 25 min — Jira evidence + story transitions
- Task 7 (SMALL): 15 min — Commit, push, cycle report
Total estimated: ~5 hr

---

## Context

Agent A has completed: CI is 4/4 green, PM_Pack state updated, ADR-014/015 written, Jira Cycle 076 stories transitioned. You are responsible for: (1) raising any remaining automation/ modules below 90% coverage, (2) executing Go-Live Stage 2 (the first real Cursor agent dispatch on a test branch), and (3) executing Go-Live Stage 3 (full cycle no auto-merge).

Go-Live Stage 2 is the first real dispatch of a Cursor agent by the controller. Use a test branch and docs-only prompt to prove the pipeline works end-to-end.

---

## Task 1 (SMALL, ~15 min): Preflight

Sub-steps:
1. Read `docs/cycle_reports/CYCLE_077_AGENT_A.md` — confirm AGENT_COMPLETE is present.
2. Pull latest: `git checkout cycle/077/integration && git pull origin cycle/077/integration`.
3. Run `python automation/ai_cycle_controller.py brain-check` — must PASS.
4. Run `python -m pytest tests/unit/ --timeout=60 -q --tb=no | tail -5` — confirm 0 unexpected failures.
5. Read the current coverage report: `python -m pytest tests/unit/ --cov=automation --cov-report=term-missing --timeout=60 -q 2>&1 | grep -E "TOTAL|FAIL|%" | tail -20`.
6. Note any modules below 90% in a working notes file.

---

## Task 2 (LARGE, ~90 min): Raise All Coverage Gaps to ≥90%

Deliverable: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60` passes with 0 failures.

Sub-steps:
1. Run per-module coverage for all automation/ modules: `python -m pytest tests/unit/ --cov=automation --cov-report=term-missing --timeout=60 2>&1 | grep -E "automation/|TOTAL"`.
2. Identify all modules below 90% coverage.
3. For each module below 90%: read the module, identify untested code paths, write targeted tests in the corresponding `tests/unit/test_{module}.py`.
4. Focus on the highest-impact gaps first: any module with <80% coverage gets at least 5 new tests.
5. Run `python -m pytest tests/unit/test_{module}.py --cov=automation.{module} --cov-report=term-missing --timeout=30` after each module to verify ≥90%.
6. Specifically ensure these are ≥90%: `ai_cycle_controller`, `run_agent_lifecycle`, `validation_runner`, `claude_post_cycle_adapter`, `jira_sync`, `git_adapter`.
7. Run the full combined check: `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing --cov-fail-under=90 --timeout=60 -q | tail -20` — must pass.
8. Document per-module coverage in `docs/cycle_reports/CYCLE_077_COVERAGE_REPORT.md`.
9. Run ruff and mypy — both must PASS.
10. Commit: `git add tests/ docs/ && git commit -m "test(coverage): raise all automation/ modules to >=90% coverage"`.

---

## Task 3 (LARGE, ~75 min): Go-Live Stage 2 — Assisted Docs-Only Agent Dispatch

Deliverable: `OPS-031` moved to DONE; `docs/validation/GO_LIVE_STAGE_2_EVIDENCE.md` written with PASS.

Go-Live Stage 2 is the first real Cursor agent dispatch by the controller on a test branch with a docs-only prompt. This proves the end-to-end pipeline: plan-cycle → validate-prompts → dispatch → monitor → report.

Sub-steps:
1. Create a test branch: `git checkout -b test/stage2-docs-only-$(date +%Y%m%d) && git push origin test/stage2-docs-only-$(date +%Y%m%d)`.
2. Read `PM_Pack/automation/prompts/CURSOR_DOCS_ONLY_SMOKE_PROMPT.md` to understand the docs-only prompt content.
3. Verify the prompt passes validation: `python automation/ai_cycle_controller.py validate-prompts --cycle 077`.
4. Check the autonomy freeze gate: `python automation/ai_cycle_controller.py status-tick` — confirm `frozen=false` or unfreezing is appropriate.
5. Run the stage 2 dispatch in live mode: `python automation/ai_cycle_controller.py run-agent --cycle 077 --agent D --prompt PM_Pack/automation/prompts/CURSOR_DOCS_ONLY_SMOKE_PROMPT.md --branch test/stage2-docs-only-{date} --live`.
6. Monitor the dispatch: poll `python automation/ai_cycle_controller.py status-tick` every 30 seconds until agent completes or 20 minutes elapses.
7. Check for AGENT_COMPLETE in the output: look for the completion marker in the agent's output.
8. Verify no destructive actions were taken: check `git log --oneline test/stage2-docs-only-{date} -10`.
9. Verify the agent wrote a docs file (the expected output of a docs-only prompt).
10. Clean up: `git push origin --delete test/stage2-docs-only-{date}` after evidence is captured.
11. Write `docs/validation/GO_LIVE_STAGE_2_EVIDENCE.md` with: dispatch timestamp, agent output hash, AGENT_COMPLETE present (yes/no), files written, any errors, overall verdict (PASS/FAIL).
12. If Stage 2 FAILS due to controller bug, diagnose and fix the specific controller issue, then re-run.
13. Commit: `git add docs/validation/ && git commit -m "docs(evidence): Go-Live Stage 2 PASS — first real Cursor dispatch"`.

---

## Task 4 (MEDIUM, ~45 min): Go-Live Stage 3 — Full Cycle No Auto-Merge

Deliverable: `OPS-032` moved to DONE; `docs/validation/GO_LIVE_STAGE_3_EVIDENCE.md` written with PASS.

Sub-steps:
1. Create a stage 3 test branch from develop: `git checkout develop && git pull && git checkout -b test/stage3-full-cycle && git push origin test/stage3-full-cycle`.
2. Create a minimal Jira story for the test cycle if needed (title: "Stage 3 smoke test story", in SCRUM project).
3. Run `python automation/ai_cycle_controller.py plan-cycle --cycle 077-stage3-test --live` — generates prompts from Jira stories.
4. Run `python automation/ai_cycle_controller.py validate-prompts --cycle 077-stage3-test` — must PASS.
5. Dispatch Agent A for the test cycle: `python automation/ai_cycle_controller.py run-agent --cycle 077-stage3-test --agent A --live`.
6. Verify Agent A completes (AGENT_COMPLETE present) without auto-merging.
7. Verify the merge gate produces CONDITIONAL_GO or PASS (not FAIL).
8. Verify no merge happened to develop (auto-merge must be disabled at this stage).
9. Clean up test branches: delete `test/stage3-full-cycle` from remote.
10. Write `docs/validation/GO_LIVE_STAGE_3_EVIDENCE.md` with full results.
11. Commit evidence.

---

## Task 5 (MEDIUM, ~30 min): Fix BUG-011 — gh api 401 on Branch Protection

Deliverable: `BUG-011` resolved; `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection` returns 200.

Sub-steps:
1. Run the failing command: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection` and capture the exact error.
2. Check token scope: `gh auth status` — confirm `GH_AUTOMATION_TOKEN` has `repo` scope.
3. If token scope is insufficient (missing `administration:read`), update `C:\AI_Runner\secrets\runner.env` to note the missing scope and write a remediation note in `docs/governance/BRANCH_PROTECTION_EVIDENCE.md`.
4. If the token has correct scope but the API returns 401, check if the token is expired: `gh api /user` — if this also fails, the token needs rotation.
5. Try with the main GitHub CLI auth: `GH_TOKEN=$(grep GH_AUTOMATION_TOKEN C:/AI_Runner/secrets/runner.env | cut -d= -f2) gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection`.
6. Capture whatever protection data is available and write to `docs/governance/BRANCH_PROTECTION_EVIDENCE.md`.
7. If the 401 cannot be resolved programmatically (requires token rotation by Kevin), document clearly in `docs/governance/BUG_011_BRANCH_PROTECTION_REMEDIATION.md` with exact steps needed.
8. Mark BUG-011 as DOCUMENTED_PENDING_TOKEN_ROTATION if API access cannot be obtained.

---

## Task 6 (MEDIUM, ~25 min): Jira Evidence and Transitions

Sub-steps:
1. Load Jira credentials from runner.env.
2. Query all in-flight Cycle 077 stories: `python -c "from automation.jira_client import JiraClient; j=JiraClient(); stories=j.get_stories_in_progress(); print(stories)"`.
3. For each story covered by Tasks 2-5: post a comment with evidence summary.
4. Transition completed stories to Done (transition ID: 41).
5. Story to transition: "Raise combined coverage to ≥90%", "Go-Live Stage 2", "Go-Live Stage 3", "Fix BUG-011".
6. Write `docs/cycle_reports/CYCLE_077_AGENT_B_JIRA_TRANSITIONS.md`.

---

## Task 7 (SMALL, ~15 min): Commit, Push, Cycle Report

Sub-steps:
1. `git status` — must be clean.
2. `git push origin cycle/077/integration`.
3. Write `docs/cycle_reports/CYCLE_077_AGENT_B.md`:
   - Coverage: list all modules with final % — all ≥90%
   - Go-Live Stage 2: PASS/FAIL with evidence file path
   - Go-Live Stage 3: PASS/FAIL with evidence file path
   - BUG-011: status (RESOLVED or DOCUMENTED_PENDING)
   - Jira: N stories transitioned to Done
   - AGENT_COMPLETE
4. `git add docs/cycle_reports/CYCLE_077_AGENT_B.md && git commit -m "report(cycle-077): Agent B AGENT_COMPLETE" && git push origin cycle/077/integration`.

---

## Validation (R-092 Tier 1)
```
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python automation/ai_cycle_controller.py brain-check
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10
```

---

## END OF PROMPT

AGENT_COMPLETE is written at the end of `docs/cycle_reports/CYCLE_077_AGENT_B.md`.
Agent C may proceed after both Agent B and Agent E report AGENT_COMPLETE.
