# CYCLE 077 AGENT D PROMPT
# Branch: cycle/077/integration
# Prerequisite: AGENT_COMPLETE confirmed in docs/cycle_reports/CYCLE_077_AGENT_F.md
# Agent D runs LAST — final close-out, merge, full Jira sync, Cycle 078 planning.

---

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight, read all 5 agent reports
- Task 2 (LARGE): 75 min — Merge gate full run + PR merge execution
- Task 3 (LARGE): 70 min — Full Jira Done sync for all Cycle 077 completed items
- Task 4 (MEDIUM): 50 min — Post-cycle GitHub + Jira bundles + official review
- Task 5 (MEDIUM): 45 min — Complete PRODUCTION_READINESS_SCORECARD + final state update
- Task 6 (MEDIUM): 35 min — Write Cycle 078 story recommendations + planning artifacts
- Task 7 (SMALL): 15 min — Final commit, push, cycle report
Total estimated: ~5 hr

---

## Context

All 5 prior agents have completed. You are the cycle close-out agent. This cycle has completed:
- CI fully green (4/4 jobs PASS)
- PR #88 ready for merge (or already merged to develop)
- Coverage ≥90% combined
- V-1/V-2/V-3 PASS — TierD-2 cap removed
- Go-Live Stages 2-6 PASS
- Go-Live Stage 7 scaffolding READY
- All NEEDS_EVIDENCE items resolved
- All ADRs complete (ADR-001 through ADR-015)

Your job: merge the PR, complete all Jira transitions, write the official post-cycle bundle, update the production readiness scorecard, and write comprehensive Cycle 078 planning.

---

## Task 1 (SMALL, ~15 min): Preflight

Sub-steps:
1. Confirm AGENT_COMPLETE in ALL of: CYCLE_077_AGENT_A.md, _B.md, _E.md, _C.md, _F.md.
2. `git checkout cycle/077/integration && git pull origin cycle/077/integration`.
3. `python automation/ai_cycle_controller.py brain-check` — must PASS.
4. Run the merge gate dry-run: `python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077 2>&1 | tail -20`. Note the verdict.
5. Check if PR #88 is already merged: `gh pr view 88 --json state,mergedAt`.
6. Check CI status: `gh run list --workflow=ci.yml --limit 1 --json status,conclusion` — must show success.
7. Confirm Score 2 and TierD-2 cap status from Agent E report.

---

## Task 2 (LARGE, ~75 min): Merge Gate Full Run + PR Merge

Deliverable: cycle/077/integration merged to develop; PR closed; CI on develop green.

Sub-steps:
1. Run the full merge gate (not dry-run): `python automation/ai_cycle_controller.py merge-gate --cycle 077 2>&1 | tee docs/cycle_reports/CYCLE_077_MERGE_GATE_RESULT.txt`. Note: this checks all evidence (CI, coverage, Codecov, model, Jira).
2. If merge gate returns PASS: proceed to step 5.
3. If merge gate returns CONDITIONAL_GO: document each unmet condition. Items that require Kevin (CODECOV_TOKEN, Cursor model expiry) should be noted but should NOT block the merge — these are P1 items, not P0.
4. If merge gate returns FAIL due to coverage < 90% or CI not passing: stop and fix before proceeding.
5. If PR #88 is not yet merged: `gh pr merge 88 --squash --delete-branch`.
6. If PR #88 is already merged: verify develop is up to date: `git checkout develop && git pull origin develop && git log --oneline -5`.
7. Wait for CI on develop: poll `gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion` every 60 seconds.
8. If CI on develop fails: diagnose the failure, fix on develop directly (hotfix commit), push, and re-poll.
9. Once CI on develop is green: write `docs/cycle_reports/CYCLE_077_PR_MERGE_EVIDENCE.md` with: PR number, merge SHA, CI run ID on develop, timestamp.
10. Create PR for cycle/077/integration → develop (if cycle/077 is separate from 075): `gh pr create --base develop --head cycle/077/integration --title "feat(cycle-077): V-1/V-2/V-3 PASS, Go-Live Stages 2-6, TierD-2 cap removed" --body "See docs/cycle_reports/CYCLE_077_*.md for full evidence."`.
11. Merge the Cycle 077 PR: `gh pr merge {PR_NUMBER} --squash --delete-branch`.
12. Verify: `git checkout develop && git pull && git log --oneline -3`.

---

## Task 3 (LARGE, ~70 min): Full Jira Done Sync

Deliverable: ALL in-scope Jira stories for Cycle 076/077 transitioned to Done (transition ID: 41).

