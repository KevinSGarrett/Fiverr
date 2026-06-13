# Claude Subscription Auth Recovery

## Symptoms

- PM review adapter cannot run subscription-backed review.
- Claude model state is stale, missing, or marked not verified.
- Post-cycle review cannot proceed due to billing/auth mismatch.

## Recovery Steps

1. Confirm current state:

```powershell
Get-Content C:\AI_Runner\state\claude_model_state.json -Raw
```

2. Run subscription preflight from controller toolchain.
3. Confirm billing mode is subscription-only (no API key fallback).
4. Re-run post-cycle verification entrypoint.

## Policy Requirements

- Claude is advisory/governance PM review path.
- If wrong model/auth state was used, results are ADVISORYONLY and must be rerun.
- API billing must remain disabled for this workflow.

## Validation

- Preflight reports pass
- model state shows verified and fresh
- post-cycle review command executes without auth errors

## Security Rules

- Never store Claude auth tokens in repository files.
- Never commit browser/session artifacts.
- Rotate related credentials if suspicious access occurs.

## Incident Handling

If expiry delayed cycle closure, record incident with affected cycle, duration, and whether reports needed rerun.

## Recovery Completion Checklist

- [ ] subscription preflight passes
- [ ] model state file refreshed
- [ ] no API key billing path active
- [ ] post-cycle command re-executed successfully
- [ ] impacted review artifacts rerun where required

## Escalation Trigger

Escalate when:

- repeated auth expiry happens within the same cycle,
- subscription access is unavailable for extended periods,
- governance closure is blocked beyond planned cycle window.

Escalation record must include business impact and recommended temporary operating mode.

