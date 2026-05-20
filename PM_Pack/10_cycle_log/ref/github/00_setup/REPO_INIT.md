# Repository Initialization Guide
# Fiverr Research System — GitHub Setup

---

## 1. Repository Creation

### Create the Repository
```
Repository name: fiverr-research-system
Description: Automated Fiverr niche research, analysis, scoring, and recommendation engine
Visibility: Private
Initialize with: README.md checked
Default branch: main
License: None (private project)
.gitignore template: Python
```

### Immediately After Creation
```bash
# Clone locally
git clone git@github.com:<your-username>/fiverr-research-system.git
cd fiverr-research-system

# Set up the develop branch
git checkout -b develop
git push -u origin develop

# Set develop as the default working branch for all agents
# (main is production-only, develop is the integration branch)
```

---

## 2. GitHub Repository Settings

### General Settings
| Setting | Value | Reason |
|---|---|---|
| Default branch | `main` | Production branch — only receives merged, tested code |
| Wikis | Disabled | Documentation lives in repo as Markdown |
| Issues | Enabled | Task tracking for all epics/stories/tasks |
| Sponsorships | Disabled | Private project |
| Projects | Enabled | Kanban board for sprint tracking |
| Discussions | Disabled | Not needed for AI-driven development |
| Allow merge commits | Disabled | Keep history clean |
| Allow squash merging | **Enabled (default)** | All PRs squash-merge to keep history readable |
| Allow rebase merging | Disabled | Prevents messy history |
| Always suggest updating PR branches | Enabled | Keep PRs up to date with target |
| Allow auto-merge | Enabled | AI agents can auto-merge after checks pass |
| Automatically delete head branches | **Enabled** | Clean up feature branches after merge |

### Pull Request Settings
| Setting | Value |
|---|---|
| Require a pull request before merging | Yes (for main and develop) |
| Dismiss stale pull request approvals when new commits are pushed | Yes |
| Require conversation resolution before merging | Yes |

---

## 3. GitHub Features to Enable

### GitHub Actions
- **Status:** Enabled
- **Allowed actions:** All actions (we'll define specific workflows)
- **Workflow permissions:** Read and write permissions
- **Allow GitHub Actions to create and approve pull requests:** Yes (for automation)

### Dependabot
- **Security updates:** Enabled
- **Version updates:** Enabled (weekly, Python ecosystem)

### Branch Protection Rules
Set up in Wave GH-2 (BRANCH_PROTECTION.md) — both `main` and `develop` get protection rules.

---

## 4. Repository Collaborators

Since this is built by AI agents, the repo has a single human owner:

| Role | Account | Permissions |
|---|---|---|
| Owner / Human Operator | Your GitHub account | Admin |
| ChatGPT PM | N/A (operates via human) | Issues, project board management |
| Cursor Agent 1-4 | Same account (local git) | Push to feature branches only |

All Cursor agents operate through the same local git installation on the same machine. Concurrency is managed through branch isolation, not separate GitHub accounts.

---

## 5. Initial Commit Structure

After repo creation, the first commit should establish the skeleton:

```bash
# Create the initial directory structure (see DIRECTORY_STRUCTURE.md)
mkdir -p src/{config,models,collection,analysis,scoring,llm,pricing,discovery,playbook,dashboard,reports,exports,utils,scripts}
mkdir -p src/collection/workflows
mkdir -p src/llm/prompts
mkdir -p src/dashboard/pages
mkdir -p tests/{unit,integration,performance,fixtures}
mkdir -p data/{seeds,exports,screenshots,checkpoints,backups,browser_profile}
mkdir -p docs

# Create placeholder __init__.py files
find src -type d -exec touch {}/__init__.py \;

# Create essential files
touch .env.example
touch config.yaml
touch run.py
touch pyproject.toml
touch requirements.txt

# Initial commit
git add .
git commit -m "chore: initialize project skeleton with directory structure"
git push origin develop
```

---

## 6. Git Configuration for AI Agents

All agents use the same local git config:

```bash
# Set consistent git config
git config user.name "Fiverr Research System"
git config user.email "dev@fiverr-research.local"

# Set default merge strategy
git config pull.rebase true

# Set default push behavior
git config push.default current

# Enable long paths (Windows)
git config core.longpaths true

# Set line ending handling (Windows)
git config core.autocrlf true
```
