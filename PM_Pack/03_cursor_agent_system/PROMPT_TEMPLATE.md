# CURSOR AGENT PROMPT TEMPLATE (Cycle 078)

Use this template for every cycle prompt in lane order `A, B, E, C, F, D`.

## Model Policy — MANDATORY
- Model: Cursor Codex 5.3
- Effort: medium
- Auto-suggest: DISABLED

## Secrets and Environment Reference
- Master `.env`: `C:\Fiverr\Fiverr\.env` (SOURCE OF TRUTH)
- Runner secrets: `C:\AI_Runner\secrets\runner.env`
- Required keys:
  - `JIRA_API_TOKEN` (exact name — not `JIRA_API` or `JIRA_TOKEN`)
  - `JIRA_EMAIL`
  - `JIRA_BASE_URL`
  - `GH_AUTOMATION_TOKEN`
  - `OPENAI_API_KEY`
  - `SCRAPFLY_API_KEY`
- `config_loader` resolution order: `runner.env` -> `os.environ` -> `.env`

## Project Plan Reference
Before implementation, read the relevant plan file:
- `C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\` — what is being built
- `C:\Fiverr\Fiverr\PM_Pack\ref\dod\` — done criteria per epic
- `C:\Fiverr\Fiverr\PM_Pack\ref\todo\` — open work per epic

## Git Operations Policy
The controller owns ALL git operations.
Agents MUST NOT run `git add`, `git commit`, or `git push`.

## Prompt Skeleton
```
====================================================================
AGENT {A|B|E|C|F|D} — CYCLE {NNN} PROMPT
====================================================================

## PROJECT CONTEXT
- Project: Fiverr Research System
- Repo root: C:\Fiverr\Fiverr
- Branch target: cycle/{NNN}/integration
- Lane order: A, B, E, C, F, D

## TASK FLOOR
- Minimum tasks: 55 LARGE-XXLARGE tasks
- Task format: ### TASK NN — Description
- Every task includes validation commands and evidence expectations

## TASKS
### TASK 01 — ...
...
### TASK 55 — ...

## VALIDATION COMMANDS
- ruff check ...
- mypy ...
- pytest ...
- python automation/ai_cycle_controller.py brain-check
- python automation/ai_cycle_controller.py pm-pack-audit --check-only

## REPORT
- Write: docs/cycle_reports/CYCLE_{NNN}_AGENT_{AGENT}.md
- Final line must be: AGENT_COMPLETE

END OF PROMPT
```
