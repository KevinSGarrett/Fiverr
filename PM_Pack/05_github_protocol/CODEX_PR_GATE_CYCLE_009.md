# CODEX PR GATE — Cycle 009

## Active PR

PR #7: `feat(cycle-008): enforce jira story mapping and harden phase 2 contracts`

## Active blocker

Codex P2 thread in `src/collection/contracts.py`:
- `validate_collection_stage_summary` must not treat `stage_counts` dictionary key order as authoritative.
- `stage_names` represents execution order.
- `stage_counts` represents an unordered mapping.
- JSON checkpoint persistence may sort nested keys.

## Required handling

The GitHub steward must not merge PR #7 until:

1. The collection validation logic is fixed or formally dispositioned.
2. Regression coverage proves checkpoint-style sorted JSON round trips do not break valid stage summaries.
3. Codex is replied to with the required disposition format.
4. The Codex thread is resolved only after fix + checks.
5. GitHub Actions are green.
6. codecov/project and codecov/patch are green.
7. Local parity passes with >=90% coverage.
8. Jira mapping includes all changed file groups and product stories.

## Required disposition for this finding if fixed

`VALID_FIXED`

Required reply must include:
- Root cause
- Files changed
- Regression tests
- Validation commands
- Checks status
- Resolve thread after push/checks: Yes
