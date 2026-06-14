# SECRETS AND ENV REFERENCE

`C:\Fiverr\Fiverr\.env` is the master source of truth.
Sync all other locations from this file.

## Canonical Locations
- Master env: `C:\Fiverr\Fiverr\.env`
- Runner secrets: `C:\AI_Runner\secrets\runner.env`
- GitHub Actions secrets: repository secret store

## Required Key Inventory
| Key | Master `.env` | `runner.env` | GitHub Actions | Purpose |
|---|---|---|---|---|
| `OPENAI_API_KEY` | required | optional | required | OpenAI scoring and embeddings |
| `SCRAPFLY_API_KEY` | required | optional | required | Collection transport |
| `JIRA_API_TOKEN` | required | required | required | Jira API auth |
| `JIRA_EMAIL` | required | required | required | Jira account |
| `JIRA_BASE_URL` | required | required | required | Jira tenant URL |
| `GH_AUTOMATION_TOKEN` | required | required | required (`GHAUTOMATIONTOKEN`) | GitHub automation |
| `CODECOV_TOKEN` | optional placeholder | optional placeholder | placeholder | Codecov upload |

## Strict Rules
- `JIRA_API_TOKEN` must use this exact key name.
- `ANTHROPIC_API_KEY` must be absent from `.env`, `runner.env`, and GitHub Actions.
- Never copy secrets from runner sources back into `.env`.
- Never print secret values in logs or reports.

## Loader Resolution Order
`automation.config_loader.get_secret()` resolves in this order:
1. `C:\AI_Runner\secrets\runner.env`
2. `os.environ`
3. `C:\Fiverr\Fiverr\.env`
