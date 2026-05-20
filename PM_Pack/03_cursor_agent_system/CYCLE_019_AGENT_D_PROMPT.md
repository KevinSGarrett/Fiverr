# Cycle 019 — Cursor Agent D Prompt
# Agent D — Dashboard Closure, Board Reconciliation, PR, Final Evidence Freeze

## Mission

Own the final stewardship for Cycle 019: close out E09 Dashboard runtime acceptance evidence
for remaining In Review stories, reconcile the Jira board with post-audit and Cycle 019 state,
open the Cycle 019 PR from cycle/019/integration into develop, resolve all Codex review
threads in-cycle, and perform the final evidence freeze. This cycle's primary product delivery
(Scoring Engine E04) was executed by Agents A, B, and C — your job is to validate the
complete state, provide dashboard/integration closure evidence, and execute the clean release
gate into develop.

## Common Non-Negotiable Rules

Work only from C:\Fiverr\Fiverr on cycle/019/integration. Run the mandatory PowerShell
preflight. Read ALL agent handoff notes (A, B, C) before starting. Confirm all scoring tests
pass before any PR/Codex work. Do not modify scoring files from Agents A/B/C unless fixing
a Codex finding. The .cursorrules file governs all decisions. No changes to main branch.

## Mandatory PowerShell Preflight

```powershell
Get-Location
git rev-parse --show-toplevel
git branch --show-current
git status --short --branch
git worktree list
git log --oneline -15
python -m pytest -q tests/unit/test_scoring.py
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
```

Pass condition: root = C:\Fiverr\Fiverr, branch = cycle/019/integration.
All scoring tests + full suite must pass before you open any PR.

## Jira and AC/DoD Rule

Primary Jira keys: SCRUM-19 (E04 epic progress), SCRUM-24 (E09 Dashboard epic),
SCRUM-274 (Cycle 019 control), SCRUM-231, SCRUM-232, SCRUM-235, SCRUM-237, SCRUM-241,
E09 In-Review stories (SCRUM-212 through SCRUM-228). Read these before any board updates.
Transitions must be evidence-backed. Do not prematurely mark stories Done without full source DoD.

## File Scope

Primary: docs/jira/ACTIVE_STORY_DOD_LEDGER.md (Agent D steward rows), .github/pull_request_template.md
(if update needed), docs/cycle_reports/CYCLE_019_AGENT_D.md, src/reports/placeholders.py
(if AC/DoD progress table helper needs update), tests/unit/test_reports.py (if touched).
Do not touch scoring calculator files.

## Required Validation Block

```powershell
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle019.db
python run.py phase2-smoke
```

---

## Tasks

### Task 1: Read all Agent A/B/C handoff notes, run full preflight

Read docs/cycle_reports/CYCLE_019_AGENT_A.md, AGENT_B.md, AGENT_C.md in full.
Record: total scoring tests added, final SHA from Agent C, coverage %, any open risks.
Run full preflight. Confirm cycle/019/integration is ahead of develop by Agents A/B/C commits.

### Task 2: Run full validation block — confirm all scoring tests pass

Execute all 6 validation commands. Record exact output. If any failure, stop and document.
Expected: >= 840 tests, >= 90% coverage, Ruff clean, Mypy clean, config/foundation/smoke PASS.

### Task 3: Perform Jira board reconciliation — review E04, E09, E10 stories

Query Jira for status of:
- SCRUM-19 (E04): Confirm S4.1-S4.13 are all In Progress
- SCRUM-24 (E09): Confirm SCRUM-212 through SCRUM-228 statuses are accurate
- SCRUM-25 (E10): Confirm SCRUM-231, 232, 235, 237, 241 statuses
- SCRUM-274: Confirm Cycle 019 control is In Progress
Identify any stories with stale or incorrect statuses. Document findings.

### Task 4: Post final Cycle 019 runtime acceptance evidence for E09 dashboard stories

For each E09 story still In Review (SCRUM-214, 215, 219, 225, 228):
Post a Jira comment: "Cycle 019 Agent D steward verification: Dashboard runtime contracts
remain stable after scoring engine implementation. No regression detected. [Validation output].
Stories remain In Review pending full operator UX acceptance and production runtime proof.
Status recommendation: Keep In Review."

### Task 5: Post Jira comments for E10 integration stories (SCRUM-231, 232, 235, 237, 241)

For each integration story, post: "Cycle 019 Agent D: Scoring engine (E04 S4.1-S4.13)
implemented this cycle. Integration stories remain non-Done pending full pipeline execution
(collection → analysis → scoring → dashboard). Status: Keep current non-Done status.
Next cycle should plan controlled scoring pipeline run."

### Task 6: Post Jira comment on SCRUM-274 (Cycle 019 control) with complete cycle summary

Summary comment: "Cycle 019 complete. 11 scoring calculators implemented (E04 S4.1-S4.13).
Tests: [count]. Coverage: [%]. PR: [PR URL]. Branch: cycle/019/integration. Final SHA: [sha].
E09 dashboard stories remain In Review; E10 integration stories remain In Progress/In Review.
No premature Done transitions."

### Task 7: Create Cycle 019 PR from cycle/019/integration → develop

Command: gh pr create --title "feat(cycle-019): scoring engine implementation E04 S4.1-S4.13"
  --body "[PR body content below]" --base develop --head cycle/019/integration

