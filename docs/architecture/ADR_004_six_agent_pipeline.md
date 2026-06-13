# ADR-004 Six-Agent Pipeline (A -> B+E -> C -> F -> D)

## Status
ACCEPTED

## Context
The cycle design could run as fewer broad agents or more specialized agents.

## Decision
Adopt six-agent pipeline with explicit role boundaries.

## Rationale
Separating planning, implementation, validation, integration, coverage, and PR governance reduces role confusion and keeps quality gates explicit.

## Consequences
Cycle overhead and prompt-writing effort increase, but governance clarity and accountability improve.

