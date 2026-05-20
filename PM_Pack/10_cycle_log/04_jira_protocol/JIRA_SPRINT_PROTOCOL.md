# JIRA SPRINT PROTOCOL
# Added: Cycle 019

---

## Sprint Naming Convention

Format: `Cycle {NNN}`
Example: `Cycle 019`, `Cycle 020`

---

## Creating a New Sprint

Before each new development cycle begins:

1. Navigate to: Board → Backlog → Create Sprint
2. Name: `Cycle {NNN}` (use zero-padded 3-digit number)
3. Do NOT set a fixed duration — manage dates manually
4. Start date: When agent work begins
5. End date: When PR is expected to merge

---

## Sprint Story Assignment Rules

1. Only assign stories that will actually be worked this cycle
2. Every story in the sprint must have an assigned agent label
3. Every story must have scope, type, and priority labels before sprint starts
4. Target 20-40 tasks across all 4 agents per sprint (5-10 per agent)
5. Never assign E02 stories while E01 blocking stories are incomplete

---

## Sprint Closure Rules

At the end of each cycle:
- Stories marked Done: leave in the closed sprint (they are recorded there)
- Stories not completed: move to Backlog or the next sprint
- Never leave a sprint open indefinitely — close after PR merges
- Never close a sprint while any story is still In Progress

---

## Current Sprint History

| Sprint | ID | Stories | Status |
|---|---|---|---|
| Cycle 019 | 35 | 29 | Active |

---

## fixVersion Management

Current: `v0.1.0 - Foundation`

Rules:
- Only assign fixVersion to stories included in the upcoming release
- v0.1.0 Foundation = all E01 stories (S1.1 through S1.11)
- Create `v0.2.0 - Collection` when E02 work begins
- Never assign a future version to a story that is not yet In Progress
