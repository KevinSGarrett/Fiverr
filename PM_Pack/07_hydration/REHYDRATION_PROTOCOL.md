# REHYDRATION PROTOCOL
# How to recover full context from the PM Pack after context loss

---

## When to Use This
- New conversation/session started
- PM Pack zip sent to a fresh ChatGPT window
- PM cannot recall project state
- Human says "start fresh" or "rehydrate"

---

## Full Rehydration Sequence (load in this exact order)

### Step 1: Identity and Rules (load once per session)
1. Read 00_index/MASTER_INDEX.md — understand pack structure
2. Read 01_pm_instructions/PM_ROLE.md — know who you are
3. Read 01_pm_instructions/PM_RULES.md — know your rules (74 rules)

### Step 2: Current State (load every cycle)
4. Read 07_hydration/HYDRATION_HEADER.md — compact state overview
5. Read 07_hydration/STATE_SNAPSHOT.md — full project state
6. Read 08_task_queue/EPIC_STATUS_TRACKER.md — epic completion %

### Step 3: Recent History (understand what happened)
7. Read the latest file in 10_cycle_log/ — what happened last cycle
8. Read the second-latest cycle log — for two-cycle context

### Step 4: Planning Context (prepare for this cycle)
9. Read 08_task_queue/CYCLE_PLANNER.md — how to select tasks
10. Read 08_task_queue/DEPENDENCY_MAP.md — what depends on what
11. Read 03_cursor_agent_system/AGENT_ROSTER.md — agent ownership

### Step 5: Operational Rules (have ready for use)
12. Read 03_cursor_agent_system/PROMPT_TEMPLATE.md — for generating prompts
13. Read 02_cycle_protocol/CYCLE_WORKFLOW.md — for following the process
14. Read 01_pm_instructions/PM_REPLY_CHECKLIST.md — for validating output

---

## Quick Rehydration (for minor drift, not full context loss)
1. Read HYDRATION_HEADER.md
2. Read STATE_SNAPSHOT.md
3. Read latest CYCLE_LOG entry
4. Proceed with cycle

---

## Token Budget for Rehydration

| Step | Estimated Tokens | Required |
|---|---|---|
| HYDRATION_HEADER.md | ~400 | Always |
| STATE_SNAPSHOT.md | ~600 | Always |
| Latest CYCLE_LOG | ~500 | Always |
| PM_RULES.md | ~1200 | First cycle of session |
| PROMPT_TEMPLATE.md | ~800 | When generating prompts |
| Spec files (on demand) | ~500-2000 each | Only when referenced |

**Quick rehydration: ~1,500 tokens | Full rehydration: ~5,000-8,000 tokens**

---

## Post-Rehydration Verification
After rehydrating, the PM must answer:
1. What cycle number are we on?
2. Which epics are active?
3. What was done last cycle?
4. What are the blockers?
5. What should we build this cycle?

If the PM cannot answer all 5, the rehydration is incomplete — load more files.