Sub-steps:
1. Query all non-Done stories in the SCRUM project: `python -c "from automation.jira_client import JiraClient; j=JiraClient(); stories=j.search_issues('project=SCRUM AND status!=Done AND sprint in openSprints()'); [print(s['key'], s['fields']['status']['name'], s['fields']['summary'][:60]) for s in stories['issues']]"`.
2. For each story that has been completed by Cycle 076 or 077 agents: transition to Done.
3. Specifically: all stories related to CI fixes, coverage improvements, V-1/V-2/V-3, Go-Live Stages 2-6, ADRs, ENV items, BUG-001 through BUG-010.
4. For stories still legitimately in progress (BUG-011 pending token rotation, BUG-012 Cursor model expiry, PENDING-001 CODECOV_TOKEN): leave in current status and post a blocking comment noting what's required.
5. For OPS-036 (24-hour observation): transition to IN_PROGRESS (Stage 7 scaffold complete, waiting for live observation).
6. For OPS-037 (7-day autonomy): leave as BLOCKED — requires 24-hour observation first.
7. Post evidence comment on each transitioned story: include the relevant evidence file path and cycle number.
8. Write `docs/cycle_reports/CYCLE_077_JIRA_FULL_SYNC.md` with: total stories transitioned to Done, remaining open stories and reasons.
9. Commit.

---

## Task 4 (MEDIUM, ~50 min): Post-Cycle Bundles + Official Review

Deliverable: GitHub bundle, Jira bundle, and official post-cycle review written; dispatch decision JSON updated.

Sub-steps:
1. Generate the post-cycle GitHub bundle: `python -c "from automation.post_cycle_review import generate_post_cycle_github_bundle; from automation.github_client import GitHubClient; c=GitHubClient(); bundle=generate_post_cycle_github_bundle(77, 'develop', c); import json; print(json.dumps(bundle, indent=2))" > docs/cycle_reports/CYCLE_077_GITHUB_BUNDLE.json`.
2. Generate the post-cycle Jira bundle: `python -c "from automation.post_cycle_review import generate_post_cycle_jira_bundle; from automation.jira_client import JiraClient; j=JiraClient(); bundle=generate_post_cycle_jira_bundle(77, j); import json; print(json.dumps(bundle, indent=2))" > docs/cycle_reports/CYCLE_077_JIRA_BUNDLE.json`.
3. Run the official post-cycle review in POST_MERGE mode: `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge 2>&1 | tee docs/cycle_reports/CYCLE_077_POST_CYCLE_REVIEW_RESULT.txt`.
4. Verify `C:\AI_Runner\state\next_cycle_dispatch_decision.json` exists and shows `blocks_dispatch: false`.
5. If `blocks_dispatch: true`: read the reason and resolve the blocking issue.
6. Write `docs/cycle_reports/CYCLE_077_POST_CYCLE_CLOSE.md` with: review status, blocks_dispatch value, next_action, GitHub bundle summary, Jira bundle summary.
7. Commit.

---

## Task 5 (MEDIUM, ~45 min): Production Readiness Scorecard + Final State Update

Deliverable: Scorecard updated with all Cycle 077 completions; final Score 1 and Score 2 calculated.

Sub-steps:
1. Read `PM_Pack/06_state/PRODUCTION_READINESS_SCORECARD.md` current state.
2. Calculate final Score 1 (internal readiness): count all DONE items in the checklist as a fraction of total trackable items. Estimate: with Stages 2-6 PASS and all prior items DONE, Score 1 ≈ 78-82%.
3. Calculate final Score 2 (E2E validation): V-1+V-2+V-3 PASS = +6%, so Score 2 = 47.1% + 6% = 53.1%. TierD-2 cap REMOVED.
4. Update `PM_Pack/06_state/PRODUCTION_READINESS_SCORECARD.md`:
   - Score 1: new value
   - Score 2: 53.1% (or actual calculated value)
   - TierD-2 cap: REMOVED (cycle 077)
   - Go-Live stages: 2/PASS, 3/PASS, 4/PASS, 5/PASS, 6/PASS, 7/SCAFFOLD_READY, 8/NOT_STARTED
   - Remaining P0 blockers: 0
   - Remaining P1 items: BUG-011 (branch protection 401), BUG-012 (Cursor model expiry - Kevin), PENDING-001 (CODECOV_TOKEN - Kevin)
