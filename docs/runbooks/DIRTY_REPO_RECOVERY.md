# Dirty Repo Recovery

## 1) Classification First (Mandatory)

Always begin with classification:

```powershell
Set-Location C:\Fiverr\Fiverr
git status --short
git diff --stat HEAD
```

Classify each changed file:

- AGENTWORK: expected from active agent scope
- UNEXPECTED: changed but outside intended scope
- CRASHRESIDUE: partial/incomplete writes after crash
- INTENTIONAL: manual human edits

Never start with cleanup commands.

## 2) If All Changes Are AGENTWORK

Validate before keeping:

```powershell
.venv\Scripts\python.exe -m ruff check automation/ src/ tests/ --output-format=full
.venv\Scripts\python.exe -m mypy automation/ src/ --ignore-missing-imports
.venv\Scripts\python.exe -m pytest -q
```

If validation passes, controller can stage approved files.

## 3) If UNEXPECTED or CRASHRESIDUE Exists

Preserve evidence first:

```powershell
$date = Get-Date -Format "yyyyMMdd"
$dst = "C:\AI_Runner\reports\incidents\DIRTY_REPO_$date"
New-Item -ItemType Directory -Path $dst -Force | Out-Null
```

Copy suspicious files to incident folder before deciding keep/discard.

Discard only with explicit file path:

```powershell
git checkout -- <specific_file>
```

Never run `git checkout -- .` or `git clean -fd`.

## 4) Stash Safe Holding Area

Use stash as reversible checkpoint:

```powershell
git stash push -m "dirty-repo-recovery-YYYYMMDD"
git stash show -p
```

This enables structured inspection before restoration.

## 5) Validation After Cleanup

Run validation after any recovery change:

```powershell
.venv\Scripts\python.exe -m ruff check automation/ src/ tests/ --output-format=full
.venv\Scripts\python.exe -m pytest -q
```

If validation fails, stop and document blocker.

## 6) Incident Documentation

Create incident file:

`C:\AI_Runner\reports\incidents\DIRTY_REPO_YYYYMMDD.md`

Include:

- files changed
- classification labels
- keep/discard actions
- stash usage
- validation outcomes

Recovery is complete only when classification, preservation, cleanup, and validation are all recorded.

## Emergency: Committing Deferred Agent Work

If agent work was completed but not committed (e.g., the controller did not run the commit
lifecycle), follow these steps to safely commit without using git add -A:

1. Run: git status --short  (review all modified/untracked files)
2. Run secret guard on all modified files
3. Stage only approved files: git add -- <file1> git add -- <file2> ...
4. Verify staged diff: git diff --cached --stat
5. Commit with descriptive message including cycle number
6. Push: git push origin <branch>

