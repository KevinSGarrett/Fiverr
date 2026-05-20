# JIRA UPDATE CHECKLIST — Run EVERY Cycle
# Updated: Cycle 019

---

## Pre-Cycle (Before Agent Work Starts)

- [ ] Active sprint exists — if not, create "Cycle {NNN}" sprint in Jira
- [ ] All planned stories moved from Backlog → To Do
- [ ] Sprint assignment confirmed for all planned stories
- [ ] Agent labels assigned (agent:1 through agent:4) — NOT agent:A/B/C/D
- [ ] Scope labels confirmed (scope:epic0N) on all active stories
- [ ] Type and priority labels set on all active stories
- [ ] Planning comment added to each story: branch name + cycle number
- [ ] fixVersion assigned if story targets v0.1.0 Foundation release

## During Cycle (After Each Agent Completes)

- [ ] Agent work committed with Jira key in commit message
- [ ] Branch name includes Jira key (e.g., feature/epic01/SCRUM-136-db-init)
- [ ] Story status moved to In Progress when agent begins
- [ ] Partial progress commented with AC status update

## Post-Cycle (After PR Merged)

- [ ] All completed stories transitioned to Done with merge evidence comment
- [ ] All incomplete stories transitioned back to To Do with rework comment
- [ ] All blocked stories marked Blocked with blocker description
- [ ] PR number recorded on each story (Development panel auto-links — verify it populated)
- [ ] Merge SHA commented on each Done story
- [ ] Story progress updated on parent epic: "X of Y stories Done"
- [ ] Epic progress percentage updated on epic ticket
- [ ] New Bug tickets created for any issues found during review
- [ ] Cycle sprint closed or left open based on PM decision
- [ ] No ticket left In Progress from the completed cycle

## Every 5 Cycles

- [ ] Cross-reference TASK_BACKLOG.md status with live Jira board
- [ ] Verify all completed stories have GitHub development panel links
- [ ] Verify no orphan stories exist (stories without parent epic)
- [ ] Verify label completeness (all 61 deployed labels are correctly applied)
- [ ] Verify fixVersion assignments are current

## Jira-GitHub Integration Health Check

- [ ] Open any recently merged story in Jira
- [ ] Scroll to Development panel on the right
- [ ] Confirm linked PRs and commits appear automatically
- [ ] If Development panel is empty for a merged story, verify the branch/commit contained the Jira key
- [ ] Integration URL: https://kevinsgarrett.atlassian.net/jira/settings/apps/github

## Comment Format Compliance

All Jira comments must follow this format — reject any that do not:
```
[Cycle NNN] Agent {1|2|3|4|pm} | Branch: cycle/NNN/integration | PR: #N

Summary: {what was done}
AC status: AC-X.X.X: PASS/FAIL
DoD status: PARTIAL / COMPLETE
Confidence: NN/100
```