PR body must include:
- Summary: First full scoring engine implementation (11 calculators + orchestrator)
- Jira Keys Advanced: [list all E04 story keys + SCRUM-274]
- Changed Areas: src/scoring/ (11 new files), tests/unit/test_scoring.py, docs/
- Validation evidence: ruff clean, mypy clean, [count] tests, [%] coverage, all gates pass
- AC/DoD progress table: Per-story rows for S4.1-S4.13
- Guardrails: No main branch changes, no unauthorized worktrees, no secrets staged

### Task 8: Monitor CI/Codecov state on the Cycle 019 PR

Run: gh pr checks [PR number]
Wait for: Lint, Typecheck, Tests, and Gates → SUCCESS
Wait for: codecov/project → SUCCESS
If any check fails, diagnose and fix before marking ready for merge.

### Task 9: Handle all Codex review threads on the Cycle 019 PR in-cycle

Run: gh api graphql ... pullRequest reviewThreads to list all Codex findings.
For each finding:
- Valid: fix code, add test if needed, push, reply with evidence, resolve thread
- Invalid/non-applicable: reply with evidence-backed rationale, resolve thread
- No unresolved Codex threads are acceptable at handoff.

### Task 10: Update src/reports/placeholders.py if AC/DoD progress table helper needs update

If the steward AC/DoD markdown table helper (added in Cycle 018 Agent D) needs any update
for scoring engine stories, add the update here. Run targeted tests for reports module.
Do not change behavior — only add if scoring-specific evidence format is needed.

### Task 11: Verify all 4 agent reports exist at required paths

Confirm:
- docs/cycle_reports/CYCLE_019_AGENT_A.md (created by Agent A)
- docs/cycle_reports/CYCLE_019_AGENT_B.md (created by Agent B)
- docs/cycle_reports/CYCLE_019_AGENT_C.md (created by Agent C)
- docs/cycle_reports/CYCLE_019_AGENT_D.md (created by you)
If any are missing, post a blocker note to the PR and document in your report.

### Task 12: Final artifact hygiene sweep

Run: git status --short
Confirm: No .env, *.db runtime databases (except data/), coverage.xml, *.zip, __pycache__,
.mypy_cache/, .ruff_cache/ are staged. Only scoped docs/cycle_reports/CYCLE_019_AGENT_D.md
and any reports updates should be in your commit.

### Task 13: Final SHA freeze and evidence synchronization

Run: git rev-parse origin/cycle/019/integration (after last push)
Record: final pushed SHA. Verify this SHA matches the PR head. Post final freeze comment to PR.
Verify: All agent reports reference this SHA or note it in handoff. Sync ledger.

### Task 14: Post final PR freeze comment with evidence

Comment on the Cycle 019 PR: "Final freeze evidence. SHA: [final sha]. Tests: [count].
Coverage: [%]. Ruff: clean. Mypy: clean. Config/Foundation/Smoke: PASS. No unresolved Codex
threads. No unauthorized worktrees. No main changes. All 4 agent reports present. Ready to merge."

### Task 15: Board audit cleanup — verify no stale governance tickets

Check: SCRUM-262 (Cycle 018 control) — should it be marked Done now that PR #15 is merged?
Check: SCRUM-264 and SCRUM-273 — confirmed Done by audit. Add final confirmation comment if needed.
Check: SCRUM-18 (E03 epic) — confirm Done status was applied by audit session.
Document any stale tickets found and recommended transitions.

### Task 16: Update SCRUM-19 (E04 epic) with Cycle 019 completion summary

Post comment: "Cycle 019: All 13 scoring stories (S4.1-S4.13) In Progress.
Implementations complete. LLM inputs stubbed. Orchestrator updated.
[Test count] new scoring tests. Cycle 020 should focus on: LLM integration wiring
for scoring, controlled scoring pipeline run, and E05 Recommendations stub expansion."

### Task 17: Run full validation block one final time on final pushed SHA

After all commits and pushes, run all 6 commands again. Confirm output matches pre-PR run.
Record in report: final test count, coverage, SHA, and all PASS statuses.

### Task 18: Confirm merge readiness recommendation

Based on:
- All required CI checks: green
- Codex threads: all resolved
- No main changes: confirmed
- No unauthorized worktrees: confirmed
- No secrets staged: confirmed
- All 4 agent reports present: confirmed
State explicitly: "PR [number] is ready to merge when approved."

### Task 19: Create final Agent D report at docs/cycle_reports/CYCLE_019_AGENT_D.md

Required sections: Preflight output, full validation summary (count, coverage, all commands),
Jira reconciliation findings, PR number and URL, CI/Codex status, Jira comments posted,
AC/DoD table for touched stories, artifact hygiene, no-main confirmation, merge recommendation.

### Task 20: Confirm no premature Done transitions

Audit: Verify no product stories were moved to Done by any agent without full source AC/DoD.
Check: SCRUM-214, 215, 219, 225, 228 (E09) — should all still be In Review (not Done).
Check: SCRUM-231, 232 (E10) — should still be In Progress (not Done).
Check: E04 stories S4.1-S4.13 — all In Progress (implementation done but pipeline not wired).
Document any premature Done transitions found and recommend corrective action.

## Final Report

Create: docs/cycle_reports/CYCLE_019_AGENT_D.md

Required content: Preflight + full validation output; PR number, URL, head SHA; CI check results;
Codex finding count + resolution status; Jira reconciliation summary; AC/DoD table (all touched keys);
merge readiness recommendation; no-main confirmation; no-unapproved-worktree confirmation.

## Completion Standard

You are complete when: PR is open with all CI checks green; Codex threads are resolved; final
SHA is synchronized across report, ledger, PR, and Jira comments; all 4 agent reports are present;
no secrets are staged; Agent D report exists at the required path.
