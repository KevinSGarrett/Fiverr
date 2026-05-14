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

After `.github/workflows/ci.yml` executes at least once, add these required checks to `develop` protection:

- CI job status covering:
  - Ruff
  - Mypy
  - Pytest with coverage gate
  - Config check
  - Foundation gate
  - Phase2 smoke
- Codecov project coverage status
- Codecov patch coverage status

Note: Codecov check names are only selectable after a run posts them. Do not mark Codecov as optional; keep coverage as a merge blocker at >=90% project and patch.

## Develop branch protection settings

Configure branch protection for `develop` with at least:

- Require pull request before merging
- Require approvals per team policy
- Require status checks to pass before merging (CI + Codecov project + Codecov patch)
- Require branches to be up to date before merging
- Restrict force pushes and deletions
- Dismiss stale approvals when new commits are pushed (recommended)

Verification command:

- `gh api repos/KevinSGarrett/Fiverr/branches/develop/protection`

If branch-protection automation is blocked by permission constraints, use GitHub UI or REST API with an admin-capable token. Do not claim protection is active until verification succeeds.

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
- CI workflow checks are green
- Codecov project coverage >=90%
- Codecov patch coverage >=90%
- No direct push to `main`
- No unresolved review threads
