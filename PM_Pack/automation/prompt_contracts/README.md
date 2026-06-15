# Prompt Contracts

This directory stores per-agent prompt contract artifacts used as structured input to prompt rendering for each cycle.

## Naming Convention

- `CYCLE_NNN_AGENT_X.contract.json`
- Example: `CYCLE_079_AGENT_E.contract.json`

## Schema

Contracts are validated against:

- `automation/schemas/prompt_contract.schema.json`

Lineage metadata is carried in:

- `metadata.sources_used` (catalog files, Jira keys, and plan references)

## Generation Flow

- Contracts are generated from Cycle planning/Jira scope using `automation/prompt_contract_builder.py` interfaces.
- Renderers consume the contract payloads to produce draft prompts in `PM_Pack/automation/prompts/drafts/`.
- Validation promotion records gate results in `PM_Pack/automation/prompts/validated/CYCLE_NNN_VALIDATION_REPORT.json`.
- Dispatch consumes only validated prompt artifacts in `PM_Pack/automation/prompts/validated/`.

## Invalid Contract Behavior

- If a contract is invalid, schema validation fails and dispatch preparation is blocked.
- Invalid or missing contract data should be fixed before rendering and promotion into `prompts/validated/`.
