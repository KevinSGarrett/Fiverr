# Hygiene Checklist
# Fiverr Research System — Ongoing Maintenance Tasks

---

## Daily Hygiene (Automated)

These tasks run automatically via GitHub Actions or are part of normal agent workflow:

| Task | How | Frequency |
|---|---|---|
| CI checks on every PR | ci.yml, pr-checks.yml | Every PR |
| Stale PR/issue detection | stale.yml | Daily at 9 AM UTC |
| Dependency vulnerability scan | Dependabot alerts | Continuous |
| Secret scanning | GitHub native + security.yml | Every PR |
| Branch auto-deletion after merge | Repo setting | Every merge |

---

## Weekly Hygiene (Manual — Human Operator)

Run these checks every Monday morning (or assign ChatGPT PM to remind):

### 1. Branch Cleanup
```bash
# List all remote branches
git fetch --prune
git branch -r

# Check for branches older than 7 days that weren't auto-deleted
# (Happens if PRs were abandoned without merging)
```

**Action:** Close stale PRs and delete orphaned branches.

### 2. Open PR Review
- Go to: GitHub → Pull Requests → Open
- Any PR open > 3 days without the `status:blocked` label needs attention
- Either: merge it, close it, or add `status:blocked` with a reason

### 3. Open Issue Review
- Go to: GitHub → Issues → Open
- Verify all open issues are assigned and have correct labels
- Close any completed issues that weren't auto-closed by PRs
- Ensure no issue has been `status:stale` for > 14 days without action

### 4. CI Health Check
- Go to: GitHub → Actions
- Verify no workflows are failing on develop
- Check for any workflows stuck in "queued" state
- Review workflow run times — flag any that exceed the performance budget

### 5. Coverage Trend
- Review the latest coverage report from CI
- Ensure coverage hasn't dropped below 80%
- If trending down, create an issue: `type:test` to add missing tests

---

## Bi-Weekly Hygiene

### 6. Dependency Updates
- Review Dependabot PRs that have accumulated
- Merge low-risk dependency updates (patch versions)
- Test and merge minor version updates
- Create issues for major version updates that need investigation

### 7. Label Audit
- Verify all required label categories still exist
- Check for unused or duplicate labels
- Ensure color scheme is consistent

---

## Monthly Hygiene

### 8. Repository Health Report
Create a summary covering:

| Metric | Target | How to Check |
|---|---|---|
| Open PRs | < 5 | GitHub → PRs → Open |
| Open issues | Trending down | GitHub → Issues → Open |
| Average PR age | < 2 days | Review PR merge timestamps |
| CI pass rate | > 95% | GitHub → Actions → filter by status |
| Coverage | ≥ 80% | Latest CI coverage report |
| Dependency vulnerabilities | 0 critical/high | Dependabot → Security tab |
| Stale branches | 0 | `git branch -r` after prune |

### 9. Documentation Review
- Verify README.md is up to date
- Check that docs/ files match current system behavior
- Update SETUP.md if dependencies or config changed
- Ensure TROUBLESHOOTING.md covers recent issues

### 10. .cursorrules Review
- Review if any new patterns emerged that should be added
- Verify rules still match the current architecture
- Update if new modules/directories were added

---

## Per-Epic Hygiene (After Each Epic Completes)

### 11. Post-Epic Cleanup
- [ ] All stories for the epic are closed
- [ ] All feature branches for the epic are deleted
- [ ] Release PR merged to main with version tag
- [ ] CHANGELOG.md updated with all stories
- [ ] No leftover TODO/FIXME comments from the epic
- [ ] Integration tests pass on main
- [ ] Documentation updated for new features
- [ ] Coverage maintained at ≥ 80%

---

## Hygiene Automation Opportunities

| Task | Can Automate? | Tool |
|---|---|---|
| Stale detection | ✅ Already automated | stale.yml |
| Branch cleanup | ✅ Already automated | Auto-delete setting |
| Coverage check | ✅ Already automated | Pytest CI gate |
| Secret scanning | ✅ Already automated | security.yml |
| Dependency alerts | ✅ Already automated | Dependabot |
| Open PR report | 🔜 Future | Scheduled workflow posting to Slack/Discord |
| TODO/FIXME scan | 🔜 Future | Custom CI step scanning for leftover markers |
| Changelog generation | 🔜 Future | Auto-generate from merged PR titles |
