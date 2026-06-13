# CYCLE 077 — AGENT D PROMPT
# Dispatched after: ALL other agents (A, B, E, C, F) AGENT_COMPLETE
# Branch: cycle/077/integration
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight + read all 5 handoffs
- Task 2 (MEDIUM): 35 min — Create PR #89 + merge gate dry-run
- Task 3 (MEDIUM): 30 min — Jira Done transitions + V-1 evidence comments
- Task 4 (MEDIUM): 25 min — Post V-1 evidence to TierD-2 Jira epic
- Task 5 (SMALL): 15 min — Cycle 078 Jira story recommendations
- Task 6 (SMALL): 10 min — Kevin handoff doc + final commit
Total estimated: ~2 hr 10 min

---

## Context

You are Cursor Agent D for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

All other agents are complete. Your job:
1. Create PR #89 (cycle/077/integration → develop)
2. Run merge gate dry-run
3. Transition completed Jira stories to Done
4. Post V-1 evidence to the TierD-2 Jira epic
5. Recommend Cycle 078 Jira stories
6. Write Kevin handoff document

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch: cycle/077/integration
Done transition ID: 41

---

## Task 1 (SMALL, ~15 min): Preflight + read all 5 handoffs

Sub-steps:
1. `git checkout cycle/077/integration && git pull origin cycle/077/integration`
2. `git log --oneline -15` — confirm all 5 agent commits present
3. Read all 5 cycle reports:
   - docs/cycle_reports/CYCLE_077_AGENT_A.md
   - docs/cycle_reports/CYCLE_077_AGENT_B.md
   - docs/cycle_reports/CYCLE_077_AGENT_E.md
   - docs/cycle_reports/CYCLE_077_AGENT_C.md
   - docs/cycle_reports/CYCLE_077_AGENT_F.md
4. Note: V-1 status (PASS/FAIL), coverage TOTAL, any unresolved flags
5. Run: `python automation/ai_cycle_controller.py brain-check` — must PASS
6. Run: `python -m ruff check automation/ src/ tests/` — 0 errors
7. Run: `python -m mypy automation/ --ignore-missing-imports` — 0 errors

---

## Task 2 (MEDIUM, ~35 min): Create PR #89 + merge gate dry-run

Deliverable: PR #89 (cycle/077/integration → develop) created; merge gate dry-run
result documented; SEC-007 and CLAUDE-SUB-007 checks PASS.

Sub-steps:
1. Check if PR already exists: `gh pr list --head cycle/077/integration`
   - If exists: use that PR number; add a comment with cycle summary
   - If not: create it now
2. Create PR (if needed):
   ```
   gh pr create \
     --base develop \
     --head cycle/077/integration \
     --title "feat(cycle-077): V-1 live collection, coverage stabilization, ADR-014/015" \
     --body "Cycle 077 complete. V-1 status: [PASS/FAIL]. Coverage: N%. 
             ADR-014 (cross-platform REPO_ROOT), ADR-015 (CI unit tests).
             All 6 agents completed with AGENT_COMPLETE."
   ```
   Note: title must be ≤72 chars; no special characters in scope field
3. Record PR number and URL
4. Run merge gate dry-run:
   `python automation/ai_cycle_controller.py merge-gate --cycle 077 --dry-run`
   - Record: PASS, PARTIAL, or FAIL; list any blocking items
5. Run SEC-007 check:
   `python automation/ai_cycle_controller.py secret-guard`
   - Must show: no secrets detected
6. Run CLAUDE-SUB-007 check:
   `python automation/ai_cycle_controller.py check-claude-sub`
   - Must show: subscription billing confirmed; API key absent
7. Document all results; if merge gate shows PARTIAL (e.g., CI not yet run), note what's pending

---

## Task 3 (MEDIUM, ~30 min): Jira Done transitions + story comments

Deliverable: All in-scope Cycle 077 Jira stories transitioned to Done or In Review;
evidence comments posted on each story.

Sub-steps:
1. List all Cycle 077 Jira stories (search by label "cycle-077" or sprint):
   Use jira_client to query: `project = SCRUM AND sprint in openSprints() AND label = "cycle-077"`
