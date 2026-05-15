# CODEOWNERS Design
# Fiverr Research System — Code Ownership & Review Routing

---

## Purpose

The CODEOWNERS file tells GitHub who is responsible for which parts of the codebase. In this project, since all 4 Cursor agents operate through a single GitHub account, CODEOWNERS serves primarily as **documentation** of ownership boundaries and as the basis for review routing if additional human reviewers are added later.

---

## Ownership Model

### Agent-to-Directory Mapping

| Agent | Role | Primary Ownership |
|---|---|---|
| Agent 1 | Infrastructure | src/config/, src/models/, src/utils/, src/scripts/, .github/, config.yaml, pyproject.toml |
| Agent 2 | Collection | src/collection/ |
| Agent 3 | Analysis/Scoring | src/analysis/, src/scoring/, src/llm/, src/pricing/, src/discovery/ |
| Agent 4 | Dashboard/UX | src/playbook/, src/dashboard/, src/reports/, src/exports/ |
| All | Shared | tests/, docs/, README.md, CHANGELOG.md |
| Human | Final Authority | Everything (admin override) |

---

## CODEOWNERS File

The file lives at `.github/CODEOWNERS` in the repo:

```
# CODEOWNERS — Fiverr Research System
# Since all agents use the same GitHub account, this file serves
# as documentation of ownership boundaries. If additional reviewers
# are added, uncomment the @username lines.

# Default: human operator owns everything
*                                   @owner-username

# === Agent 1: Infrastructure ===
/src/config/                        @owner-username
/src/models/                        @owner-username
/src/utils/                         @owner-username
/src/scripts/                       @owner-username
/src/orchestrator.py                @owner-username
/.github/                           @owner-username
/pyproject.toml                     @owner-username
/config.yaml                        @owner-username
/requirements.txt                   @owner-username

# === Agent 2: Collection ===
/src/collection/                    @owner-username

# === Agent 3: Analysis & Scoring ===
/src/analysis/                      @owner-username
/src/scoring/                       @owner-username
/src/llm/                           @owner-username
/src/pricing/                       @owner-username
/src/discovery/                     @owner-username

# === Agent 4: Dashboard & UX ===
/src/playbook/                      @owner-username
/src/dashboard/                     @owner-username
/src/reports/                       @owner-username
/src/exports/                       @owner-username

# === Shared (All Agents) ===
/tests/                             @owner-username
/docs/                              @owner-username

# === Critical Files (Human Review Recommended) ===
# These files have outsized impact — changes should be reviewed carefully
/src/models/base.py                 @owner-username
/src/models/database.py             @owner-username
/src/orchestrator.py                @owner-username
/.github/workflows/                 @owner-username
/pyproject.toml                     @owner-username
```

---

## Cross-Boundary Changes

When a PR touches files owned by multiple agents:

| Scenario | Example | Required Action |
|---|---|---|
| Agent touches own files only | Agent 3 edits src/scoring/demand.py | Normal PR flow |
| Agent touches shared files | Agent 2 edits tests/conftest.py | Normal PR flow |
| Agent touches another agent's files | Agent 3 edits src/models/keyword.py | Add both scope labels, risk:medium minimum |
| Agent touches critical files | Any agent edits src/orchestrator.py | risk:critical, human review required |

### How to Handle Cross-Boundary PRs
1. Add all relevant `scope:*` labels
2. Raise the risk level to at least `risk:medium`
3. In the PR description, explain WHY the cross-boundary change is needed
4. If touching critical files, wait for human review

---

## Future: Multi-Reviewer Setup

If the project grows to include human reviewers beyond the single operator:

1. Replace `@owner-username` with specific team handles
2. Enable "Require review from Code Owners" in branch protection
3. Set up GitHub Teams for each agent role
4. Each team gets auto-assigned to PRs touching their owned paths

Example future CODEOWNERS:
```
/src/config/          @infra-team
/src/collection/      @collection-team
/src/scoring/         @analysis-team
/src/dashboard/       @dashboard-team
```

---

## CODEOWNERS Enforcement

| Setting | Current Value | Future Value |
|---|---|---|
| Require review from Code Owners | ❌ Disabled | ✅ Enable when multi-reviewer |
| Auto-assign reviewers | ❌ N/A | ✅ Based on CODEOWNERS |
| Branch protection integration | Passive (documentation) | Active (required reviews) |
