# JIRA COMMENT PROTOCOL — 10 Triggers

---

| # | Event | Template |
|---|---|---|
| 1 | Task assigned to cycle | [Cycle {NNN}] Assigned to Agent {X}. Branch: cycle/{NNN}/integration |
| 2 | Task completed by agent | [Cycle {NNN}] Completed by Agent {X}. Files: {list}. Tests: {pass/fail}. Confidence: {score}/100 |
| 3 | Task failed review | [Cycle {NNN}] Review failed. Issues: {list}. Rework assigned to Cycle {NNN+1} |
| 4 | Task blocked | [Cycle {NNN}] Blocked by: {description}. Waiting on: {ticket or action} |
| 5 | Task rework completed | [Cycle {NNN}] Rework completed. Original issues resolved. |
| 6 | Bug discovered | [Cycle {NNN}] Bug found during review. Bug ticket: {JIRA-ID} |
| 7 | Epic milestone | [Cycle {NNN}] Progress: {X}% complete. Stories done: {N}/{total} |
| 8 | PR created | [Cycle {NNN}] PR #{N} created: cycle/{NNN}/integration -> develop |
| 9 | PR merged | [Cycle {NNN}] PR #{N} merged to develop. CI: passed. |
| 10 | Dependency resolved | [Cycle {NNN}] Dependency resolved. {ticket} now unblocked. |

## Rules
- Every comment starts with [Cycle {NNN}]
- Comments are factual — no opinions or speculation
- Include specifics (file names, test counts, error messages)
- Link related tickets when relevant
- Never leave a status transition without a comment
