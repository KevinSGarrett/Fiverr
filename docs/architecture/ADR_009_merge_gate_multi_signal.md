# ADR-009 Merge Gate Requires CI, Codecov, Codex, Jira Signals

## Status
ACCEPTED

## Context
Merge safety requires more than unit tests.

## Decision
Require all four CI checks, two Codecov checks, Codex review disposition, and Jira/control state for merge readiness.

## Rationale
Multi-signal gating reduces false-positive merges and enforces governance and quality across tooling layers.

## Consequences
Merges may be slower but become auditable and less error-prone. Token/auth failures can block merges and must be handled operationally.

