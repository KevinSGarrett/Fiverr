# CYCLE 077 — AGENT A PROMPT
# Branch: cycle/077/integration (from develop after PR #88 merge)
# Prerequisites: PR #88 merged to develop; Cursor model re-verified; ≥14 Jira stories open
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (MEDIUM): 25 min — Branch setup + preflight
- Task 2 (MEDIUM): 30 min — PM_Pack state update (Cycle 077)
- Task 3 (SMALL): 15 min — ADR-014 cross-platform REPO_ROOT
- Task 4 (SMALL): 15 min — ADR-015 CI-only unit tests
- Task 5 (MEDIUM): 25 min — Fix BUG-011 gh api 401
- Task 6 (SMALL): 10 min — Jira evidence + cycle report
Total estimated: ~2 hr 0 min

---

## Context

You are Cursor Agent A for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

Cycle 076 is complete. PR #88 (cycle/075/integration → develop) has been merged.
The CI suite is now fully green: lint PASS, type-check PASS, smoke-gates PASS, tests-coverage PASS.

Your job is to set up the Cycle 077 branch, update all PM_Pack state documents to reflect
Cycle 077, write two new ADRs documenting the cross-platform fixes made during CI remediation,
and fix the gh api 401 bug (BUG-011) that has blocked branch protection evidence capture.

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch target: cycle/077/integration (from develop)

---

## Task 1 (MEDIUM, ~25 min): Branch setup and full preflight

Deliverable: cycle/077/integration created from develop; all preflight checks PASS;
working state confirmed clean.

Sub-steps:
1. `git checkout develop && git pull origin develop`
2. Verify HEAD matches the merged PR #88 commit: `git log --oneline -3`
3. `git checkout -b cycle/077/integration`
4. Run: `python automation/ai_cycle_controller.py brain-check` — must output BRAIN CHECK PASS
5. Run: `python automation/ai_cycle_controller.py pm-pack-audit` — must output PASS
6. Run: `python -m ruff check automation/ src/ tests/` — must output 0 errors
7. Run: `python -m mypy automation/ --ignore-missing-imports` — must output 0 errors
8. Run: `python -m pytest tests/unit/ -q --tb=short --timeout=60` — all must pass
9. Record HEAD SHA, confirm develop SHA matches post-merge
10. If any check fails, fix before proceeding; do not continue with failing environment

---

## Task 2 (MEDIUM, ~30 min): Update all PM_Pack state documents for Cycle 077

Deliverable: All 9 state documents in PM_Pack/ updated to reflect Cycle 077 start state;
HYDRATION_HEADER.md updated with current scores, cycle, and blockers.

Sub-steps:
1. Read PM_Pack/07_hydration/HYDRATION_HEADER.md — note current CYCLE_CURRENT value
2. Update HYDRATION_HEADER.md:
   - Set CYCLE_CURRENT: 077
   - Set CYCLE_PREV: 076
   - Set WAVE_CURRENT: 10 (Wave 10 complete)
   - Update Score 1: 67.3% | Score 2: 47.1%
   - Update TierD-2 status: SEED x17 cap ACTIVE; V-1 not yet executed
   - Update blockers: V-1 execution (+2%), gh api 401 (BUG-011), Cursor model re-verify
3. Update PM_Pack/02_state_and_history/STATE_SNAPSHOT.md:
   - Set last_completed_cycle: 076
   - Record Cycle 076 summary: coverage 92.58%, 5935 tests, ADR-011/012/013, PR #88 merged
4. Update PM_Pack/02_state_and_history/CURRENT_STATE_CANONICAL.md:
   - Current cycle: 077; branch: cycle/077/integration; active stage: Stage 1
5. Update PM_Pack/02_state_and_history/PRODUCTION_READINESS_SCORECARD.md:
   - Score 1: 67.3%; Score 2: 47.1%; V-1 status: NOT YET EXECUTED
6. Update PM_Pack/02_state_and_history/TIERD2_TRACKER.json (if exists):
   - cycle_current: 77; v1_status: PENDING; v2_status: PENDING; score_2: 47.1
7. Update PM_Pack/05_governance/POST_CYCLE_CYCLE_REPORT_INDEX.md — add Cycle 076 entry
8. Verify pm-pack-audit still PASS after all updates
9. Stage all PM_Pack changes: `git add PM_Pack/`

---

## Task 3 (SMALL, ~15 min): Write ADR-014 — Cross-platform REPO_ROOT fix

Deliverable: `docs/architecture/ADR_014_CROSS_PLATFORM_REPO_ROOT.md` committed.

