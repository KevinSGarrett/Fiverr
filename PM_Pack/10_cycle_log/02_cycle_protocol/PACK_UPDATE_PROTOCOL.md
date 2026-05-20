# PACK UPDATE PROTOCOL
# Rules for updating the PM Pack every cycle

---

## Files Updated EVERY Cycle (mandatory)

| File | What Changes |
|---|---|
| 07_hydration/STATE_SNAPSHOT.md | Current epic/story/task status, focus area, blockers |
| 08_task_queue/EPIC_STATUS_TRACKER.md | Completion percentages for all epics and stories |
| 10_cycle_log/CYCLE_{NNN}.md | New entry for this cycle |

## Files Updated WHEN RELEVANT

| File | When |
|---|---|
| 07_hydration/HYDRATION_HEADER.md | When focus area changes (new epic starts) |
| 08_task_queue/TASK_BACKLOG.md | When task statuses change |
| 08_task_queue/DEPENDENCY_MAP.md | When new dependencies discovered |

## Files NEVER Modified

| File | Why |
|---|---|
| ref/**/* | Reference library is read-only |
| 01_pm_instructions/PM_RULES.md | Rules are fixed |
| 03_cursor_agent_system/PROMPT_TEMPLATE.md | Template is fixed |

## Update Process
1. Make all changes in-memory
2. Verify consistency (TASK_BACKLOG status matches EPIC_STATUS_TRACKER)
3. Document what changed in the CYCLE_LOG entry
4. Instruct human: "Zip C:\Fiverr1\Project_Manager\ as PM_Pack_Cycle_{NNN}.zip"
