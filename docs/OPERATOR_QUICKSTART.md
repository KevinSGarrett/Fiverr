# Operator Quickstart (Cycle Branch Workflow)

This quickstart is for the human operator running cycle work in a shared branch flow.

## 1) Verify current branch and clean context

```powershell
cd C:\Fiverr\Fiverr
git status
git branch --show-current
git log --oneline -8
```

## 2) Start a new cycle branch from `develop`

Replace `002` with the active cycle number.

```powershell
git checkout develop
git pull origin develop
git checkout -b cycle/002/integration
git status
```

## 3) Run agents in order and commit after each agent

Recommended pattern:

1. Run Agent A prompt and review files changed by Agent A.
2. Commit Agent A changes.
3. Repeat for Agents B, C, and D.

After each agent:

```powershell
git status
git add <agent-owned-files>
git commit -m "<agent-scope commit message>"
git log --oneline -8
```

## 4) Final validation on cycle branch

```powershell
python -m ruff check src tests
python -m mypy src
python -m pytest -q
git status
```

## 5) Push cycle branch and open PR into `develop`

```powershell
git push -u origin cycle/002/integration
gh pr create --base develop --head cycle/002/integration --title "Cycle 002 integration" --body "Cycle 002 integration branch with Agent A/B/C/D commits."
```

## 6) Branch protection reminder

- Do not push to `main`.
- Do not open cycle PRs to `main`.
- `main` is release-only.
