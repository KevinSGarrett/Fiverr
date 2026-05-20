# Repository Settings Reference
# Fiverr Research System — Exact GitHub Configuration

---

## 1. General Repository Settings (Settings → General)

### Repository Name and Description
- **Name:** `fiverr-research-system`
- **Description:** `Automated Fiverr niche research, analysis, scoring, and recommendation engine — built with Python, Playwright, SQLAlchemy, OpenAI, and Streamlit`
- **Website:** Leave blank
- **Topics:** `python`, `fiverr`, `automation`, `web-scraping`, `ai`, `openai`, `streamlit`, `sqlalchemy`

### Features
| Feature | Enabled | Notes |
|---|---|---|
| Wikis | ❌ | Docs live in repo |
| Issues | ✅ | Task tracking |
| Sponsorships | ❌ | Private project |
| Preserve this repository | ❌ | Not needed |
| Discussions | ❌ | Not needed for AI workflow |
| Projects | ✅ | Kanban board for sprint management |

### Pull Requests
| Setting | Value |
|---|---|
| Allow merge commits | ❌ Disabled |
| Allow squash merging | ✅ **Enabled (Primary)** |
| Default to PR title for squash commit | ✅ Enabled |
| Allow rebase merging | ❌ Disabled |
| Always suggest updating PR branches | ✅ Enabled |
| Allow auto-merge | ✅ Enabled |
| Automatically delete head branches | ✅ Enabled |

### Danger Zone
- **Visibility:** Private
- **Transfer/Archive/Delete:** Do not touch

---

## 2. Branch Settings (Settings → Branches)

### Default Branch
- **Default branch:** `main`
- **Rename branch:** N/A (set at creation)

### Branch Protection Rules

**Rule 1: `main` (production)**
| Protection | Value |
|---|---|
| Require a pull request before merging | ✅ |
| Required approvals | 0 (single developer — self-merge after checks) |
| Dismiss stale PR approvals | ✅ |
| Require review from Code Owners | ❌ (single developer) |
| Require status checks to pass | ✅ |
| Required checks | `ci / lint`, `ci / type-check`, `ci / test`, `pr-checks / validate-pr` |
| Require branches to be up to date | ✅ |
| Require conversation resolution | ✅ |
| Require signed commits | ❌ (optional — enable if desired) |
| Require linear history | ✅ |
| Include administrators | ✅ (even admin must follow rules) |
| Restrict who can push | Only merge via PR |
| Allow force pushes | ❌ Never |
| Allow deletions | ❌ Never |

**Rule 2: `develop` (integration)**
| Protection | Value |
|---|---|
| Require a pull request before merging | ✅ |
| Required approvals | 0 |
| Require status checks to pass | ✅ |
| Required checks | `ci / lint`, `ci / type-check`, `ci / test` |
| Require branches to be up to date | ❌ (agents merge frequently — avoid rebase churn) |
| Require conversation resolution | ✅ |
| Require linear history | ❌ (squash handles this) |
| Include administrators | ✅ |
| Allow force pushes | ❌ Never |
| Allow deletions | ❌ Never |

---

## 3. Actions Settings (Settings → Actions → General)

| Setting | Value |
|---|---|
| Actions permissions | Allow all actions and reusable workflows |
| Workflow permissions | Read and write permissions |
| Allow GitHub Actions to create and approve pull requests | ✅ |

---

## 4. Pages Settings
- **Disabled** — no GitHub Pages needed

---

## 5. Environments (Settings → Environments)

### Environment: `production`
| Setting | Value |
|---|---|
| Required reviewers | None (single developer) |
| Wait timer | 0 |
| Deployment branches | `main` only |

---

## 6. Secrets and Variables (Settings → Secrets and variables → Actions)

### Repository Secrets
| Secret Name | Purpose | Required |
|---|---|---|
| `OPENAI_API_KEY` | LLM API access for CI tests (if integration tests run) | Optional |
| `CODECOV_TOKEN` | Coverage reporting (if using Codecov) | Optional |

### Repository Variables
| Variable Name | Value | Purpose |
|---|---|---|
| `PYTHON_VERSION` | `3.11` | CI matrix version |
| `MIN_COVERAGE` | `80` | Minimum test coverage threshold |

---

## 7. Webhooks
- None required for v1. Future: Slack/Discord notifications.

---

## 8. Deploy Keys
- None required. All agents use the owner's SSH key.

---

## 9. GitHub Apps / Integrations

### Recommended
| App | Purpose | Priority |
|---|---|---|
| Dependabot | Automated dependency updates | Install immediately |
| CodeQL | Security vulnerability scanning | Install immediately |

### Optional (Nice to Have)
| App | Purpose |
|---|---|
| Codecov | Coverage visualization |
| Renovate | Alternative to Dependabot |
| Stale | Auto-close stale issues/PRs |
