# Secrets Management
# Fiverr Research System — Handling Credentials and Environment Variables

---

## Environment Variable Architecture

### .env File (Local Development)
The `.env` file lives at the repo root and is NEVER committed. It contains all runtime secrets.

```bash
# .env — DO NOT COMMIT THIS FILE
# Copy from .env.example and fill in your values

# === Required ===
OPENAI_API_KEY=sk-your-key-here

# === Database ===
# SQLite (default for development)
DATABASE_URL=sqlite:///data/fiverr_research.db
# PostgreSQL (production)
# DATABASE_URL=postgresql://user:password@localhost:5432/fiverr_research

# === LLM Settings ===
OPENAI_MODEL=gpt-4o
OPENAI_MINI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=60

# === Proxy (Optional) ===
# PROXY_URL=http://user:pass@proxy.example.com:8080
# PROXY_ROTATION=true

# === Collection ===
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SLOW_MO=0

# === Logging ===
LOG_LEVEL=INFO
LOG_FORMAT=json

# === Dashboard ===
STREAMLIT_PORT=8501
```

### .env.example (Committed — Template)
```bash
# .env.example — Copy to .env and fill in values
# NEVER put actual credentials in this file

OPENAI_API_KEY=sk-your-key-here
DATABASE_URL=sqlite:///data/fiverr_research.db
OPENAI_MODEL=gpt-4o
OPENAI_MINI_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_MAX_RETRIES=3
OPENAI_TIMEOUT=60
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_SLOW_MO=0
LOG_LEVEL=INFO
LOG_FORMAT=json
STREAMLIT_PORT=8501
```

---

## GitHub Secrets (CI/CD)

### Repository Secrets (Settings → Secrets → Actions)

| Secret Name | Purpose | Required for CI? | How to Set |
|---|---|---|---|
| `OPENAI_API_KEY` | LLM calls in integration tests | Only if running LLM integration tests | Settings → Secrets → New repository secret |
| `CODECOV_TOKEN` | Coverage reporting | Only if using Codecov | Settings → Secrets → New repository secret |

### Repository Variables (Settings → Variables → Actions)

| Variable | Value | Purpose |
|---|---|---|
| `PYTHON_VERSION` | `3.11` | CI Python version |
| `MIN_COVERAGE` | `80` | Coverage threshold |

### Accessing Secrets in Workflows
```yaml
# In GitHub Actions:
env:
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

# For optional secrets (CI shouldn't fail if not set):
- name: Run integration tests
  if: ${{ secrets.OPENAI_API_KEY != '' }}
  run: pytest tests/integration/ -v
  env:
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

---

## Secret Loading in Code

### Pattern: Always Use Environment Variables
```python
# CORRECT — Load from environment
import os
api_key = os.environ["OPENAI_API_KEY"]  # Raises KeyError if missing

# CORRECT — Load with default
api_key = os.getenv("OPENAI_API_KEY")  # Returns None if missing

# WRONG — Never hardcode
api_key = "sk-abc123..."  # NEVER DO THIS

# WRONG — Never put in config.yaml
# openai_api_key: sk-abc123...  # NEVER DO THIS
```

### Pattern: Config Loader Validates Secrets on Startup
```python
# src/config/loader.py should validate all required secrets exist at startup
class ConfigLoader:
    def validate_secrets(self) -> None:
        required = ["OPENAI_API_KEY"]
        missing = [k for k in required if not os.getenv(k)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables: {', '.join(missing)}. "
                f"Copy .env.example to .env and fill in values."
            )
```

### Pattern: Structured Logger Redacts Secrets
```python
# src/utils/logging.py should redact any secret-like values
REDACT_PATTERNS = [
    r"sk-[a-zA-Z0-9]+",       # OpenAI keys
    r"password=\S+",           # Passwords
    r"token=\S+",              # Tokens
]

def redact(message: str) -> str:
    for pattern in REDACT_PATTERNS:
        message = re.sub(pattern, "***REDACTED***", message)
    return message
```

---

## Secret Rotation Schedule

| Secret | Rotation Period | How to Rotate |
|---|---|---|
| OpenAI API key | Every 90 days | Generate new key in OpenAI dashboard → update .env → update GitHub Secret |
| Database password | Every 90 days (production) | Change in database → update .env |
| Proxy credentials | Per provider policy | Update with provider → update .env |

### Rotation Checklist
1. Generate new credential at the provider
2. Update local `.env` file
3. Update GitHub Secret (if used in CI)
4. Verify CI still passes
5. Revoke the old credential
6. Log rotation in CHANGELOG.md

---

## Files That Must Be Gitignored

```gitignore
# Secrets
.env
.env.local
.env.production

# Database
*.db
*.sqlite3

# Browser profile (contains cookies/sessions)
data/browser_profile/

# Exports (may contain sensitive analysis)
data/exports/

# Screenshots
data/screenshots/

# Backups
data/backups/

# OS files
.DS_Store
Thumbs.db
```

---

## Security Audit Checklist

### Before Every PR
- [ ] No hardcoded secrets in any file
- [ ] All new environment variables added to .env.example (without values)
- [ ] No secrets logged (even at DEBUG level)
- [ ] No secrets in error messages
- [ ] No secrets in test fixtures (use mock values)

### Monthly Audit
- [ ] All secrets rotated within last 90 days
- [ ] GitHub Secret scanning alerts: 0
- [ ] Dependabot security alerts: 0 critical/high
- [ ] No .env file accidentally committed (check git history)
- [ ] .gitignore still covers all sensitive paths
