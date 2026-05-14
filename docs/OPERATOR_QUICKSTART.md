# Operator Quickstart (Cycle Branch Workflow)

This quickstart is for PM/operator oversight in an agent-managed cycle branch flow.
When GitHub auth is available, Cursor agents execute branch checks, push, and PR preparation.

## 1) Confirm steward agent context

```powershell
cd C:\Fiverr\Fiverr
git status
git branch --show-current
git log --oneline -8
```

## 2) Start/verify cycle branch from `develop`

Replace `003` with the active cycle number.

```powershell
git checkout develop
git pull origin develop
git checkout -b cycle/003/integration
git status
```

## 3) Run Agents A/B/C/D and commit by ownership

Recommended pattern:

1. Run Agent A prompt and review files changed by Agent A.
2. Commit Agent A changes.
3. Repeat for Agents B, C, and D.
4. Agent D acts as final GitHub steward unless PM assigns another agent.

After each agent:

```powershell
git status
git add <agent-owned-files>
git commit -m "<agent-scope commit message>"
git log --oneline -8
```

## 4) Steward agent runs final validation on cycle branch

```powershell
python -m ruff check src tests
python -m mypy src
python -m pytest -q
git status
```

## 5) Steward agent pushes branch and opens PR into `develop`

```powershell
git push -u origin cycle/003/integration
gh pr create --base develop --head cycle/003/integration --title "Cycle 003 integration" --body "Cycle 003 integration branch with Agent A/B/C/D commits."
```

## 6) Branch protection reminder

- PR target for cycle branches is `develop`.
- Do not push to `main`.
- Do not open cycle PRs to `main`.
- `main` is release-only.
- Human operator approves/reviews; agent steward executes git operations.
