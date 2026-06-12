# Architecture Overview

The Fiverr Autonomous Runner architecture combines PM state authority, automation orchestration, CI governance, and controlled execution loops.

## Text Diagram

```text
          +---------------------+
          |    PM_Pack Brain    |
          | hydration/canonical |
          +----------+----------+
                     |
                     v
          +----------------------+
          | ai_cycle_controller  |
          | plan/validate/dispatch|
          +----+------------+----+
               |            |
               v            v
     +---------------+   +------------------+
     | prompt system |   | policy gates     |
     | gen/validate  |   | model/freeze/QA  |
     +-------+-------+   +--------+---------+
             |                    |
             v                    v
      +-------------+      +--------------+
      | Agent runs  |----->| repair loops |
      | A/B/E/C/F/D |      | + incidents  |
      +------+------+      +------+-------+
             |                    |
             v                    v
      +-------------+      +--------------+
      | CI + checks |<-----| merge gate   |
      | lint/type/test|     | codex/codecov|
      +------+------+      +------+-------+
             |                    |
             +---------+----------+
                       v
               +---------------+
               | cycle reports |
               | PM closeout   |
               +---------------+
```

## Core Principles

1. PMPack state files are authoritative and must remain synchronized.
2. Controller governs planning, validation, and merge-readiness gates.
3. Model policy and freeze policy are hard controls.
4. Repair loops are auditable and bounded by explicit evidence checks.
5. CI + Codecov + review gates protect develop/main branch integrity.

This architecture is optimized for repeatable autonomous cycles with explicit governance checkpoints.

## Data and Control Flow Notes

- PM state updates happen first, then planning and validation.
- Dispatch is blocked unless model and freeze gates are green.
- Repair loops feed back into validation before any closure claims.
- Merge readiness depends on CI, coverage, review disposition, and policy evidence.

## Operational Boundary

Source implementation in `src/` is separate from governance and orchestration in PM_Pack/docs/automation controls. This separation keeps planning authority independent from feature code while still enforcing end-to-end quality gates through CI and post-cycle review.

