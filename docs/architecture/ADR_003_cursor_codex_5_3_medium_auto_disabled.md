# ADR-003 Cursor Codex 5.3 Medium, Auto Disabled

## Status
ACCEPTED

## Context
Cursor offers multiple models and automatic selection behavior.

## Decision
Pin to Codex 5.3 at medium effort. Disable Auto and fallback.

## Rationale
Deterministic model configuration improves reproducibility and policy compliance while balancing speed/quality.

## Consequences
Verification must be refreshed after updates and session expiry events to prevent silent drift.

