# SECRETS AND API KEY GUIDE FOR CURSOR AGENTS
# =============================================
# This file documents exactly how to find and use every secret/token in this project.
# NEVER hardcode or print actual token values. Check presence/length only.

## HOW TO GET A SECRET IN PYTHON CODE

```python
# ALWAYS use this — it checks runner.env, os.environ, and .env in priority order
from automation.config_loader import get_secret

openai_key = get_secret("OPENAI_API_KEY")
jira_token = get_secret("JIRA_API_TOKEN")
jira_email = get_secret("JIRA_EMAIL")
jira_base_url = get_secret("JIRA_BASE_URL")
gh_token = get_secret("GH_AUTOMATION_TOKEN")
scrapfly_key = get_secret("SCRAPFLY_API_KEY")
codecov_token = get_secret("CODECOV_TOKEN")
```

## SECRET LOCATIONS

### C:/AI_Runner/secrets/runner.env (PRIMARY — automation runner secrets)
Format: KEY=VALUE
Keys: GH_AUTOMATION_TOKEN, JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, CODECOV_TOKEN

### C:/Fiverr/Fiverr/.env (SECONDARY — project dev secrets, gitignored)
Format: KEY=VALUE (standardized June 2026)
Keys: OPENAI_API_KEY, DATABASE_URL, SCRAPFLY_API_KEY, JIRA_API_TOKEN, JIRA_EMAIL,
      JIRA_BASE_URL, GH_AUTOMATION_TOKEN, REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET

### GitHub Actions Secrets (CI/CD only — not accessible locally)
Keys: GH_AUTOMATION_TOKEN, JIRA_API_TOKEN, JIRA_EMAIL, JIRA_BASE_URL, CODECOV_TOKEN

## KEY NAME REFERENCE TABLE

| Purpose               | Key Name              | Source              |
|-----------------------|-----------------------|---------------------|
| OpenAI API            | OPENAI_API_KEY        | .env                |
| Jira API Token        | JIRA_API_TOKEN        | runner.env + .env   |
| Jira Email            | JIRA_EMAIL            | runner.env + .env   |
| Jira Base URL         | JIRA_BASE_URL         | runner.env + .env   |
| GitHub Token          | GH_AUTOMATION_TOKEN   | runner.env + .env   |
| ScrapFly API          | SCRAPFLY_API_KEY      | .env                |
| Codecov Token         | CODECOV_TOKEN         | runner.env          |

## JIRA API USAGE

```python
from automation.config_loader import get_secret
import requests

JIRA_BASE = get_secret("JIRA_BASE_URL")   # https://kevinsgarrett.atlassian.net
JIRA_EMAIL = get_secret("JIRA_EMAIL")     # kevinsgarrett@gmail.com  
JIRA_TOKEN = get_secret("JIRA_API_TOKEN") # ATATT3x...

headers = {"Authorization": f"Bearer {JIRA_TOKEN}"}
# OR for basic auth:
auth = (JIRA_EMAIL, JIRA_TOKEN)
response = requests.get(f"{JIRA_BASE}/rest/api/3/issue/SCRUM-1", auth=auth)
```

## NEVER-DO RULES
- NEVER print or log a full token value
- NEVER hardcode any token in source code or prompts
- NEVER put tokens in commit messages
- NEVER check presence of ANTHROPIC_API_KEY — this system uses Claude subscription only
- If you find a token embedded in code: tell the user to rotate it immediately
