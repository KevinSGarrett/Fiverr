# Model Policy Reference

This document is the authoritative model policy reference for autonomous cycle execution.

## Cursor Model Policy

- Model: Codex 5.3
- Effort: medium
- Auto model selection: DISABLED
- Fallback model: DISABLED
- Verification source: `C:\AI_Runner\state\cursor_model_state.json`
- Freshness window: 7 days from verification (`valid_until`)

Required status is `VERIFIED` before dispatch, planning finalization, or merge-gate dependent operations.

## Claude Policy

- Usage scope: PM review and governance review only
- Billing mode: subscription only
- API key policy: blocked for PM review workflow
- Drift handling: if wrong model used, mark result ADVISORYONLY and rerun

## Verification Commands

```powershell
powershell -File C:\AI_Runner\scripts\verify_model_selection.ps1
Get-Content C:\AI_Runner\state\cursor_model_state.json -Raw
Get-Content C:\AI_Runner\state\claude_model_state.json -Raw
```

## Drift and Expiry Rules

- If `valid_until` is expired, dispatch is blocked.
- If `observed_model` differs from policy, dispatch is blocked.
- If auto model selection is enabled unexpectedly, dispatch is blocked.
- If fallback becomes enabled, dispatch is blocked.

## Governance Integration

Model policy state must be referenced in cycle run summaries, incident reports, and post-cycle review outcomes. Any model-policy inconsistency is treated as a governance failure, not a minor warning.

## Required Evidence Fields

Cycle reports should include:

- `observed_model`
- `observed_effort`
- `auto_model_disabled`
- `fallback_disabled`
- `status`
- `valid_until`

This makes model compliance auditable by anyone reviewing cycle history.

## Non-Compliance Action

If any evidence field contradicts policy:

1. stop dispatch,
2. run verification script,
3. log incident,
4. rerun affected tasks under verified settings.

No exceptions are allowed for autonomous dispatch pathways.