Sub-steps:
1. Create docs/architecture/ADR_014_CROSS_PLATFORM_REPO_ROOT.md
2. Content must include: Status (Accepted), Context (18 automation modules had
   hardcoded Path("C:/Fiverr/Fiverr") which failed on Linux CI), Decision
   (use Path(__file__).parent.parent instead), Consequences (all automation modules
   now work on any platform; CI lint/type-check/smoke-gates pass), Date: 2026-06-12
3. Minimum 200 words; include the list of 18 affected modules
4. Stage: `git add docs/architecture/ADR_014_CROSS_PLATFORM_REPO_ROOT.md`

---

## Task 4 (SMALL, ~15 min): Write ADR-015 — CI-only unit tests and pytest-timeout

Deliverable: `docs/architecture/ADR_015_CI_UNIT_TESTS_ONLY.md` committed.

Sub-steps:
1. Create docs/architecture/ADR_015_CI_UNIT_TESTS_ONLY.md
2. Content must include: Status (Accepted), Context (full test suite OOM-killed on 7GB
   GitHub runner; Playwright not needed for unit coverage; some tests had real subprocess
   calls and asyncio.sleep backoff), Decision (CI runs tests/unit/ only with --timeout=60;
   pytest-timeout added to dev deps; integration tests excluded from CI), Consequences
   (no OOM risk; hung tests fail fast; coverage gate still met at 92.58%), Date: 2026-06-12
3. Minimum 200 words
4. Stage: `git add docs/architecture/ADR_015_CI_UNIT_TESTS_ONLY.md`

---

## Task 5 (MEDIUM, ~25 min): Fix BUG-011 — gh api 401 on branch protection

Deliverable: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection`
returns 200 (not 401); evidence written to `docs/governance/BRANCH_PROTECTION_EVIDENCE.md`.

Sub-steps:
1. Run: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection` — confirm current 401
2. Check current token scopes: `gh auth status` — note what scopes GH_AUTOMATION_TOKEN has
3. The issue: GH_AUTOMATION_TOKEN lacks `repo` + `admin:repo_hook` scopes for branch protection
4. Try with your own token: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection`
   (using the currently authenticated gh session, which has full repo access)
5. If this succeeds (200), capture the output and write to
   `docs/governance/BRANCH_PROTECTION_EVIDENCE.md` with timestamp
6. Update `docs/governance/BRANCH_PROTECTION_EVIDENCE.md`:
   - Capture JSON output from the API call
   - Record: required_status_checks, enforce_admins, restrictions, required_pull_request_reviews
   - Note: this evidence uses Kevin's personal token (gh CLI), not GH_AUTOMATION_TOKEN
7. Stage: `git add docs/governance/BRANCH_PROTECTION_EVIDENCE.md`
8. In the Cycle 077 cycle report, note: if GH_AUTOMATION_TOKEN 401 persists,
   the automation should fall back to `gh api` for branch protection reads

---

## Task 6 (SMALL, ~10 min): Cycle report, Jira evidence, commit

Deliverable: CYCLE_077_AGENT_A.md written; Jira planning comment posted;
all changes committed with proper message.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_AGENT_A.md with:
   - Branch setup result (HEAD SHA)
   - PM_Pack state update summary (which files changed)
   - ADR-014 and ADR-015 written (word counts)
   - BUG-011 fix result (200 or explanation if still 401)
   - Branch protection evidence captured: YES/NO
   - Ruff PASS | Mypy PASS | brain-check PASS | pm-pack-audit PASS
   - End with: AGENT_COMPLETE
2. Find the Cycle 077 Jira story for "Merge cycle/075/integration PR and verify CI pass"
   — post a comment: "Agent A Cycle 077: branch cycle/077/integration created from develop
   (post-PR-#88-merge). PM_Pack state updated. ADR-014/015 written. BUG-011 fix attempted.
   Full preflight PASS. Proceeding to Agent B."
3. `git add docs/cycle_reports/CYCLE_077_AGENT_A.md`
4. `git commit -m "feat(cycle-077): PM_Pack state update, ADR-014/015, BUG-011 fix attempt"`
5. `git push origin cycle/077/integration`
6. Confirm push succeeded and report HEAD SHA

---

## Validation (R-092 Tier 1 — targeted only)

```bash
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python -m ruff check automation/ src/ tests/
python -m mypy automation/ --ignore-missing-imports
python -m pytest tests/unit/test_pm_pack_loader.py -q --tb=short --timeout=30
```

All must PASS before writing AGENT_COMPLETE.

---

## Hard gates

- If brain-check FAILS after PM_Pack update, fix the state files before committing
- If pm-pack-audit FAILS, fix the inconsistency before proceeding
- Do NOT commit broken state
- Do NOT run plan-cycle --live; this is setup only
- Do NOT modify baseline DB at `data/cycle037_live.db`

---

END OF PROMPT
