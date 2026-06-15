# ADR 016: PM_Pack Policy Unification

## Status
Accepted

## Context
Prompt and governance files diverged across cycles, leading to inconsistent lane counts, task floors, and agent git behavior.

## Decision
Unify policy across these artifacts:
- `PM_Pack/03_cursor_agent_system/PROMPT_TEMPLATE.md`
- `PM_Pack/03_cursor_agent_system/PROMPT_RULES.md`
- `PM_Pack/03_cursor_agent_system/AGENT_TASK_FLOOR_ENFORCEMENT.md`
- `PM_Pack/automation/agent_lanes.yml`
- `automation/prompt_validator.py`

Canonical decisions:
- Task floor = 55 minimum.
- Lane system = `A, B, E, C, F, D`.
- Git operations are controller-only.

## Consequences
Prompt generation, validation, and dispatch gating are aligned to one policy baseline and reject stale four-lane or low-task prompts.
