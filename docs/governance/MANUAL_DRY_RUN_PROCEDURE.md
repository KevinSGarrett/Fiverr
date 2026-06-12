# Manual Dry-Run Procedure (OPS-030)

This procedure defines Go-Live Stage 1 dry-run evidence requirements. Stage 1 proves planning and validation quality without dispatching agents and without pushing git changes.

## Objective

Demonstrate that cycle prompt generation and prompt validation are stable, complete, and policy-compliant for Cycle 075.

## Required Command Sequence

Run in repo root:

```powershell
Set-Location C:\Fiverr\Fiverr
python automation/ai_cycle_controller.py plan-cycle --live --cycle 075
python automation/ai_cycle_controller.py validate-prompts --cycle 075
```

## Expected Output Characteristics

### plan-cycle --live --cycle 075

- Generates six real prompts (A, B, E, C, F, D).
- Each prompt includes 55 or more LARGE tasks.
- Prompt files land in expected dispatch planning locations.
- Planning report includes no stale-cycle mismatch.

### validate-prompts --cycle 075

- Confirms all six prompts meet quality gates.
- Confirms floor and structure checks pass.
- Flags any missing section, unsafe directive, or placeholder content.
- Produces clear PASS/FAIL result with file-level details.

## Stage 1 COMPLETE Definition

Stage 1 is COMPLETE only when all conditions are true:

1. Six real prompts are generated.
2. Each prompt contains at least 55 LARGE tasks.
3. All prompts pass validation.
4. No Cursor dispatch occurred.
5. No `git push` occurred.

## Evidence to Archive

- Planning output logs
- Validation output logs
- Prompt file paths and timestamps
- Stage 1 completion note in cycle report

If any condition fails, Stage 1 remains IN_PROGRESS and must be rerun after correction.

