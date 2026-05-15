# BRANCH WORKFLOW PER CYCLE

---

### 1. Create Integration Branch
```bash
cd C:\Fiverr
git checkout develop
git pull origin develop
git checkout -b cycle/{NNN}/integration
```

### 2. Agents Work Sequentially
Agent A -> commit -> Agent B -> commit -> Agent C -> commit -> Agent D -> commit

Each commit: {type}({scope}): {description} [Agent {X}]

### 3. Push
```bash
git push -u origin cycle/{NNN}/integration
```

### 4. Create PR
- Target: develop
- Title: feat(cycle-{NNN}): {summary from PM}
- Body: task list from PM (use PR_CYCLE_BATCH.md template)
- Labels: type:feature, priority:P3-medium, scope:{epic}, risk:{level}

### 5. CI Runs
lint -> type-check -> test -> PR validation

### 6. Merge
- All green -> squash merge
- Failing -> PM diagnoses, creates fix tasks


## Main Promotion Policy — Binding After Cycle 001 Corrective Review

Cursor agents must **never push directly to `main`**. Normal cycle flow is:

1. Human creates `cycle/{NNN}/integration` from `develop`.
2. Agents A-D run sequentially on the same branch and commit only their assigned files.
3. Human pushes the cycle branch once after all agent commits.
4. Human opens one PR from `cycle/{NNN}/integration` into `develop`.
5. PM reviews agent work and CI evidence.
6. Human squash-merges to `develop` only after PM approval and green gates.
7. `main` is updated only by a separate approved release PR from `develop` into `main`.

For this project, the first planned `develop -> main` promotion should be the **Foundation Release v0.1.0** after Epic 01 passes release gates: config loads, DB init works, CLI smoke works, tests pass, no secrets/data hygiene issues, and PM confidence is acceptable. Earlier direct pushes to `main` are not part of the strategy.

## Cycle 005 Addendum — Integration/GitHub Steward Ownership

Post-agent GitHub work is assigned to the Cursor Integration/GitHub Steward, normally Agent D unless the PM assigns Agent A. The steward owns final validation, Codex review disposition verification, push/PR update, check verification, and merge readiness reporting. The human operator is not the default executor for push/PR/merge tasks.
