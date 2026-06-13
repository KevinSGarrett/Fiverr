# MODEL DRIFT EVIDENCE — CYCLE 075

- Captured at (UTC): 2026-06-12T00:47:58.069091+00:00
- Cursor model state: VERIFIED

## Cursor Model State

```text
Model: Codex 5.3
Status: VERIFIED
Valid until: 2026-06-18T03:00:00Z
Days remaining: 6
Auto disabled: unknown
Last verified at: unknown
DRIFT_DETECTED: False
Exit code: 0
```

## Claude Model State

```json
{
  "verified_at": "2026-06-11T00:00:00Z",
  "machine": "FIVERR-AI-RUNNER",
  "billing_mode": "claude_subscription_only",
  "account_source": "same Claude.ai / Claude Desktop subscription account",
  "subscription_login_verified": true,
  "anthropic_api_key_present": false,
  "api_credit_fallback_allowed": false,
  "console_payg_allowed": false,
  "plan": "Claude Team (Scentiment)",
  "requested_model": "Claude Sonnet 4.6",
  "observed_default_model": "Opus 4.8",
  "model_note": "Claude Code defaults to Opus 4.8. Controller must invoke with --model claude-sonnet-4-6 for official PM review.",
  "requested_effort": "medium",
  "observed_effort": "UNVERIFIED",
  "adaptive_thinking_required": true,
  "adaptive_thinking_enabled": false,
  "verification_method": "cli_test_run",
  "status": "SUBSCRIPTION_VERIFIED",
  "claude_code_version": "2.1.172 (Claude Code)",
  "claude_code_binary": "C:\\Users\\Windows 11\\.local\\bin\\claude.EXE",
  "auth_status": "AUTHENTICATED",
  "last_verified_at": "2026-06-11T14:14:01.918437+00:00"
}
Exit code: 0
```

## Incident Procedure

No drift incident trigger required.
