# Branching Strategy
# Fiverr Research System — Git Flow for AI-Driven Development

---

## Branch Architecture

```
main (production)
 └── develop (integration)
      ├── feature/epic01/S1.1-project-scaffolding     (Agent 1)
      ├── feature/epic02/S2.7-keyword-expansion        (Agent 2)
      ├── feature/epic04/S4.1-demand-score             (Agent 3)
      ├── feature/epic09/S9.3-opportunities-page       (Agent 4)
      ├── fix/epic02/broken-gig-selector               (Any agent)
      ├── chore/update-dependencies                    (Agent 1)
      └── hotfix/critical-db-migration-fix             (Any agent → main)
```

---

## Branch Types

### 1. `main` — Production Branch
- **Purpose:** Always contains stable, tested, working code
- **Who merges here:** Only from `develop` via release PR
- **When:** After a complete epic is tested end-to-end
- **Protection:** Full CI + all checks must pass
- **Direct commits:** NEVER allowed
- **Force push:** NEVER allowed

### 2. `develop` — Integration Branch
- **Purpose:** Integration point for all feature work
- **Who merges here:** All agents merge feature branches here
- **When:** After PR checks pass
- **Protection:** CI checks must pass
- **Direct commits:** NEVER allowed
- **This is the "working trunk"** — agents branch FROM develop and merge BACK to develop

### 3. `feature/*` — Feature Branches
- **Purpose:** All new development work
- **Lifecycle:** Created from `develop` → work → PR to `develop` → delete after merge
- **Naming:** See BRANCH_NAMING.md
- **Who creates:** Any agent, for their assigned stories/tasks
- **One branch per story** (preferred) or per logical unit of work
- **Max lifetime:** 3 days. If not merged in 3 days, rebase from develop and reassess scope

### 4. `fix/*` — Bug Fix Branches
- **Purpose:** Fix bugs found during development
- **Lifecycle:** Created from `develop` → fix → PR to `develop` → delete
- **When:** Bug discovered that blocks other work

### 5. `hotfix/*` — Critical Production Fixes
- **Purpose:** Emergency fixes to `main`
- **Lifecycle:** Created from `main` → fix → PR to `main` AND `develop` → delete
- **When:** Production-breaking bug that can't wait for normal flow
- **Expected frequency:** Rare (< 1 per month)

### 6. `chore/*` — Maintenance Branches
- **Purpose:** Dependency updates, config changes, docs, CI changes
- **Lifecycle:** Same as feature branches
- **When:** Non-functional changes

---

## Merge Strategy

### All merges use SQUASH MERGE
- Every PR becomes a single commit on the target branch
- PR title becomes the commit message
- This keeps `develop` and `main` history clean and readable
- Individual commits within a feature branch don't matter (they get squashed)

### Merge Direction Flow
```
feature/* → develop (via PR, squash merge)
develop → main (via release PR, squash merge)
hotfix/* → main (via PR, squash merge)
hotfix/* → develop (via second PR or cherry-pick)
```

### Merge Rules
| Rule | Enforcement |
|---|---|
| No direct pushes to main | Branch protection |
| No direct pushes to develop | Branch protection |
| All merges via PR | Branch protection |
| All PRs must pass CI | Required status checks |
| Squash merge only | Merge commit and rebase disabled in settings |
| Delete branch after merge | Automatic (repo setting) |

---

## Agent Workflow

### Daily Agent Workflow
```
1. Agent receives task assignment (from ChatGPT PM via issue)
2. Agent creates feature branch from latest develop
   git checkout develop
   git pull origin develop
   git checkout -b feature/epic01/S1.2-config-system
3. Agent implements the task (multiple commits OK — they'll be squashed)
4. Agent pushes branch
   git push -u origin feature/epic01/S1.2-config-system
5. Agent creates PR to develop (using PR template)
6. CI runs automatically
7. If CI passes → squash merge to develop
8. Branch auto-deleted
```

### Before Starting Any New Branch
```bash
# ALWAYS start from latest develop
git checkout develop
git pull origin develop
git checkout -b feature/epicXX/description
```

### Conflict Resolution
If develop has changed since branch creation:
```bash
# Option A: Rebase (preferred for clean history)
git checkout feature/epic01/S1.2-config-system
git fetch origin
git rebase origin/develop
# Resolve conflicts if any
git push --force-with-lease

# Option B: Merge develop in (if rebase is too complex)
git checkout feature/epic01/S1.2-config-system
git merge origin/develop
# Resolve conflicts
git push
```

---

## Release Flow

### When to Create a Release
- After completing a full epic (all stories merged to develop)
- After the integration tests pass on develop
- Minimum: once per epic completion

### Release Process
```
1. Ensure develop is stable (all CI green)
2. Create PR: develop → main
   Title: "release: Epic 01 — Foundation & Infrastructure"
   Body: List all stories merged since last release
3. All checks must pass
4. Squash merge to main
5. Tag the release:
   git checkout main
   git pull origin main
   git tag -a v0.1.0 -m "Epic 01: Foundation & Infrastructure"
   git push origin v0.1.0
```

### Version Numbering
```
v0.{epic_number}.{patch}

v0.1.0 — Epic 01 complete
v0.2.0 — Epic 02 complete
v0.3.0 — Epic 03 complete
...
v0.10.0 — Epic 10 complete (launch ready)
v1.0.0 — First production release (post-validation)
```
