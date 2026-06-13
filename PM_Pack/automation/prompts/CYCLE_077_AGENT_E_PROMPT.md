# CYCLE 077 — AGENT E PROMPT
# Dispatched after: Agent B AGENT_COMPLETE
# Branch: cycle/077/integration
# PRIMARY OBJECTIVE: Execute V-1 live collection (1 keyword) — earns +2% Score 2
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight + read all handoffs
- Task 2 (LARGE): 75 min — Execute V-1 live Fiverr collection (1 keyword)
- Task 3 (MEDIUM): 30 min — Archive evidence and update TierD-2 tracker
- Task 4 (MEDIUM): 20 min — Jira V-1 story update + cycle report
Total estimated: ~2 hr 20 min

---

## Context

You are Cursor Agent E for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

This is the most important task in Cycle 077. Executing a single V-1 live collection
earns +2% Score 2, lifts the TierD-2 SEED x17 cap, and unlocks V-2.

Current state:
- Score 1: 67.3% | Score 2: 47.1%
- TierD-2 cap: ≤50% until V-1 PASS
- V-1 procedure: docs/validation/V1_COLLECTION_RUN_PROCEDURE.md
- V-1 evidence writer: automation/live_validation_writer.py
- Evidence schema: docs/validation/live_validation_evidence.schema.json
- Evidence storage: data/evidence/ (gitignored for raw payloads; .gitkeep committed)

The golden anchor set keyword for V-1: use keyword `"python"` (category: programming-tech)
This is a high-signal, low-noise keyword that will produce reliable V-1 evidence.

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch: cycle/077/integration

---

## Task 1 (SMALL, ~15 min): Preflight and read all handoffs

Deliverable: Confirmed on correct branch; Agent A + B work verified; V-1 procedure read.

Sub-steps:
1. `git checkout cycle/077/integration && git pull origin cycle/077/integration`
2. Confirm Agents A + B commits present: `git log --oneline -8`
3. Read docs/cycle_reports/CYCLE_077_AGENT_A.md — note any flags
4. Read docs/cycle_reports/CYCLE_077_AGENT_B.md — note coverage TOTAL value
5. Read docs/validation/V1_COLLECTION_RUN_PROCEDURE.md in full — understand every step
6. Read automation/live_validation_writer.py — understand the write_v1_evidence() API
7. Run: `python automation/ai_cycle_controller.py brain-check` — must PASS
8. Confirm data/evidence/ directory exists (it has a .gitkeep)
9. Confirm Jira story "Execute V-1 live Fiverr collection (1 keyword) and archive evidence"
   exists and is In Progress (or transition it to In Progress now)

---

## Task 2 (LARGE, ~75 min): Execute V-1 live Fiverr collection

Deliverable: Live Fiverr search for keyword "python" completes successfully;
raw payload saved to data/evidence/v1_payload_python.json (gitignored);
live_validation_evidence.json updated with v1_status=PASS;
all 7 live_validation_writer tests still pass.

Sub-steps:
1. Locate the collect-live or search entrypoint:
   - Check: `python run.py --help` for available commands
   - Check: `python run.py collect-live --help` if it exists
   - Check: `python run.py phase2-smoke --keyword python` if collect-live unavailable
   - If no single-keyword command exists, locate the search function in src/ and call it directly
2. Execute a live search for keyword "python" with limit=25 results:
   - Expected: Fiverr search API returns gig listings for "python"
   - Accept any HTTP 200 response with gig data; do not require perfect data
   - If you get rate-limited (429), wait 30 seconds and retry once
   - If you get a 403/401, check if authentication is required and document
3. Capture the raw response payload:
   - Save to: `data/evidence/v1_payload_python.json`
   - This file is gitignored (data/evidence/ is in .gitignore) — that's correct
   - The .gitkeep stays committed; only raw payloads are ignored
4. Validate the payload meets V-1 minimum requirements (per V1_COLLECTION_RUN_PROCEDURE.md):
   - At least 1 gig result returned (not empty)
   - Each result has at minimum: title, seller, price (or any price-adjacent field)
   - Response was not an error page or CAPTCHA
5. If V-1 PASS conditions are met, call `automation/live_validation_writer.py` to record:
   ```python
   from automation.live_validation_writer import write_v1_evidence
   write_v1_evidence(
       keyword="python",
       result_count=N,           # actual number of gigs returned
       payload_path="data/evidence/v1_payload_python.json",
       status="PASS",
       notes="Live Fiverr collection for keyword 'python' — Cycle 077 V-1"
   )
   ```
6. If V-1 FAIL conditions (empty response, error, CAPTCHA, blocked):
   - Save whatever response was received to data/evidence/v1_payload_python_FAIL.json
   - Call write_v1_evidence(..., status="FAIL", notes="<exact reason>")
   - Still proceed to Task 3 — document the failure properly
