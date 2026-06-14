# ADR 020: Prompt Factory Architecture

## Status
Accepted

## Context
Cycle 078 requires deterministic generation of six agent prompts from Jira scope, PM_Pack policy context, and PM_Pack/ref catalogs. Dispatch must be blocked unless prompts pass validation and are promoted to a trusted location.

## Decision
Use a two-step prompt package pipeline:

1. `automation/prompt_contract_builder.py` builds full prompt contracts from Jira AC/DoD, lane metadata, and catalog context.
2. `automation/prompt_promotion.py` validates each draft prompt and promotes only passing prompts into `PM_Pack/automation/prompts/validated/`.

Controller integration in `automation/ai_cycle_controller.py`:

- `plan-cycle --live` now:
  - loads Jira inventory (`acceptance_criteria` and `definition_of_done`)
  - builds draft files under `PM_Pack/automation/prompts/CYCLE_078/`
  - promotes valid prompts to `PM_Pack/automation/prompts/validated/`
  - writes `PM_Pack/automation/prompts/validated/CYCLE_078_MANIFEST.json`
- `run-agent` now reads prompt input from `prompts/validated/` only and exits non-zero if the prompt is missing there.

## Consequences

- Dispatch path is fail-closed on prompt validation.
- Cycle prompt package status is machine-readable via validated manifest.
- Prompt generation remains aligned to PM_Pack policy and Jira AC/DoD hydration.