5. Update `PM_Pack/07_hydration/HYDRATION_HEADER.md` — set `CYCLE_CURRENT: 078`, `CYCLE_PREVIOUS: 077`, clear resolved blockers.
6. Update `PM_Pack/06_state/STATE_SNAPSHOT.md` — Cycle 077 COMPLETE, Cycle 078 READY_FOR_DISPATCH.
7. Run pm-pack-audit: `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS.
8. Commit: `git add PM_Pack/ && git commit -m "state(pm-pack): final Cycle 077 state, Score2=53.1%, TierD-2 cap REMOVED"`.

---

## Task 6 (MEDIUM, ~35 min): Cycle 078 Story Recommendations + Planning

Deliverable: `docs/cycle_reports/CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md` with ≥10 stories; `docs/cycle_reports/CYCLE_077_CYCLE_078_PLANNING.md`.

Sub-steps:
1. Read `docs/cycle_reports/CYCLE_077_AGENT_F.md` — note the Stage 7 scaffold status and any remaining items.
2. Write `docs/cycle_reports/CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md` with 12 stories:
   - "Execute Go-Live Stage 7: 24-hour unattended observation run" (XL) — runs `start_24h_observation.ps1`, monitors for 24 hours
   - "Execute Go-Live Stage 8: 7-day autonomy trial" (XL) — blocked until Stage 7 PASS
   - "Execute V-4 through V-9 validation gates" (XXL) — each V-stage earns +2% Score 2
   - "Implement daily/weekly automated reporting" (L) — daily Slack digest, weekly PDF report
   - "Wire Codecov integration after token obtained" (M) — requires PENDING-001 resolved by Kevin
   - "Fix gh api 401 branch protection via token rotation" (M) — requires BUG-011 token scope fix
   - "Implement real Cursor model auto-verification" (L) — automate VERIFIED status check
   - "Wire EC2 failover as warm standby" (XL) — ARCH-007 followup
   - "Implement 14-day rolling backtesting engine" (XXL) — from late-May architecture design
   - "Add Upwork + Exploding Topics signal integrations" (XXL) — from roadmap
   - "Complete Go-Live Stage 7 debrief and stabilization" (L) — post-observation fixes
   - "Prepare for 24/7 fully unattended operation sign-off" (L) — final P2 checklist items
3. Write `docs/cycle_reports/CYCLE_077_KEVIN_HANDOFF.md`:
   - Cycle 077 summary: all completions
   - Score 1: {new}% | Score 2: 53.1% | TierD-2 cap: REMOVED
   - Go-Live stages 2-6: all PASS
   - Go-Live stage 7: SCAFFOLD_READY — Kevin can start the 24-hour observation at any time
   - Cursor model: must be re-verified before Cycle 078 dispatch
   - CODECOV_TOKEN: must be obtained from codecov.io before GJCI-006/007/008
   - Next step: create Cycle 078 Jira stories and run `plan-cycle --cycle 078 --live`
4. Commit both files.

---

## Task 7 (SMALL, ~15 min): Final Commit, Push, Cycle Report

Sub-steps:
1. Run comprehensive final validation:
   - `python -m ruff check automation/ src/ tests/ -q` — 0 errors
   - `python -m mypy automation/ --ignore-missing-imports -q` — 0 errors
   - `python automation/ai_cycle_controller.py brain-check` — PASS
   - `python automation/ai_cycle_controller.py pm-pack-audit` — PASS
   - `gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion` — success
2. `git status` — clean.
3. `git push origin cycle/077/integration` (final push before this branch is fully merged).
4. Write `docs/cycle_reports/CYCLE_077_AGENT_D.md`:
   - Merge gate verdict
   - PR merge status and develop CI result
   - Jira: N stories transitioned to Done, M remaining with reasons
   - Post-cycle review: status, blocks_dispatch
   - Score 1: {new}% | Score 2: 53.1% | TierD-2 cap: REMOVED
   - Go-Live stages 2-6: all PASS summary
   - Go-Live stage 7: SCAFFOLD_READY
   - Cycle 078 stories: 12 recommended
   - AGENT_COMPLETE
5. `git add docs/cycle_reports/CYCLE_077_AGENT_D.md && git commit -m "report(cycle-077): Agent D AGENT_COMPLETE — Cycle 077 COMPLETE" && git push origin cycle/077/integration`.

---

## Validation (R-092 Tier 2 — Comprehensive)
```
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077
python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge | tail -5
gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion
```

---

## END OF PROMPT

AGENT_COMPLETE is written at the end of `docs/cycle_reports/CYCLE_077_AGENT_D.md`.
Cycle 077 is complete upon Agent D AGENT_COMPLETE.
Cycle 078 begins after: Cursor model re-verified, ≥12 Cycle 078 stories created in Jira, plan-cycle --cycle 078 --live.
