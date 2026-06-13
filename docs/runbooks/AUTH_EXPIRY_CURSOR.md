# Cursor Session Expiry Recovery

## Symptoms

- Cursor CLI actions fail due to auth/session expiration.
- Model verification scripts cannot validate non-interactive command.
- Agent dispatch halts even when runner appears online.

## Recovery Procedure

1. Confirm session/auth problem via model verification script:

```powershell
powershell -File C:\AI_Runner\scripts\verify_model_selection.ps1
```

2. Re-authenticate Cursor in desktop UI if required.
3. Confirm model policy values in picker:
   - Codex 5.3
   - medium effort
   - auto disabled
   - fallback disabled
4. Re-run verification script.

## Validate State File

Check:

`C:\AI_Runner\state\cursor_model_state.json`

Required fields:

- `status = VERIFIED`
- `observed_model = Codex 5.3`
- `valid_until` in future

## Resume Decision

- If expiry happened before dispatch: continue after verification.
- If expiry happened during active task: rerun affected task under verified state.

## Incident Logging

Write incident if cycle tasks were blocked or if session repeatedly expires within short windows. Include timestamps, observed errors, and recovery duration.

## Recurrence Controls

When expiry repeats, add:

1. pre-dispatch model verification command in execution checklist,
2. mid-cycle freshness check before major stage transitions,
3. post-recovery smoke command to prove non-interactive Cursor operation.

Suggested smoke command:

```powershell
& "C:\Users\Windows 11\AppData\Local\cursor-agent\agent.cmd" -p "print HELLO" --output-format text --trust
```

The recovery is complete only when state is VERIFIED and smoke output confirms operational command path.

