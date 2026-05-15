# Security Policy
# Fiverr Research System — Security Standards & Practices

---

## Security Principles

1. **No secrets in code** — All credentials live in environment variables or GitHub Secrets
2. **Least privilege** — Each component gets only the access it needs
3. **Scan everything** — Automated scanning on every PR
4. **Assume breach** — Design for what happens when (not if) a credential leaks
5. **Rotate regularly** — API keys rotated every 90 days minimum

---

## Threat Model

### What We Protect
| Asset | Sensitivity | Protection |
|---|---|---|
| OpenAI API key | High — billable | .env (never committed), GitHub Secrets |
| Database credentials | High | .env, never in config.yaml |
| Proxy credentials | Medium | .env |
| Fiverr session cookies | Medium | data/browser_profile/ (gitignored) |
| Scraped data | Low-Medium | Local only, not committed |
| Source code | Low (private repo) | GitHub access controls |

### Threat Vectors
| Vector | Mitigation |
|---|---|
| Secret committed to git | Pre-commit scan, CI secret scan, .gitignore |
| Dependency vulnerability | Dependabot, pip-audit |
| Leaked .env file | Never committed, .gitignore enforced |
| Compromised dependency | Pin versions, Dependabot alerts |
| Browser profile theft | Gitignored, local-only |
| API key in logs | Structured logging redacts sensitive fields |

---

## Security Scanning

### Layer 1: Pre-Commit (Local)
Agents should check before pushing:
```bash
# Quick scan for obvious secrets
grep -rn "sk-[a-zA-Z0-9]" src/ tests/
grep -rn "password\s*=" src/ tests/ | grep -v "test\|mock\|example"
grep -rn "OPENAI_API_KEY\s*=" src/ tests/ | grep -v "os.environ\|os.getenv\|\.env"
```

### Layer 2: CI Security Workflow (Every PR)
The `security.yml` GitHub Action checks:
1. **Secret patterns** — regex scan for API keys, passwords, tokens
2. **Dependency audit** — pip-audit against known vulnerability databases

### Layer 3: GitHub Native (Continuous)
| Feature | Status | What It Does |
|---|---|---|
| Secret scanning | Enabled | Detects committed secrets (OpenAI keys, AWS keys, etc.) |
| Push protection | Enabled | Blocks pushes containing detected secrets |
| Dependabot alerts | Enabled | Alerts on vulnerable dependencies |
| Dependabot security updates | Enabled | Auto-creates PRs for security patches |
| Code scanning (CodeQL) | Recommended | Static analysis for security bugs |

---

## Secret Patterns to Detect

| Pattern | Regex | What It Catches |
|---|---|---|
| OpenAI API key | `sk-[a-zA-Z0-9]{20,}` | OpenAI keys |
| Generic API key | `[aA][pP][iI]_?[kK][eE][yY].*=.*['\"][a-zA-Z0-9]{16,}` | Hardcoded API keys |
| Generic secret | `[sS][eE][cC][rR][eE][tT].*=.*['\"][a-zA-Z0-9]{16,}` | Hardcoded secrets |
| Generic password | `[pP][aA][sS][sS][wW][oO][rR][dD].*=.*['\"].+['\"]` | Hardcoded passwords |
| Private key header | `-----BEGIN (RSA\|DSA\|EC\|OPENSSH) PRIVATE KEY-----` | Private keys |
| Connection string | `(postgres\|mysql\|sqlite):\/\/.*:.*@` | DB connection with credentials |

---

## Incident Response

### If a Secret Is Committed

**Immediate actions (within 1 hour):**
1. **Revoke the credential** — Go to the provider (OpenAI dashboard, etc.) and invalidate it
2. **Generate a new credential** — Create replacement
3. **Update .env** — Replace locally
4. **Update GitHub Secrets** — If used in CI
5. **Do NOT just delete the commit** — The secret is already in git history

**Cleanup (within 24 hours):**
6. **Scrub git history** — Use BFG Repo-Cleaner or `git filter-repo`
7. **Force push** — After scrubbing (only time force push is acceptable)
8. **Notify** — Log the incident in CHANGELOG.md
9. **Post-mortem** — Document how it happened and how to prevent recurrence

### Response Timeline
| Severity | Response Time | Example |
|---|---|---|
| API key with billing | < 1 hour | OpenAI key committed |
| Database credentials | < 1 hour | Postgres password in code |
| Proxy credentials | < 4 hours | Proxy auth token |
| Non-sensitive config | < 24 hours | Debug flag, non-secret config |

---

## Dependency Security

### Dependabot Configuration
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 5
    labels:
      - "type:chore"
      - "scope:deps"
      - "priority:P3-medium"
      - "risk:low"
    ignore:
      # Don't auto-update major versions
      - dependency-name: "*"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    labels:
      - "type:chore"
      - "scope:ci-cd"
      - "priority:P4-low"
      - "risk:low"
```

### Dependency Update Policy
| Update Type | Action | Risk |
|---|---|---|
| Patch version (1.2.3 → 1.2.4) | Auto-merge if CI passes | Low |
| Minor version (1.2.0 → 1.3.0) | Review changelog, merge if safe | Medium |
| Major version (1.0.0 → 2.0.0) | Create investigation issue, test thoroughly | High |
| Security patch | Merge immediately regardless of version | Critical |
