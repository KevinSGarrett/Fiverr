# ADR-005 Controller Owns Git, Agents Do Not Commit

## Status
ACCEPTED

## Context
Agents can technically perform git operations but may commit incomplete or unsafe changes without centralized checks.

## Decision
Controller exclusively handles `git add`, `git commit`, and `git push`.

## Rationale
Centralized git control reduces risk of secret leakage, partial commits, and incorrect branch operations.

## Consequences
Agent prompts must explicitly prohibit commits. Controller workload increases due to final staging and merge hygiene responsibilities.

