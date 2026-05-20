# GITHUB RULES FOR PM
# Updated: Cycle 019

---

## Repository Info

| Field | Value |
|---|---|
| Repo URL | https://github.com/KevinSGarrett/Fiverr |
| Default branch | develop (active development) |
| Production branch | main (release only — no direct pushes) |
| Local path | C:\Fiverr\Fiverr |
| Jira integration | Live — auto-links commits/PRs to Jira keys |

---

## PM Responsibilities Per Cycle

1. Define cycle integration branch name before any agent works
2. Specify exact branch name in every agent prompt
3. Define PR title (must be ≤72 chars, follow conventional commits, no em-dash)
4. Define PR body (include Jira keys, summary, validation commands)
5. Verify all CI checks pass before approving merge
6. Ensure all agents commit to the SAME integration branch
7. Add `override:large-pr` label to PR if total diff exceeds 1000 lines
8. Track branch lifecycle in cycle log

---

## Branch Rules

| Branch type | Format | Example |
|---|---|---|
| Cycle integration | `cycle/{NNN}/integration` | `cycle/020/integration` |
| Story feature | `feature/epic{NN}/SCRUM-{key}-{slug}` | `feature/epic01/SCRUM-136-db-init` |
| Bug fix | `fix/SCRUM-{key}-{slug}` | `fix/SCRUM-200-config-crash` |
| Hotfix | `hotfix/{description}` | `hotfix/missing-import` |

**DL-031:** Integration branches use `cycle/{NNN}/integration`. Story branches use `feature/epic{NN}/SCRUM-{key}-{slug}`.

---

## Deployed GitHub Infrastructure (Cycle 019)

### Workflows (all in .github/workflows/)
| File | Purpose |
|---|---|
| `ci.yml` | Lint (Ruff) + Type-check (Mypy) + Tests (Pytest) + Codecov |
| `pr-checks.yml` | PR title validation + PR size check (max 1000 lines, override with label) |
| `security.yml` | Secret scan + dependency audit |
| `stale.yml` | Auto-marks PRs/issues stale after 30 days |
| `release.yml` | Auto-creates GitHub release when a tag is pushed to main |

### Labels (61 deployed)
See `ref/github/03_labels/LABEL_TAXONOMY.md` for full list. Key labels:
- `override:large-pr` — required on any PR exceeding 1000 lines (add BEFORE CI runs)
- `agent:1-infrastructure` through `agent:4-dashboard` — one per PR
- `priority:P1-critical` through `priority:P4-low`
- `scope:epic01` through `scope:epic10`

### Repo Files
- `.cursorrules` — Cursor agent architecture rules (line-length=100, dual templates, etc.)
- `.github/CODEOWNERS` — directory ownership per agent
- `.github/dependabot.yml` — weekly pip and actions updates
- `.github/ISSUE_TEMPLATE/` — 5 templates (bug, epic, feature, spike, task)
- `.github/pull_request_template.md` — cycle-format 91-line template

---

## PR Rules

### Title Format (CRITICAL — enforced by pr-checks.yml)
```
{type}({scope}): {description}
```
- Max 72 characters total
- Allowed types: feat, fix, refactor, test, docs, chore, style, perf, ci, build, release, hotfix, revert
- No em-dashes (—), only ASCII hyphens (-)
- No period at end
- Examples:
  - `feat(cycle-020): E02 collection engine core pipeline [Claude AI]`
  - `fix(scoring): correct saturation score direction [Agent C]`

### PR Size Policy
- Warning at 300 lines changed
- Block at 1000 lines changed
- To bypass: add `override:large-pr` label BEFORE opening the PR
- Audit/batch PRs always need `override:large-pr`

### Required Labels on Every PR
At minimum: `type:*` + `priority:*` + `scope:*` + `agent:*`

### Merge Method
- Always: squash merge only
- Never: merge commit or rebase merge
- Branch auto-deletes after merge

---

## CI Requirements (ALL must pass before merge)

| Check | Tool | Threshold |
|---|---|---|
| Lint | Ruff | Zero errors |
| Type-check | Mypy | Zero errors (136+ source files) |
| Tests | Pytest | All passing |
| Coverage | Codecov | >=90% project, >=90% patch |
| PR title | pr-checks.yml | Valid format + ≤72 chars |
| PR size | pr-checks.yml | ≤1000 lines OR override:large-pr label present |
| Secret scan | security.yml | No secrets in src/ |
| Dependency audit | security.yml | No known vulnerabilities |

---

## Push Policy

- Cursor agents commit locally; human operator pushes the branch
- Cursor agents do NOT push independently unless PM explicitly authorizes
- Cursor agents NEVER push to main directly
- Only one PR per cycle (from cycle/NNN/integration to develop)
- main is updated only by a separate approved release PR

---

## Dependabot Policy

Dependabot is active and will auto-open PRs weekly for pip and actions updates. Protocol:
1. Let Dependabot open the PR
2. Wait for CI to run against the current develop base
3. If CI passes: merge the Dependabot PR
4. If CI fails: close the PR with comment explaining the failure; Dependabot will reopen on next schedule
5. Never merge a Dependabot PR that fails CI
6. Never manually force-update a Dependabot PR — let it reopen cleanly

See `05_github_protocol/DEPENDABOT_PROTOCOL.md` for full details.