2. For each story, determine its completion state based on cycle reports:
   a. "Execute V-1 live collection" — Done if V-1 PASS; In Progress if V-1 FAIL
   b. "Merge cycle/075/integration PR" — Done (PR #88 was merged before Cycle 077)
   c. "Add Jira Done transitions for Cycle 076 stories" — Done (handled now)
   d. "Raise combined coverage to >=90%" — Done if Agent C confirmed ≥90%
   e. "Update TierD-2 tracker" — Done if V-1 PASS; In Review if V-1 FAIL
   f. "Stabilize full-suite coverage" — Done if Agent B confirmed stable
   g. "Add branch protection evidence" — Done if Agent A fixed BUG-011
3. For each story being transitioned to Done:
   - Post evidence comment FIRST (summary of what was done + file paths)
   - Then transition to Done: `jira_client.transition_issue(story_key, transition_id=41)`
4. For stories staying In Progress or In Review: post status comment explaining why
5. Count total: N stories → Done; M stories → In Review

---

## Task 4 (MEDIUM, ~25 min): Post V-1 evidence to TierD-2 Jira epic

Deliverable: TierD-2 validation epic updated with V-1 result; if V-1 PASS, full
Score 2 update posted; V-2 unlocked if applicable.

Sub-steps:
1. Find the TierD-2 Jira epic (search: "TierD-2 Validation" or "SEED x17")
2. Post a detailed comment to the epic:
   ```
   Cycle 077 V-1 Result: [PASS/FAIL]
   
   Keyword: python
   Gig results collected: N
   Evidence: data/live_validation_evidence.json (v1_status=[PASS/FAIL])
   Tracker: docs/cycle_reports/CYCLE_077_TIERD2_TRACKER.json
   
   Score impact:
     Score 2 before: 47.1%
     Score 2 after: [49.1% (+2.0%) if PASS | 47.1% (unchanged) if FAIL]
     TierD-2 x17 cap: [LIFTED if PASS | STILL ACTIVE if FAIL]
   
   Next: V-2 is [UNLOCKED | BLOCKED] — execute in Cycle 078 if PASS
   ```
3. If V-1 PASS: also find the "Execute V-2 live parsing validation on V-1 payload" Jira story
   and post: "V-1 PASS confirmed. V-2 is now unblocked. Targeting Cycle 078 Agent E."
4. Update CYCLE_077_TIERD2_TRACKER.json with agent_d_confirmed: true and current timestamp

---

## Task 5 (SMALL, ~15 min): Cycle 078 Jira story recommendations

Deliverable: `docs/cycle_reports/CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md` written
with at least 8 story recommendations in table format.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md
2. Based on current state, recommend these stories (add/adjust based on V-1 result):
   
   If V-1 PASS:
   - Execute V-2 live parsing validation on V-1 payload (Agent E priority)
   - Execute V-3 full scoring pass and compare to golden anchor (Agent E)
   - Update Score 2 with V-2 evidence (+2%)
   
   Always:
   - Execute Stage 2: docs-only assisted Agent D test on test branch
   - Fix CODECOV_TOKEN and enable Codecov integration (PENDING-001)
   - Raise any src/ modules still below 90%
   - Investigate and fix gh api 401 on branch protection (if BUG-011 still open)
   - Add integration test for live_validation_writer with real data/evidence/
   - Improve Score 1 toward 70% target (current 67.3%)
   
3. Format as table: | Summary | Type | Epic | Acceptance Criteria | Size |
4. Minimum 8 rows; maximum 12 rows (keep it focused)

---

## Task 6 (SMALL, ~10 min): Kevin handoff + final commit

Deliverable: CYCLE_077_KEVIN_HANDOFF.md written; everything committed and pushed;
Jira cycle-control story transitioned to Done.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_KEVIN_HANDOFF.md:
   ```
   # Cycle 077 Complete - Kevin Handoff
   
   ## Status
   All 6 agents completed with AGENT_COMPLETE.
   
   ## V-1 Result
   Status: [PASS/FAIL]
   Score 2: [47.1% or 49.1%]
   TierD-2 cap: [LIFTED or ACTIVE]
   
   ## PR
   PR #89: https://github.com/KevinSGarrett/Fiverr/pull/[N]
   
   ## Your Immediate Actions
   1. Wait for CI on PR #89 — expected to be green
   2. Review and merge PR #89 to develop
   3. Create 8 Jira stories from CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md
   4. Re-verify Cursor model before 2026-06-18 if not already done
   5. If CODECOV_TOKEN still missing: obtain from codecov.io
   
   ## V-2 Status
   [V-2 is UNLOCKED — authorize Agent E in Cycle 078 for V-2 execution]
   OR
   [V-2 still BLOCKED — V-1 failed; investigate and retry V-1 in Cycle 078]
   ```
2. Find Jira story for "Add Jira Done transitions for all Cycle 076 stories after PR merge"
   — post comment and transition to Done
3. Find the Cycle Control story for Cycle 077 — transition to Done
4. Create docs/cycle_reports/CYCLE_077_AGENT_D.md:
   - PR #89 created: URL
   - Merge gate dry-run: PASS/PARTIAL/FAIL
   - SEC-007: PASS | CLAUDE-SUB-007: PASS
   - Jira Done transitions: N stories
   - V-1 evidence posted to TierD-2 epic
   - Cycle 078 story recommendations: M stories
   - Kevin handoff written
   - End with: AGENT_COMPLETE
5. `git add -A`
6. `git commit -m "chore(c077): PR #89, Jira Done transitions, V-1 evidence, C078 story recommendations"`
7. `git push origin cycle/077/integration`

---

## Validation (R-092 Tier 2 — Agent D only)

```bash
python -m ruff check automation/ src/ tests/
python -m mypy automation/ --ignore-missing-imports
python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=xml --cov-fail-under=90 --timeout=60 -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py merge-gate --cycle 077 --dry-run
```

---

## Hard gates

- Do NOT execute merge gate --live
- Do NOT auto-merge PR
- Do NOT modify data/cycle037_live.db
- PR title must be ≤72 chars; no + in scope field; use only letters/numbers/-
- If Jira token fails during transitions: document which stories were NOT transitioned
  and include them in the Kevin handoff as manual action items

---

END OF PROMPT
