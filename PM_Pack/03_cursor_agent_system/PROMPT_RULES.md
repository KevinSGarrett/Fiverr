# PROMPT RULES (Cycle 078 Governance)

## Hard Floor
- Every agent prompt must contain >=55 LARGE tasks per cycle.
- Each task must be >=3 sentences and include explicit validation commands.
- Task header grammar: `### TASK NN — Description`.

## Lane System
- Active lanes are six-agent only: `A, B, E, C, F, D`.
- Four-lane references (`A, B, C, D`) are deprecated and invalid.

## Git Policy
- Git operations are controller-only.
- Agents must never stage, commit, or push.
- Prompts must not include runnable `git add`, `git commit`, or `git push` commands.

## Mandatory Prompt Content
- Model policy block: Cursor Codex 5.3, medium effort, Auto disabled.
- Secrets reference block with canonical `.env` and `runner.env` paths.
- PM_Pack reference block to `project_plan`, `dod`, and `todo`.
- Validation command block (`ruff`, `mypy`, `pytest`, `brain-check`, `pm-pack-audit`).

## Rejection Conditions
- Fewer than 55 tasks.
- Missing `END OF PROMPT`.
- Missing cycle branch `cycle/NNN/integration`.
- Missing final report path under `docs/cycle_reports/`.
- Any instruction that bypasses prompt validation during dispatch.
