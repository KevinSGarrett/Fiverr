# Branch Protection Rules
# Fiverr Research System — Detailed Configuration

---

## Protection Rule: `main`

### Access via: Settings → Branches → Add branch protection rule
**Branch name pattern:** `main`

| Setting | Value | Reason |
|---|---|---|
| Require a pull request before merging | ✅ | No direct pushes to production |
| Required number of approvals | 0 | Single developer project — self-approve via passing checks |
| Dismiss stale pull request approvals when new commits are pushed | ✅ | Re-validate after changes |
| Require review from Code Owners | ❌ | Single developer |
| Restrict who can dismiss pull request reviews | ❌ | N/A |
| Require approval of the most recent reviewable push | ❌ | N/A |
| **Require status checks to pass before merging** | ✅ | **Critical — this is the quality gate** |
| Require branches to be up to date before merging | ✅ | Ensures tested against latest main |
| **Required status checks:** | | |
| — `ci / lint` | ✅ | Ruff linting must pass |
| — `ci / type-check` | ✅ | Mypy type checking must pass |
| — `ci / test` | ✅ | Pytest with ≥80% coverage must pass |
| — `pr-checks / validate-pr` | ✅ | PR title, size, labels must pass |
| Require conversation resolution before merging | ✅ | All comments addressed |
| Require signed commits | ❌ | Optional — enable for higher security |
| Require linear history | ✅ | Squash merge enforces this |
| Require merge queue | ❌ | Not needed for single developer |
| Require deployments to succeed | ❌ | No CD pipeline in v1 |
| Lock branch | ❌ | |
| Do not allow bypassing the above settings | ✅ | Even admin must follow rules |
| Restrict who can push to matching branches | ✅ | Only via PR merge |
| Allow force pushes | ❌ **NEVER** | Prevents history destruction |
| Allow deletions | ❌ **NEVER** | Prevents branch deletion |

---

## Protection Rule: `develop`

**Branch name pattern:** `develop`

| Setting | Value | Reason |
|---|---|---|
| Require a pull request before merging | ✅ | All work via feature branch PRs |
| Required number of approvals | 0 | AI agents self-merge after CI |
| Dismiss stale pull request approvals | ✅ | |
| **Require status checks to pass** | ✅ | |
| **Required status checks:** | | |
| — `ci / lint` | ✅ | |
| — `ci / type-check` | ✅ | |
| — `ci / test` | ✅ | |
| Require branches to be up to date | ❌ | Relaxed for develop — agents merge frequently, strict up-to-date causes rebase churn |
| Require conversation resolution | ✅ | |
| Require linear history | ❌ | Squash merge handles this |
| Do not allow bypassing | ✅ | |
| Allow force pushes | ❌ **NEVER** | |
| Allow deletions | ❌ **NEVER** | |

---

## Why No Approval Requirement?

This is a single-developer project operated by AI agents. The quality gate is **automated CI checks**, not human review. The checks are:

1. **Linting** — Code style and error detection
2. **Type checking** — Static type analysis
3. **Tests** — Unit + integration tests with coverage threshold
4. **PR validation** — Title format, size limits, required labels

If all 4 checks pass, the PR is safe to merge. Human review is applied selectively for high-risk PRs (see RISK_TIERS.md).

---

## Emergency Override Procedure

If a critical fix needs to bypass checks (extremely rare):

1. **Document why** in the PR description
2. **Add label:** `override:emergency`
3. **Admin can temporarily disable** the "Do not allow bypassing" setting
4. **Re-enable immediately** after the merge
5. **Create a follow-up issue** to add the missing test/fix that should have been there
6. **Log the override** in the project changelog
