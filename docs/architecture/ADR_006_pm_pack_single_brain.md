# ADR-006 PM_Pack as Single Brain Source of Truth

## Status
ACCEPTED

## Context
Distributed state across many docs caused contradictions and stale cycle data.

## Decision
Treat PM_Pack state authority files as the canonical control brain.

## Rationale
Centralized canonical files reduce ambiguity and allow audit tooling to enforce consistency.

## Consequences
Governance transactions must keep PM_Pack synchronized each cycle; stale-state drift becomes a blocking issue.

