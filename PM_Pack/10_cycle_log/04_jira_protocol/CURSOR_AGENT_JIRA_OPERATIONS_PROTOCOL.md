# Cursor Agent Jira Operations Protocol

Version: Cycle 010

## Operator-confirmed authority

Cursor agents have full read/write/edit access to the connected Jira board. The PM may explicitly assign Cursor agents to perform Jira work during any cycle.

Cursor agents may, when instructed:

- read Jira issues,
- search Jira board state,
- inspect issue descriptions and acceptance criteria,
- create Jira issues,
- update Jira issue descriptions,
- add Jira comments,
- transition Jira issue status,
- add implementation evidence,
- update Jira mapping tables,
- create bug/rework tickets from Codex/CI/QA findings,
- reconcile changed files to product-story Jira keys.

## Required guardrails

Cursor agents must follow these rules when touching Jira:

1. Never mark a broad product story Done unless the full source DOD is satisfied.
2. For partial implementation, use In Progress.
3. For PR-ready implementation with passing checks, use In Review.
4. For governance tickets, Done is allowed only after the PM Pack/repo-side rule has actually been merged or the requested process change is complete.
5. Every Jira comment must include:
   - cycle number,
   - agent name,
   - branch,
   - PR number or expected PR,
   - changed file group,
   - validation evidence,
   - Codex/CI/Codecov status when relevant,
   - whether the Jira story is partial or full DOD completion.
6. Product-code changes must update product tickets, not only governance tickets.
7. Governance changes must update governance tickets, not only product tickets.
8. If a Cursor agent cannot access Jira, it must report the blocker and include exact Jira operations that should be performed.

## PM prompt requirement

Every cycle prompt must explicitly state whether the agent is responsible for Jira operations.

Examples:

- "You must update SCRUM-154 and SCRUM-156 after completing validation."
- "You must create a bug if Codex identifies a valid defect."
- "You must not update Jira in this cycle; include a report only."

## Default ownership

| Role | Normal Jira responsibility |
|---|---|
| Agent A | Foundation, Integration, CI/GitHub governance, branch/PR/Jira mapping governance |
| Agent B | Collection tickets and collection-related bugs |
| Agent C | Analysis, Scoring, Recommendations, Pricing, Discovery tickets |
| Agent D | Dashboard, Reporting, Export, Playbook, PR stewardship evidence tickets |

## Relationship to PM

The PM remains responsible for reviewing Jira state and ensuring the final cycle handoff is accurate. Cursor agents can execute Jira operations directly when assigned, but the PM must still audit outcomes before the next cycle.
