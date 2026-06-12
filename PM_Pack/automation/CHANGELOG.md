# Automation Changelog

## 2026-06-11 — V5 Correction Session

### Summary

Cycle governance and automation policy controls were corrected to close all 15 AUDIT-P0/P1 findings. The correction window aligned PMPack state authority, model policy enforcement, and workflow gating readiness for Cycle 075.

### Key Changes

1. Standardized two-score governance language across core PM state files.
2. Reconciled stale cycle references and refreshed active-cycle state.
3. Hardened prompt and planning governance around floor and validation expectations.
4. Confirmed runner recovery posture and freeze-lift sequencing.
5. Stabilized cycle handoff posture for Stage 1 dry-run progression.

### Evidence Commits (develop)

- `9a2948a`
- `f8f2e11`
- `982c2ef`
- `87b5f92`

### Operational Impact

- PMPack consistency checks return PASS.
- Brain-check remains green.
- Active cycle moved into controlled execution posture for Cycle 075.
- Governance documents now treat hydration state as highest authority.

### Known Follow-up

- Branch protection evidence capture blocked by current local `gh` authentication state.
- TierD-2 remains SEED x17 and continues to cap full Score 2 advancement pending live evidence.

### Validation Notes

- `pm-pack-audit` returns PASS (with non-blocking warnings requiring later cleanup).
- `brain-check` returns PASS.
- Workflow YAML parse for runner smoke passes.

### Why This Matters

The correction session converts the cycle from a partially contradictory governance state to a controlled, auditable execution state. This prevents stale documentation from driving wrong planning decisions and ensures model/runner policy controls are active before additional go-live advancement.

## Cycle 076 — 2026-06-12

### Added
- ADR-011: Repair loop uses git stash for quarantine
- ADR-012: Six-agent execution order canonical definition
- ADR-013: develop is integration target; main is release-only

### Fixed
- All deprecated Ruff text-format references replaced with --output-format=full (see below)

