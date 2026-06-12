# GitHub Auth Expiry Recovery

## Symptoms

- `gh` commands return HTTP 401 or "Bad credentials".
- Branch protection and PR metadata queries fail.
- CI/merge governance checks cannot retrieve status from GitHub API.

## Recovery Steps

1. Confirm failure:

```powershell
gh auth status
gh api /user
```

2. Re-authenticate:

```powershell
gh auth login
```

3. Validate token scope:

```powershell
gh auth status -t
```

4. Re-run blocked command, for example:

```powershell
gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection
```

## Scope Expectations

Token should allow repo read/write operations required by runner governance tasks. If scope is insufficient, refresh credential with proper scopes rather than bypassing checks.

## Post-Recovery Validation

- branch protection query succeeds
- PR checks query succeeds
- merge gate can read required statuses

## Incident Logging

If expiry disrupted active cycle work, write an incident report under `C:\AI_Runner\reports\incidents\` with failure window, impacted tasks, and recovery timestamp.

## Troubleshooting Notes

- If `gh auth status` succeeds but API calls still fail, verify the token host context is `github.com`.
- If CI checks cannot be read, ensure token has `repo` and checks read scopes.
- If running inside service context, confirm environment variables are loaded for that session.

## Recovery Validation Matrix

| Validation | Command | Pass Criteria |
|---|---|---|
| Identity | `gh api /user` | user JSON returned |
| Repo access | `gh repo view KevinSGarrett/Fiverr` | repository metadata returned |
| Branch protection read | `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection` | protection JSON returned |
| PR read | `gh pr list --repo KevinSGarrett/Fiverr` | PR list returned |

Do not continue cycle governance tasks until this matrix is green.

