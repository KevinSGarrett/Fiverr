# BUILD SEQUENCE EXCEPTION LOG

## V5 Audit Exception Window

Period covered: 2026-06-09 through 2026-06-11

## Exception 1 — Prompt Floor Violation

- Status: RESOLVED
- Date discovered: 2026-06-09
- Commit evidence: `1428a92`
- Root cause: no hard verification loop enforcing 55-task minimum across A/B/E/F
- Impact: dispatch quality drift and under-scoped execution prompts
- Resolution: `AGENT_TASK_FLOOR_ENFORCEMENT.md` promoted to hard policy; enforcement logic added to Agent A governance scope
- Preventing recurrence: floor verification included in planning validation gate

## Exception 2 — STATE_SNAPSHOT Stale at C049

- Status: RESOLVED
- Date discovered: 2026-06-10
- Root cause: stale synchronization between canonical cycle state and snapshot state
- Impact: contradictory cycle reference in governance files
- Resolution: reconciled state to Cycle 075 and validated with `pm-pack-audit` PASS
- Preventing recurrence: include state snapshot verification in governance transaction checklist

## Exception 3 — Dispatch Stub Prompt Contamination

- Status: RESOLVED
- Date discovered: 2026-06-10
- Root cause: 12 stub prompts remained in dispatch-visible directories
- Impact: risk of accidental dispatch of invalid prompt artifacts
- Resolution: moved to `drafts/STUBDONOTDISPATCH*` pattern
- Preventing recurrence: naming guard and dispatch directory preflight check

## Exception 4 — Runner Credentials in ZIP Artifacts

- Status: RESOLVED
- Date discovered: 2026-06-11
- Root cause: sanitizer logic depended on path heuristics instead of value-pattern detection
- Impact: potential credential exposure in archived artifacts
- Resolution: sanitizer rewritten with value-based detection; affected tokens rotated
- Preventing recurrence: archive scans and token-handling guardrails in export workflow

## Current Open Exceptions

None.  
All V5 exceptions above are closed and marked RESOLVED.

