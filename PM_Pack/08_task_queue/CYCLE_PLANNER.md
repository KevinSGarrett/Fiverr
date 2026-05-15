# CYCLE PLANNER
# Logic for selecting tasks each cycle

---

## Planning Algorithm

```
1. READ current state from STATE_SNAPSHOT.md and EPIC_STATUS_TRACKER.md
2. IDENTIFY which phase we're in (1-7)
3. IDENTIFY which epics are active in that phase
4. FOR each active epic:
   a. Find the next incomplete story (lowest number first)
   b. Get all tasks in that story
   c. Check DEPENDENCY_MAP — are dependencies met?
   d. If yes -> add to candidate pool
   e. If no -> skip (or assign dependency work first)
5. ASSIGN candidates to agents based on AGENT_ROSTER.md ownership
6. VERIFY no file overlap between agents
7. VERIFY total tasks per agent is 20-40 (target 24-32) unless both waivers are approved
8. OUTPUT task assignments for 4 agents
```

---

## Phase Guidance

### Phase 1: Foundation (Cycle 001 — approx Cycle 005)
- Focus: Epic 01 only
- Agent A: S1.1 scaffolding, S1.2 config, S1.3 models — lead
- Agent B: S1.3 support (model tests), S1.5 logging
- Agent C: S1.6 utilities, S1.3 support (analysis models)
- Agent D: S1.7 test infra, S1.1 support (README, docs)
- Exit: Epic 01 >= 80% complete

### Phase 2: Collection + Analysis (approx Cycle 006 — 015)
- Agent A: Epic 01 remaining + support
- Agent B: Epic 02 collection engine (lead)
- Agent C: Epic 03 analysis engine (lead)
- Agent D: Epic 09 dashboard shell (early start)
- Exit: Epic 02 + 03 >= 80%

### Phase 3: Scoring (approx Cycle 016 — 022)
- Agent C: Epic 04 scoring system (lead)
- Exit: Epic 04 >= 80%

### Phase 4: Recommendations + Pricing (approx Cycle 023 — 030)
- Agent A: Epic 06 pricing engine
- Agent C: Epic 05 recommendations (lead)
- Agent D: Epic 08 playbook + Epic 09 widgets
- Exit: Epic 05 + 06 >= 80%

### Phase 5: Discovery (approx Cycle 031 — 037)
- Agent B: Epic 07 discovery collection
- Agent C: Epic 07 discovery analysis (lead)
- Exit: Epic 07 >= 80%

### Phase 6: Playbook + Dashboard (approx Cycle 038 — 045)
- Agent D: Epic 08 + 09 (lead)
- Exit: Epic 08 + 09 >= 80%

### Phase 7: Integration (approx Cycle 046 — 055)
- Agent A: Epic 10 orchestrator, integration tests (lead)
- All agents: E2E tests
- Exit: All epics 100%, full test suite green

---

## Velocity Tracking

| Cycle | Planned | Completed | Velocity | Notes |
|---|---|---|---|---|
| (filled each cycle) | | | | |

## Estimated Timeline
- ~55 cycles at 25 tasks/cycle average
- At 1-2 cycles per day: 4-8 weeks to complete