7. Run: `python -m pytest tests/unit/test_live_validation_writer.py -q --tb=short` — all 7 must pass
8. Verify data/live_validation_evidence.json was created/updated with the new entry

---

## Task 3 (MEDIUM, ~30 min): Archive evidence and update TierD-2 tracker

Deliverable: TierD-2 tracker updated with V-1 result; Score 2 recalculated if PASS;
PRODUCTION_READINESS_SCORECARD.md updated.

Sub-steps:
1. Read the current TIERD2 tracker: docs/cycle_reports/CYCLE_076_TIERD2_TRACKER.json
   (or whichever is the most recent tracker)
2. Create docs/cycle_reports/CYCLE_077_TIERD2_TRACKER.json with updated values:
   - cycle_current: 77
   - v1_status: "PASS" or "FAIL" (based on Task 2 result)
   - v1_keyword: "python"
   - v1_result_count: N (actual)
   - score_2_before_v1: 47.1
   - score_2_after_v1: 49.1 (if PASS; +2% earned) or 47.1 (if FAIL; unchanged)
   - tierd2_cap_lifted: true (if PASS) or false (if FAIL)
   - v2_status: "UNLOCKED" (if V-1 PASS) or "BLOCKED" (if V-1 FAIL)
3. If V-1 PASS: update PM_Pack/02_state_and_history/PRODUCTION_READINESS_SCORECARD.md
   - Score 2: 47.1% → 49.1% (+2.0% V-1 earned)
   - TierD-2 cap: LIFTED (V-1 PASS)
   - Note: TierD-2 x17 multiplier cap no longer blocks Score 2 from exceeding 50%
4. If V-1 FAIL: update scorecard with failure reason; Score 2 unchanged
5. Stage: `git add docs/cycle_reports/CYCLE_077_TIERD2_TRACKER.json PM_Pack/`
6. Verify brain-check and pm-pack-audit still PASS after scorecard update

---

## Task 4 (MEDIUM, ~20 min): Jira V-1 story update + cycle report

Deliverable: Jira V-1 story transitioned to Done (if PASS) or In Progress (if FAIL);
CYCLE_077_AGENT_E.md written; changes committed and pushed.

Sub-steps:
1. Find Jira story "Execute V-1 live Fiverr collection (1 keyword) and archive evidence"
2. Post a detailed comment:
   - Keyword: python
   - Result count: N
   - V-1 status: PASS or FAIL
   - Evidence file: data/live_validation_evidence.json (v1_status updated)
   - TierD-2 impact: Score 2 47.1% → 49.1% (+2.0%) or unchanged
   - Cap lifted: YES or NO
3. If V-1 PASS: transition story to Done (transition_id=41)
4. If V-1 FAIL: leave In Progress; add blocker note to cycle report
5. Also update Jira story "Update TierD-2 tracker with V-1/V-2 evidence":
   - Post comment: "V-1 complete (status: PASS/FAIL). Tracker at CYCLE_077_TIERD2_TRACKER.json"
6. Create docs/cycle_reports/CYCLE_077_AGENT_E.md:
   - V-1 execution result (PASS/FAIL + details)
   - Keyword: python; gig results: N
   - Score 2 updated: 47.1% → NEW_VALUE
   - TierD-2 cap lifted: YES/NO
   - Evidence file created: data/live_validation_evidence.json
   - TIERD2_TRACKER updated: CYCLE_077_TIERD2_TRACKER.json
   - test_live_validation_writer.py: 7/7 PASS
   - Ruff PASS | brain-check PASS | pm-pack-audit PASS
   - End with: AGENT_COMPLETE
7. `git add -A`
8. `git commit -m "feat(v1): execute V-1 live Fiverr collection (python keyword), update TierD-2 tracker"`
9. `git push origin cycle/077/integration`

---

## Validation (R-092 Tier 1)

```bash
python -m pytest tests/unit/test_live_validation_writer.py -q --tb=short --timeout=30
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python -m ruff check automation/ src/ tests/
```

---

## Hard gates

- Do NOT modify data/cycle037_live.db
- Do NOT commit data/evidence/v1_payload_*.json (it is gitignored by design)
- DO commit data/live_validation_evidence.json (it records structured evidence, not raw payloads)
- Do NOT fabricate or estimate V-1 result counts — use the actual response
- If V-1 collection fails completely (network error, no module, import error):
  set status="FAIL", document the exact error, and proceed to write the cycle report
- V-1 FAIL is acceptable this cycle; what matters is the attempt is documented
- Do NOT skip to Agent C without completing Tasks 2-3

---

END OF PROMPT
