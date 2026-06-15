# ADR 017: Prompt Dispatch Safety

## Status
Accepted

## Context
Dispatch logic previously allowed prompt validation failure to proceed under `--safe-docs-only`, creating an unsafe bypass.

## Decision
- `safe-docs-only` may relax model gate only.
- Prompt validation failure always blocks dispatch with non-zero exit.
- `cursor-docs-smoke` is the only docs smoke command.
- Production dispatch source remains `PM_Pack/automation/prompts/`.

## Consequences
All dispatch paths enforce prompt correctness. Smoke checks remain available through a dedicated non-production command without weakening dispatch controls.
