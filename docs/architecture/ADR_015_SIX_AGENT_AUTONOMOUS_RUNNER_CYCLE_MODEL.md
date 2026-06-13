# ADR-015: Six-Agent Autonomous Runner Cycle Model

## Status

ACCEPTED

## Context

Single-agent cycle execution reached throughput and reliability limits for governance-heavy, evidence-heavy cycle operations.

## Decision

Adopt fixed six-agent order:

`A -> (B + E in parallel) -> C -> F -> D`

with explicit handoff contracts and `AGENT_COMPLETE` completion markers in cycle reports.

## Consequences

- Parallel B/E execution reduces cycle wall-clock time.
- Explicit handoffs improve auditability and reduce skipped prerequisites.
- Agent A remains the setup/governance gatekeeper before execution fan-out.

## Effective Since

Cycle 070.
