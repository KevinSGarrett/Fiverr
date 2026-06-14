# ADR 023: Post-Merge vs Pre-Merge Gate Responsibilities

- Status: Accepted
- Date: 2026-06-13
- Owner: Cycle 078 Agent D

## Context

Pre-merge blocking policy and post-merge retrospective verification were conflated, causing unclear merge responsibilities.

## Decision

- **Pre-merge gate** remains blocking and determines merge eligibility.
- **Post-merge verification** is informational/retrospective and writes:
  - `PM_Pack/automation/merge_gates/PR_<NNNN>_POST_MERGE_VERIFICATION.json`

Controller CLI path:

- `python automation/ai_cycle_controller.py merge-gate --post-merge --pr <NNN>`

## Consequences

- Merge safety is strictly enforced before merge.
- Post-merge evidence is still captured without retroactively mutating merge decisions.
