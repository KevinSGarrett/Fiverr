# ADR 022: Pre-Merge Artifact Governance

- Status: Accepted
- Date: 2026-06-13
- Owner: Cycle 078 Agent D

## Context

Merge execution previously relied on runtime checks only. A deterministic artifact proving pre-merge PASS at a specific HEAD SHA was required for auditable governance.

## Decision

`execute_merge()` now requires a pre-merge artifact at:

- `PM_Pack/automation/merge_gates/PR_<NNNN>_PRE_MERGE_PASS.json`

The artifact must exist and its `head_sha` must match current branch `HEAD`.

If missing or stale:

- raise `MergeBlockedError("PRE_MERGE_ARTIFACT_MISSING")`
- raise `MergeBlockedError("PRE_MERGE_ARTIFACT_STALE: SHA mismatch")`

## Consequences

- Merge execution is fail-closed when governance artifact is absent/stale.
- Audit trail exists for merge decisions and SHA integrity.
