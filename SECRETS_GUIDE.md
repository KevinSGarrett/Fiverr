# Secrets Guide

## Source of Truth
- Master env file: `C:\Fiverr\Fiverr\.env`
- Runner env file: `C:\AI_Runner\secrets\runner.env`
- GitHub Actions secrets must match the master `.env`.

## Canonical Keys
| Purpose | Key |
|---|---|
| OpenAI API | `OPENAI_API_KEY` |
| Scrapfly API | `SCRAPFLY_API_KEY` |
| Jira API token | `JIRA_API_TOKEN` |
| Jira email | `JIRA_EMAIL` |
| Jira base URL | `JIRA_BASE_URL` |
| GitHub automation token | `GH_AUTOMATION_TOKEN` |
| Codecov token | `CODECOV_TOKEN` |

## Key Name Rules
- Jira token key must be exactly `JIRA_API_TOKEN`.
- Invalid Jira token names include `JIRA_API`, `JIRA_TOKEN`, and `JIRA_KEY`.
- `ANTHROPIC_API_KEY` must be absent in this project configuration.

## Loader Resolution Order
Use `automation.config_loader.get_secret()`:
1. `C:\AI_Runner\secrets\runner.env`
2. `os.environ`
3. `C:\Fiverr\Fiverr\.env`

## Safety Rules
- Never print full token values.
- Never commit tokens to repository files.
- Never copy values from runner env files back into `.env`.
