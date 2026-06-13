# ADR-008 Two-Score Model (Internal vs E2E)

## Status
ACCEPTED

## Context
Single completion percentages overstated production readiness.

## Decision
Maintain Score 1 (internal build) and Score 2 (E2E readiness), with Score 2 evidence-capped.

## Rationale
Separating implementation progress from live operational readiness prevents inflated production claims.

## Consequences
Reports must always show both scores and explain cap logic; governance audits must validate consistency.

