# BRANCH WORKFLOW PER CYCLE
# Updated: Cycle 019 (DL-031)

---

## Branch Naming Rules (DL-031)

| Branch Type | Pattern | Example |
|---|---|---|
| Cycle integration | `cycle/{NNN}/integration` | `cycle/020/integration` |
| Story feature | `feature/epic{NN}/SCRUM-{key}-{slug}` | `feature/epic01/SCRUM-136-db-init` |
| Bug fix | `fix/SCRUM-{key}-{slug}` | `fix/SCRUM-200-config-crash` |

Always include the Jira key in story/fix branch names. This triggers the Jira-GitHub auto-link.

---

## Cycle Workflow

### Step 1 — Create Integration Branch

The human operator creates the branch (Cursor agents do not push independently):

```bash
cd C:\Fiverr\Fiverr
git checkout develop
git pull origin develop
git checkout -b cycle/{NNN}/integration
```

### Step 2 — Agents Work Sequentially

Agent A → commit → Agent B → commit → Agent C → commit → Agent D → commit

Each commit follows conventional commits format (DL-032):
```
{type}({scope}): {description} [Agent {N}]

Examples:
feat(cycle-020): add Playwright session manager [Agent B]
fix(models): SCRUM-136 add missing FK index [Agent A]
```

On integration branches: use `cycle-{NNN}` as scope.
On story branches: use the module name as scope (models, collection, scoring, etc.).

### Step 3 — Push

```bash
git push -u origin cycle/{NNN}/integration
```

### Step 4 — Create PR

Title must be ≤72 chars, follow conventional commits, ASCII only:
```
feat(cycle-020): E02 collection engine core pipeline [Claude AI]
```

Labels to add before CI runs:
- `type:feature` (or appropriate type)
- `priority:P3-medium` (or appropriate priority)
- `scope:epic02` (scope of primary work)
- `agent:2-collection` (primary agent)
- `risk:*` if applicable
- `override:large-pr` if diff exceeds 1000 lines

### Step 5 — CI Runs

All 5 workflows trigger automatically:
- `ci.yml` — lint, type-check, tests, codecov
- `pr-checks.yml` — title validation + size check
- `security.yml` — secret scan + dependency audit
- `stale.yml` — no action on new PRs
- `release.yml` — no action (only triggers on main)

### Step 6 — Review and Merge

PM verifies:
1. All CI checks green
2. Codecov project ≥90% and patch ≥90%
3. PR body lists all tasks
4. No unresolved PR conversations
5. Jira tickets updated

Then: **squash merge only** → branch auto-deleted.

### Step 7 — Post-Merge

```bash
git checkout develop
git pull origin develop
```

Verify develop is green. Update Jira tickets with merge SHA comment.

---

## Main Promotion Policy

`main` is never a direct target of cycle PRs. The only path to main:

```
develop → (release PR) → main
```

First planned promotion: **Foundation Release v0.1.0** after all E01 stories pass release gates.

---

## Commit Scope Reference (DL-032)

| Branch type | Commit scope |
|---|---|
| Integration branch | `cycle-{NNN}` |
| Story branch | Module name (models, collection, scoring, llm, dashboard, etc.) |
| Bug fix branch | Module name |
| Hotfix | hotfix or module name |
