# Operator Quickstart (Cycle Branch Workflow)

This quickstart is for PM/operator oversight in an agent-managed cycle branch flow.
When GitHub auth is available, Cursor agents execute branch checks, push, and PR stewardship.

## 1) Confirm steward agent context

```powershell
cd C:\Fiverr\Fiverr
git status
git branch --show-current
git log --oneline -8
```

## 2) Start/verify cycle branch from `develop`

Replace `004` with the active cycle number.

```powershell
git checkout develop
git pull origin develop
git checkout -b cycle/004/integration
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
python -m ruff check .
python -m mypy src
python -m pytest -q --cov=src --cov-report=xml --cov-report=term-missing --cov-fail-under=90
python run.py config-check
python run.py foundation-gate --database-url sqlite:///data/foundation_gate_cycle007.db
python run.py phase2-smoke
git status
```

Capture status as separate categories in steward reports and dashboards:

- Local parity: `ruff`, `mypy`, `pytest --cov --cov-fail-under=90`, `config-check`, `foundation-gate`, `phase2-smoke`.
- GitHub Actions: workflow checks on the PR head SHA.
- Codecov project: repository-level status (`codecov/project`).
- Codecov patch: diff-level status (`codecov/patch`).
- Codex disposition: review-thread replies/resolution per `docs/CODEX_REVIEW_DISPOSITION.md`.

## 5) Steward agent pushes branch and opens/updates PR into `develop`

```powershell
git push -u origin cycle/007/integration
gh pr create --base develop --head cycle/007/integration --title "feat(cycle-007): resume phase 2 after codex and coverage gate closure" --body "Cycle 007 integration branch with Agent A/B/C/D deliverables and stewardship evidence."
```

## 6) Branch protection reminder

- PR target for cycle branches is `develop`.
- Do not push to `main`.
- Do not open cycle PRs to `main`.
- `main` is release-only.
- Human operator approves/reviews; agent steward executes git operations.

## 7) Runtime artifact and zip hygiene

- Runtime database files under `data/` are local artifacts and must stay out of handoff zip packages by default.
- Only archive runtime DB files intentionally, and only outside the repository package output.
- Before handoff, steward agent should verify ignored runtime DB files are not included in packaging commands.
