# CYCLE 077 — AGENT C PROMPT
# Dispatched after: Agents A + B + E all AGENT_COMPLETE
# Branch: cycle/077/integration
# Generated: 2026-06-12 by Claude PM post-Cycle 076 review

## Agent Time Budget (estimated)
- Task 1 (SMALL): 15 min — Preflight + read all three handoffs
- Task 2 (MEDIUM): 30 min — Validate V-1 evidence against schema
- Task 3 (MEDIUM): 35 min — Integration check: coverage + CI simulation
- Task 4 (SMALL): 20 min — Cross-agent consistency audit
- Task 5 (SMALL): 10 min — Cycle report + commit
Total estimated: ~1 hr 50 min

---

## Context

You are Cursor Agent C for the Fiverr Research System 24/7 Autonomous Runner, Cycle 077.

Agents A, B, and E have completed. Your role is verification and integration:
- Validate V-1 evidence passes the schema
- Confirm coverage is still ≥90% after all changes
- Confirm CI would pass with current branch state
- Audit all three agent handoffs for consistency

Repository: C:\Fiverr\Fiverr
Jira cloud ID: eae77257-a572-4e19-b746-8b184ba2d01f
Branch: cycle/077/integration

---

## Task 1 (SMALL, ~15 min): Preflight and read all handoffs

Sub-steps:
1. `git checkout cycle/077/integration && git pull origin cycle/077/integration`
2. `git log --oneline -10` — confirm Agent A, B, E commits all present
3. Read docs/cycle_reports/CYCLE_077_AGENT_A.md
4. Read docs/cycle_reports/CYCLE_077_AGENT_B.md
5. Read docs/cycle_reports/CYCLE_077_AGENT_E.md
6. Note V-1 status (PASS or FAIL), coverage TOTAL, any open flags
7. Run: `python automation/ai_cycle_controller.py brain-check` — must PASS
8. Run: `python -m ruff check automation/ src/ tests/` — 0 errors
9. Run: `python -m mypy automation/ --ignore-missing-imports` — 0 errors

---

## Task 2 (MEDIUM, ~30 min): Validate V-1 evidence against schema

Deliverable: V-1 evidence passes schema validation; schema compliance documented.

Sub-steps:
1. Load the V-1 evidence schema: docs/validation/live_validation_evidence.schema.json
2. Load the actual evidence: data/live_validation_evidence.json
3. Validate using jsonschema:
   ```python
   import json
   from jsonschema import validate, ValidationError
   schema = json.load(open("docs/validation/live_validation_evidence.schema.json"))
   evidence = json.load(open("data/live_validation_evidence.json"))
   try:
       validate(instance=evidence, schema=schema)
       print("SCHEMA VALIDATION: PASS")
   except ValidationError as e:
       print(f"SCHEMA VALIDATION: FAIL — {e.message}")
   ```
4. If schema validation FAILS: document the specific violation; check if schema needs updating
   to accommodate the actual evidence structure Agent E produced
5. If schema needs updating (evidence format differs from schema expectations):
   - Update docs/validation/live_validation_evidence.schema.json to match actual structure
   - Re-validate with updated schema
   - Note: schema should be updated to match evidence, not vice versa
6. Verify V-1 evidence contains required fields:
   - keyword field present
   - result_count field present (integer ≥0)
   - status field is "PASS" or "FAIL"
   - timestamp field present
7. Run all 7 live_validation_writer tests:
   `python -m pytest tests/unit/test_live_validation_writer.py -v --tb=short --timeout=30`
8. Document schema validation result in cycle report

---

## Task 3 (MEDIUM, ~35 min): Integration check — coverage + CI simulation

Deliverable: Full unit test suite passes with ≥90% coverage; no regressions from
Agents A/B/E changes; CI simulation confirms all 4 jobs would pass.

