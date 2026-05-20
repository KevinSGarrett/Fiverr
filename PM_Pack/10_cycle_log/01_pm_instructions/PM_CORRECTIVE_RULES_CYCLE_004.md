# PM CORRECTIVE RULES — CYCLE 004

1. Every PM reply must include an updated PM Pack zip. No exceptions.
2. Every continue-cycle reply must include four detailed Cursor prompts unless the user explicitly asks only for review.
3. Jira remains PM-owned; if Jira returns 502 or other transient errors, record the intended action queue and retry in a later pass.
4. GitHub live verification must be assigned to Cursor steward agents when ChatGPT cannot fetch GitHub.
5. No direct push or PR to main is allowed. Cycle branches target develop. Main is release-only.
6. Uploaded repo archives may contain line-ending conversion noise; verify with `git diff --ignore-space-at-eol` before treating dirty tree as substantive.
