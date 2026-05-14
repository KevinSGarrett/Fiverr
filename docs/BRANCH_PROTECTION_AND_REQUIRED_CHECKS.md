# Branch Protection and Required Checks Runbook

## Policy baseline

- Default branch must be `develop` during active development cycles.
- Cycle work must happen on `cycle/###/integration` branches and merge into `develop`.
- `main` is release-only and must not receive direct cycle merges or direct pushes.

## Set and verify default branch

1. Verify current default branch:
   - `gh repo view KevinSGarrett/Fiverr --json defaultBranchRef`
2. Set default branch to `develop` when required:
   - `gh repo edit KevinSGarrett/Fiverr --default-branch develop`
3. Re-verify:
   - `gh repo view KevinSGarrett/Fiverr --json defaultBranchRef`

If the `gh repo edit` command fails due to permission scope, perform the same action in GitHub repository settings and record the operator who completed it.

## Required checks for `develop` after first CI run

After `.github/workflows/ci.yml` executes at least once, configure these checks as required for `develop`:

- `CI / Lint, Typecheck, Tests, and Gates`
- `codecov/project`
- `codecov/patch`

Codecov check names are only selectable after Codecov has posted them at least once. Do not mark Codecov as optional; keep both coverage checks as merge blockers at >=90% project and patch targets.

## Configure required checks in GitHub UI

1. Open repository settings:
   - `https://github.com/KevinSGarrett/Fiverr/settings/branches`
2. Edit the `develop` branch protection rule (or create one if missing).
3. Enable **Require status checks to pass before merging**.
4. Add required checks:
   - `CI / Lint, Typecheck, Tests, and Gates`
   - `codecov/patch`
   - `codecov/project` (when visible)
5. Save changes, then open a fresh PR targeting `develop` and verify all three checks appear in the merge box.

## Configure required checks with `gh`/API (operator path)

1. Capture live check names from a recent successful commit on `develop`:
   - `gh api repos/KevinSGarrett/Fiverr/commits/develop/check-runs`
   - `gh api repos/KevinSGarrett/Fiverr/commits/develop/status`
2. Update branch protection (admin token required), including:
   - Required context `CI / Lint, Typecheck, Tests, and Gates`
   - Required context `codecov/patch`
   - Required context `codecov/project` once posted by Codecov
3. Verify protection:
   - `gh api repos/KevinSGarrett/Fiverr/branches/develop/protection`

If API updates are blocked by permissions, use GitHub UI and record the operator.

## Develop branch protection settings

Configure branch protection for `develop` with at least:

- Require pull request before merging
- Require approvals per team policy
- Require status checks to pass before merging (`CI / Lint, Typecheck, Tests, and Gates` + `codecov/project` + `codecov/patch`)
- Require branches to be up to date before merging
- Restrict force pushes and deletions
- Dismiss stale approvals when new commits are pushed (recommended)

Verification command:

- `gh api repos/KevinSGarrett/Fiverr/branches/develop/protection`

If branch-protection automation is blocked by permission constraints, use GitHub UI or REST API with an admin-capable token. Do not claim protection is active until verification succeeds.

## Missing `codecov/project` handling policy

If `codecov/patch` is present but `codecov/project` is absent on PRs/commits:

1. Treat the PR as **not automatically merge-ready**.
2. Steward must investigate visibility (Codecov config, first baseline run on `develop`, app/repo linkage, token/auth mode).
3. Steward must either:
   - restore `codecov/project` visibility and add it as a required check, or
   - document a PM-approved temporary exception in cycle governance artifacts.

Stewards cannot self-authorize temporary exceptions.

## Main branch release-only policy

For `main`:

- Allow merges only from release PRs based on `develop`.
- Require all checks and approvals.
- Block direct pushes.
- Keep stricter controls than `develop`.

If `main` does not yet exist, create and protect it before first release cutover.

## Merge blockers checklist

- Default branch is `develop`
- PR targets `develop` for cycle integration work
- `CI / Lint, Typecheck, Tests, and Gates` is green
- `codecov/project` is visible and green at >=90% (or PM-approved documented exception)
- `codecov/patch` is visible and green at >=90%
- No direct push to `main`
- No unresolved review threads