Sub-steps:
1. Run the full unit test suite:
   `python -m pytest tests/unit/ --cov=automation --cov=src --cov-report=term-missing -q --timeout=60`
2. Record the TOTAL coverage percentage — must be ≥90%
3. If any tests FAIL (unexpected):
   - Run failing test individually with `-v --tb=long` to see full output
   - Fix the failure (likely an import or assertion issue from Agent changes)
   - Re-run full suite after fix
4. Simulate CI lint job: `python -m ruff check automation/ src/ tests/` — 0 errors
5. Simulate CI type-check job: `python -m mypy automation/ --ignore-missing-imports` — 0 errors
6. Simulate CI smoke-gates:
   `python automation/ai_cycle_controller.py compile-policy`
   `python automation/ai_cycle_controller.py brain-check`
   `python automation/ai_cycle_controller.py pm-pack-audit`
7. All 4 simulated CI jobs must PASS before proceeding
8. If coverage drops below 90% after Agent B/E changes: identify which module dropped
   and add targeted tests to restore it

---

## Task 4 (SMALL, ~20 min): Cross-agent consistency audit

Deliverable: All PM_Pack state documents consistent with each other and with
Cycle 077 cycle reports; TierD-2 tracker matches scorecard.

Sub-steps:
1. Read PM_Pack/07_hydration/HYDRATION_HEADER.md — confirm CYCLE_CURRENT=077
2. Read PM_Pack/02_state_and_history/STATE_SNAPSHOT.md — confirm last_completed_cycle=076
3. Read PM_Pack/02_state_and_history/PRODUCTION_READINESS_SCORECARD.md:
   - If V-1 PASS: Score 2 should show 49.1%; TierD-2 cap should show LIFTED
   - If V-1 FAIL: Score 2 should show 47.1%; TierD-2 cap should show ACTIVE
4. Read docs/cycle_reports/CYCLE_077_TIERD2_TRACKER.json — confirm v1_status matches
5. Cross-check: all three documents must agree on V-1 status and Score 2 value
6. If inconsistency found: fix whichever file is wrong; re-run pm-pack-audit
7. Verify docs/architecture/ has 15 ADRs (ADR_001 through ADR_015)
8. Stage any fixes: `git add PM_Pack/ docs/`

---

## Task 5 (SMALL, ~10 min): Cycle report + commit

Deliverable: CYCLE_077_AGENT_C.md written; all changes committed and pushed.

Sub-steps:
1. Create docs/cycle_reports/CYCLE_077_AGENT_C.md:
   - V-1 schema validation: PASS/FAIL (with details if FAIL)
   - Full suite coverage: N% (PASS/FAIL gate)
   - Tests: N passed, N failed (must be 0 unexpected failures)
   - Ruff PASS | Mypy PASS | brain-check PASS | pm-pack-audit PASS
   - CI simulation: all 4 jobs PASS
   - Cross-agent consistency: consistent/inconsistency-found-and-fixed
   - ADR count: 15/15 present
   - End with: AGENT_COMPLETE
2. Find Jira story "Raise combined automation+src coverage to >=90%" — post comment
   with current TOTAL coverage value
3. `git add -A`
4. `git commit -m "verify(c077): V-1 schema validation, integration check, cross-agent consistency audit"`
5. `git push origin cycle/077/integration`

---

## Validation (R-092 Tier 1)

```bash
python -m pytest tests/unit/ --cov=automation --cov=src -q --timeout=60 | tail -5
python -m ruff check automation/ src/ tests/
python -m mypy automation/ --ignore-missing-imports
python automation/ai_cycle_controller.py brain-check
```

---

## Hard gates

- Do NOT proceed if full suite coverage drops below 90%
- Do NOT proceed if brain-check FAILS
- Do NOT modify data/cycle037_live.db
- If V-1 schema validation fails and cannot be fixed this cycle, document it and
  flag as CYCLE_078 priority — do NOT block the rest of the cycle for this

---

END OF PROMPT
