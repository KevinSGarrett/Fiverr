# Stale Policy
# Fiverr Research System — Stale Branch, PR, and Issue Management

---

## Stale Pull Requests

### Definition
A PR is considered stale when it has no commits, comments, or label changes for a defined period.

### Stale Timeline

| Day | Action | Automated? |
|---|---|---|
| Day 0 | PR opened | — |
| Day 3 | `status:stale` label added + bot comment: "This PR has been inactive for 3 days. Please update, reduce scope, or close." | ✅ stale.yml |
| Day 5 | Bot posts second warning: "This PR will be auto-closed in 2 days if no activity." | ✅ stale.yml |
| Day 7 | PR auto-closed with comment: "Closed due to inactivity. Reopen if still needed." | ✅ stale.yml |

### Exemptions (PRs that are NEVER auto-closed)
| Label | Reason |
|---|---|
| `status:blocked` | Waiting on external dependency |
| `status:on-hold` | Intentionally paused |
| `priority:P1-critical` | Critical work — must be resolved, not closed |
| `type:release` | Release PRs may wait for epic completion |

### Reopening a Closed Stale PR
1. Reopen the PR
2. Rebase from latest develop: `git rebase origin/develop`
3. Push updated branch
4. Remove `status:stale` label
5. CI re-runs automatically

---

## Stale Issues

### Stale Timeline for Issues

| Day | Action | Automated? |
|---|---|---|
| Day 0 | Issue created | — |
| Day 7 | `status:stale` label added + bot comment | ✅ stale.yml |
| Day 21 | Second warning comment | ✅ stale.yml |
| Day 30 | Issue auto-closed | ✅ stale.yml |

### Exemptions (Issues that are NEVER auto-closed)
| Label | Reason |
|---|---|
| `issue:epic` | Epics track long-running work |
| `status:blocked` | Waiting on dependency |
| `priority:P1-critical` | Must be resolved |
| `priority:P2-high` | Important work |

---

## Stale Branches

### Definition
A branch is stale when:
- It has no associated open PR
- Its last commit is older than 7 days
- It has not been merged

### Stale Branch Cleanup
GitHub auto-deletes branches after PR merge (repo setting). For branches without PRs:

**Weekly check (manual):**
```bash
# Prune deleted remote branches locally
git fetch --prune

# List remote branches sorted by last commit date
git for-each-ref --sort=committerdate refs/remotes/origin --format='%(committerdate:short) %(refname:short)'

# Delete branches with no activity for 7+ days and no open PR
# Verify in GitHub UI first — never force-delete without checking
```

### Protected from Deletion
| Branch | Protected? |
|---|---|
| `main` | ✅ Never delete |
| `develop` | ✅ Never delete |
| Any branch with open PR | ✅ Do not delete |
| Feature branches after merge | Auto-deleted |

---

## Stale Workflow Configuration

### stale.yml Settings
```yaml
stale-pr-message: >
  This PR has been inactive for 3 days. Please:
  1. Push new commits to continue work
  2. Add `status:blocked` label if waiting on something
  3. Close if no longer needed
  This PR will be auto-closed after 7 days of inactivity.

close-pr-message: >
  Closed due to 7 days of inactivity. Feel free to reopen
  if this work is still needed — just rebase from develop first.

stale-issue-message: >
  This issue has had no activity for 7 days. Please update
  or add `status:blocked` if waiting. Will auto-close after 30 days.

close-issue-message: >
  Closed due to 30 days of inactivity. Reopen if still relevant.

days-before-pr-stale: 3
days-before-pr-close: 7
days-before-issue-stale: 7
days-before-issue-close: 30

exempt-pr-labels: 'status:blocked,status:on-hold,priority:P1-critical,type:release'
exempt-issue-labels: 'issue:epic,status:blocked,priority:P1-critical,priority:P2-high'
```

---

## Metrics to Track

| Metric | Target | Red Flag |
|---|---|---|
| PRs closed as stale per week | < 2 | > 5 means agents are creating PRs they don't finish |
| Average PR age at merge | < 2 days | > 4 days means bottlenecks |
| Stale branches at any time | 0 | > 3 means cleanup is falling behind |
| Issues closed as stale per month | < 5 | > 10 means issues are being created without follow-through |
