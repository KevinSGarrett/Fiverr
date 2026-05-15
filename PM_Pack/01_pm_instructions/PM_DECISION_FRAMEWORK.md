# PM DECISION FRAMEWORK
# How the PM makes decisions about priority, sequencing, scope, and risk

---

## Decision 1: What to Build Next

### Priority Order
1. **Blockers first** — Anything blocking other agents takes P1
2. **Foundation before features** — Epic 01 must complete before Epics 02-09
3. **Dependencies respected** — Check DEPENDENCY_MAP.md before assigning
4. **Parallel where possible** — Assign independent work to all 4 agents simultaneously
5. **Epic order** — Follow the macro sequence below
6. **Within an epic** — Follow story number order (S1.1 then S1.2 then S1.3)

### Epic Sequencing (7 Phases)
| Phase | Epics | Why | Agents |
|---|---|---|---|
| 1 | Epic 01 (Foundation) | Everything depends on config, models, CLI | A (lead) + B,C,D (support) |
| 2 | Epic 02 + 03 | Collection feeds analysis, agent-isolated | B + C |
| 3 | Epic 04 (Scoring) | Requires analysis models | C (lead) |
| 4 | Epic 05 + 06 | Both use scoring output, parallelizable | C + A |
| 5 | Epic 07 (Discovery) | Requires full pipeline | C (lead) + B |
| 6 | Epic 08 + 09 | Presentation layer | D (lead) + A |
| 7 | Epic 10 (Integration) | Final wiring + testing | A (lead) + all |

---

## Decision 2: How Much Work Per Cycle

### Target Velocity
| Metric | Target | Maximum |
|---|---|---|
| Tasks per agent | 24-32 | 40 |
| Minimum tasks per agent | 20 | 20 |
| Total tasks per cycle | 96-128 | 160 |
| Estimated agent time | 1-2 hours | 4 hours |
| New files per agent | 3-8 | 15 |

### Scope Adjustment Triggers
| Signal | Action |
|---|---|
| Agent produced errors last cycle | Reduce scope 30%, add rework tasks |
| Agent completed everything cleanly | Increase scope 20% next cycle |
| Multiple agents blocked by same dep | Focus all agents on unblocking |
| Human reports slowness | Reduce total tasks, increase depth |

---

## Decision 3: How to Handle Risks

| Risk Level | Criteria | PM Action |
|---|---|---|
| Low | Tests, docs, config changes | Agent self-verifies, PM spot-checks |
| Medium | New features within established patterns | PM reviews DOD, runs QA gates |
| High | New workflows, scoring formulas, LLM prompts | PM deep-reviews, human review recommended |
| Critical | Schema migration, orchestrator, security | PM blocks merge until human confirms |

---

## Decision 4: When to Split or Combine Work

### Split When
- Story has >15 tasks — split across cycles
- Agent prompt would become unsafe/unclear above preferred range; use structure before reducing depth
- Work touches files owned by multiple agents — split by ownership

### Combine When
- Multiple small tasks touch the same file — group for one agent
- Related tests can be written together — group test tasks
- Config changes affect multiple modules — single agent handles all config
