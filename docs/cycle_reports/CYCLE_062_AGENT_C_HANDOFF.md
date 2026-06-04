# CYCLE 062 — AGENT C HANDOFF

Post-merge placeholder (do not replace until D finalizes squash): `[C062_SQUASH_SHA]`

## Execution Order

C runs AFTER B AND E. C NEVER waits for F. F runs AFTER C.

## Scope

C is validation/report-only for C062 gate adjudication.

- No implementation work.
- No migration authoring.
- No test-authoring changes.

## Blocking Checks (GO/NO-GO)

### 1) §11 Schema Parity (Blocking)

After B migration_12 is applied, verify table-column parity:

- `PRAGMA table_info(price_analysis)`
- `PRAGMA table_info(niche_price_analysis)`
- `PRAGMA table_info(pricing_snapshots)`

All ORM-declared columns must exist physically.  
If any are missing: immediate NO-GO.

### 2) Dashboard Demo-Data Ban

Run demo-data reference check in dashboard pages:

- Search for `build_dashboard_demo_data`
- Expected result: empty

Any hit: NO-GO.

### 3) Golden Parity (Blocking)

Command:

`py -3.11 run.py score --golden --config-override relevance.enable_stage_3_5=false --config-override analysis.external_signals_enabled=false`

Expected anchor:
- `kw=110` => `62.7 / 1.0 / CONDITIONAL_GO`

Any drift outside gate rules: NO-GO.

### 4) Regression Pack (45 tests)

Run all 45 named regression tests from cycle control pack.  
All must pass.

Any failure: NO-GO.

### 5) Coverage Gate

Run single-project coverage command:

`py -3.11 -m pytest --cov=src --cov-fail-under=90`

Coverage must be >=90 with single `--cov=src` invocation.

### 6) Hard Gate Integrity

Validate no secrets committed, no unresolved review-thread blockers, and no bypass of hard-gate policy.

## Final Verdict Rule

- GO only if all 6 checks pass with evidence.
- Any failed check => NO-GO with exact command output and impact statement.

## Deliverable

`docs/cycle_reports/CYCLE_062_AGENT_C.md` containing:
- command transcripts summary
- pass/fail matrix
- gate-by-gate rationale
- final GO/NO-GO verdict
