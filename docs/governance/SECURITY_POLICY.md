# Repository Security Policy

## Scope

This policy applies to the Fiverr autonomous runner repository, including PM_Pack, workflows, runbooks, and controller-adjacent operational artifacts. The objective is to prevent credential leakage, unsafe automation actions, and unauthorized production-impacting behavior.

## Core Rules

1. Never commit secrets, credentials, tokens, private keys, or exported auth sessions.
2. Treat all ZIP and export artifacts as potential secret-carriers; scan before distribution.
3. Use least privilege for GitHub, Jira, and runner credentials.
4. Do not bypass model policy or merge gates.
5. Preserve auditability: every corrective action must be traceable in cycle reports.

## Secret Handling

- Store credentials outside versioned files.
- Use environment files excluded by `.gitignore`.
- Rotate tokens immediately if exposure is suspected.
- Replace path-based sanitization with value-pattern detection in export routines.

## Change Safety Controls

- No force push to protected branches.
- No direct merge to `main` by autonomous runner.
- Required CI checks and Codecov checks must pass before merge.
- PMPack contradiction blocks dispatch and merge readiness.

## Incident Requirements

Security-relevant events require incident files under `C:\AI_Runner\reports\incidents\` with timestamp, scope, affected assets, and remediation actions. Incidents include leaked credentials, unauthorized model drift, unsafe command attempts, and corrupted state.

## Enforcement

Violations suspend autonomous dispatch until corrected and documented. Repeated violations require explicit operator review before resuming automation.

