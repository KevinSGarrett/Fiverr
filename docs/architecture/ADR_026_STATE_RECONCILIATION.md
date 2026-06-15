# ADR 026: State Reconciliation Protocol

## Status
Accepted

## Context
Post-Cycle 079 state drift showed contradictory cycle values across hydration metadata and runner state:
- `policy_compiler.py` parsed hydration using patterns that did not consistently align with header formats.
- `C:/AI_Runner/state/controller_state.json` and `C:/AI_Runner/state/heartbeat.json` were not advanced after Cycle 079 merge.
- Result: cycle detection and audit signals drifted between hydration/state/policy snapshot sources.

## Decision
- `HYDRATION_HEADER.md` must use `Active cycle:` in human-readable cycle headers for every cycle rollover.
- `policy_compiler.py` must support both `CYCLE_CURRENT:` and `Active cycle:` compatible hydration formats.
- Agent A must update hydration header cycle metadata as the first task of each cycle.
- Agent A must reconcile runner state (`controller_state.json`, `heartbeat.json`) before dispatch gate checks.

## Implementation Note
- Policy compiler fix referenced by governance: SHA `5e33cb4`.

## Consequences
- Compile-policy output and PM pack audit become cycle-consistent earlier in each cycle.
- Dispatch preconditions become deterministic for downstream agents.
- State reconciliation is a required startup governance gate, not a best-effort task.
