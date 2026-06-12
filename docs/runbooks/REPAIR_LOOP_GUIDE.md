# Repair Loop Guide

The repair loop is the controlled mechanism for correcting failed validations, missing artifacts, or governance mismatches without losing auditability. It is not a free-form retry system; each loop iteration must be evidence-backed.

## When to Trigger Repair Loop

- prompt validation fails
- PMPack audit reports contradiction
- required report file missing
- CI check fails on predictable fixable issue
- model verification stale during active cycle

## Repair Loop Phases

1. **Detect**: capture exact failing signal and command output.
2. **Classify**: determine whether failure is content, state, workflow, or auth.
3. **Repair**: apply smallest correct change in allowed paths.
4. **Revalidate**: rerun the exact failing command plus prerequisite checks.
5. **Record**: append outcome to cycle report and incident log if needed.

## Example Commands

```powershell
python automation/ai_cycle_controller.py validate-prompts --cycle 075
python automation/ai_cycle_controller.py pm-pack-audit
.venv\Scripts\python.exe -m ruff check automation/ .github/ --output-format=full
```

## Guardrails

- No destructive cleanup shortcuts.
- No skip markers to bypass tests.
- No changing protected branch rules during repair.
- No silent retries; every retry requires new evidence.

## Completion Criteria

A repair loop iteration is complete only when:

- the previously failing check now passes,
- changes are documented in cycle report,
- no new blocker introduced.

If loop exceeds planned retries, escalate to manual review with full evidence package.

