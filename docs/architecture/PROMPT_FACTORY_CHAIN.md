# PROMPT_FACTORY_CHAIN v2

## Artifact Chain
- `board_inventory.json` (Jira stories with AC/DoD)
- Step 2: Catalog build (`python automation/ref_catalog_builder.py build`)
- `PM_Pack/automation/project_plan_catalog.json` (spec cross-reference)
- `PM_Pack/automation/dod_catalog.json`
- `PM_Pack/automation/todo_epic_catalog.json`
- `PM_Pack/automation/github_governance_catalog.json`
- Step 2b: Catalog schema validation before mapping:
  - `automation/schemas/project_plan_catalog.schema.json`
  - `automation/schemas/dod_catalog.schema.json`
  - `automation/schemas/todo_epic_catalog.schema.json`
  - `automation/schemas/github_governance_catalog.schema.json`
- `PM_Pack/automation/prompt_contracts/CYCLE_NNN_AGENT_X.contract.json` (structured input)
- `PM_Pack/automation/prompts/drafts/CYCLE_NNN_AGENT_X_DRAFT.md` (rendered markdown)
- Validation output: `CYCLE_NNN_VALIDATION_REPORT.json`
- Promotion output: `PM_Pack/automation/prompts/validated/CYCLE_NNN_AGENT_X_PROMPT.md`
- `CYCLE_NNN_MANIFEST.json` (deployment manifest)
- `prompt_package_manifest.json` (dispatch gate)

## Cycle 081 Note
- Cycle `081` uses the schema-validation Step `2b` as a hard precondition before prompt contract generation.

Cursor dispatch reads only from `PM_Pack/automation/prompts/validated/`.
