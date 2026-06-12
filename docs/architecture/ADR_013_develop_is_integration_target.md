# ADR-013: develop Branch Is the Integration Target; main Is Release-Only

## Status
Accepted

## Context
The repository has two long-lived branches: main and develop. A decision must be made
about which branch cycle PRs target, what merge policies apply, and when main is updated.

## Decision
- All cycle PRs target `develop`. No cycle PR may target `main`.
- `develop` requires PR + passing CI (lint, type-check, tests-coverage, smoke-gates) +
  Codecov project and patch gates + Codex review disposition check + model evidence check.
- `main` is release-only. Only deliberate release PRs from develop merge to main.
  These require explicit human approval and are outside the autonomous cycle workflow.
- The merge_gate.py branch guard enforces this by blocking any PR that targets main.
- No force-push is permitted on either branch.

## Consequences
- Autonomous cycles can never pollute main.
- develop accumulates cycle work; main represents deliberately released versions.
- The branch protection settings for develop and main must reflect these rules.
- Breaking changes between cycles are isolated to the cycle/NNN/integration branch
  until explicitly merged to develop.
