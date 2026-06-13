# BUG_011_BRANCH_PROTECTION_DIAGNOSIS

## API checks executed

1. Without token:
   - `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection -i`
   - Result: `HTTP/2.0 401 Unauthorized`, body `"message": "Bad credentials"`.

2. With `GH_AUTOMATION_TOKEN` from runner env:
   - `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection -i`
   - Result: `HTTP/2.0 200 OK` with full branch protection payload.

## OAuth scope evidence

- Response header `X-Oauth-Scopes` includes broad admin-capable scopes:
  - `repo`, `admin:repo_hook`, `admin:org`, `workflow`, and others.
- `X-Accepted-Oauth-Scopes` was empty for this endpoint response.

## Diagnosis

- The failure mode is **credential quality**, not endpoint capability.
- Invalid/expired/missing token yields 401.
- Valid token with repo admin capability succeeds immediately.

## Remediation

1. Ensure runtime uses `GH_AUTOMATION_TOKEN` from `C:/AI_Runner/secrets/runner.env`.
2. Verify token is current and includes at least `repo` scope (and admin-repo access for protection mutations).
3. Export `GH_TOKEN` before `gh api`/`gh pr` operations in automation jobs.
4. Add a preflight check:
   - `gh auth status` and a read probe to `/branches/develop/protection`.

## Current status

- **BUG-011 currently reproducible only with bad credentials.**
- With configured automation token, branch protection endpoint is accessible and returns 200.
