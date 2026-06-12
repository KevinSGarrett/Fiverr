# ADR-010 Post-Cycle PM Review Mandatory Between Cycles

## Status
ACCEPTED

## Context
Running cycles without post-cycle review allowed stale assumptions and unresolved contradictions to compound.

## Decision
Require post-cycle PM review between every cycle transition.

## Rationale
Mandatory review enforces state reconciliation, evidence validation, and blocker visibility before next dispatch.

## Consequences
Cycle throughput can decrease slightly, but governance integrity and operational predictability improve significantly.

