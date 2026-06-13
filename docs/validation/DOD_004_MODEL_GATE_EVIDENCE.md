# DOD-004 Model Gate Evidence (Cycle 077)

Command: `python automation/ai_cycle_controller.py run-agent --cycle 077 --agent A --dry-run`

## Captured output

```text
[1/5] MODEL_GATE check...
MODEL_GATE PASS
  Model    : Codex 5.3
  Effort   : medium
  Auto off : True
  Age      : 1.9 days
```

## cursor_model_state.json

```text
verified_at: 2026-06-11T03:00:00Z
observed_model: Codex 5.3
observed_effort: medium
status: VERIFIED
valid_until: 2026-06-18T03:00:00Z
```

## claude_model_state.json

```text
verified_at: 2026-06-11T00:00:00Z
billing_mode: claude_subscription_only
status: SUBSCRIPTION_VERIFIED
auth_status: AUTHENTICATED
```

## Expiry check

- Cursor model verification window remains valid until `2026-06-18T03:00:00Z`.
- Dry-run model gate age output (`1.9 days`) is consistent with non-expired state.

Model gate status: PASS.
