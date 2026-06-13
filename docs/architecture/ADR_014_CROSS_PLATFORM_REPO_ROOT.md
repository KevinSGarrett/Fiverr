# ADR-014: Cross-Platform Repository Root Resolution

## Status

ACCEPTED

## Context

Multiple automation modules historically hardcoded `C:/Fiverr/Fiverr` paths. This created portability and CI/runtime issues across Windows and Linux runner environments.

## Decision

Standardize repo-root derivation using path traversal from file location (for example `Path(__file__).resolve().parent.parent`) or equivalent deterministic root discovery, instead of hardcoded host paths.

## Consequences

- Improves compatibility for Windows and Linux CI/runner nodes.
- Reduces fragile path assumptions in automation scripts.
- Requires consistent path-helper use in future automation additions.

## Implementing Commits

- cycle/077/integration (documentation/state alignment cycle)
