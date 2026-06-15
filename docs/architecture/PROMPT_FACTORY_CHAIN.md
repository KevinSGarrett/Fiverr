# PROMPT_FACTORY_CHAIN

## Artifact Chain
- `board_inventory.json` (Jira stories with AC/DoD)
- `PM_Pack/automation/project_plan_catalog.json` (spec cross-reference)
- `PM_Pack/automation/prompt_contracts/CYCLE_NNN_AGENT_X.contract.json` (structured input)
- `PM_Pack/automation/prompts/drafts/CYCLE_NNN_AGENT_X_DRAFT.md` (rendered markdown)
- Validation output: `CYCLE_NNN_VALIDATION_REPORT.json`
- Promotion output: `PM_Pack/automation/prompts/validated/CYCLE_NNN_AGENT_X_PROMPT.md`
- `CYCLE_NNN_MANIFEST.json` (deployment manifest)
- `prompt_package_manifest.json` (dispatch gate)

Cursor dispatch reads only from `PM_Pack/automation/prompts/validated/`.
