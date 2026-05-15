# CYCLE WORKFLOW
# 8-phase step-by-step process for every development cycle

---

## Phase 1: INGEST (PM reads the pack)
1. Human sends PM_Pack_Cycle_{N-1}.zip (or initial pack for Cycle 001)
2. PM loads HYDRATION_HEADER.md — restore context
3. PM loads STATE_SNAPSHOT.md — know current state
4. PM loads latest CYCLE_LOG entry — know what happened last
5. PM checks if human provided agent work results to review

## Phase 2: REVIEW (PM reviews prior agent work)
6. If prior agent work exists:
   a. PM reviews each agent's work against their prompt and DOD
   b. PM runs QA gates (06_review_and_qa/QA_GATES.md)
   c. PM assigns confidence scores (0-100) per agent
   d. PM identifies rework needs
   e. PM updates task status in TASK_BACKLOG.md
7. If no prior work (Cycle 001): skip to Phase 3

## Phase 3: PLAN (PM decides what to build)
8. PM runs board-first Jira inventory before selecting code work (FULL_BOARD_AC_DOD_FIRST_PROTOCOL.md)
9. PM selects exact Jira issues and AC/DoD bullets before task drafting
10. PM loads CYCLE_PLANNER.md and DEPENDENCY_MAP.md
11. PM selects tasks for each agent (respecting dependencies + ownership)
12. PM verifies no file overlap between agents
13. PM determines integration branch name: cycle/{NNN}/integration

## Phase 4: GENERATE (PM creates agent prompts)
13. PM loads PROMPT_TEMPLATE.md
14. PM generates Agent A prompt following the template exactly
15. PM generates Agent B prompt following the template exactly
16. PM generates Agent C prompt following the template exactly
17. PM generates Agent D prompt following the template exactly
19. PM validates each prompt against PROMPT_RULES.md (>=6,000 words unless dual-waived, 20-40 tasks per agent, AC/DoD per task, Jira responsibility explicit, all sections present)

## Phase 5: JIRA UPDATE (PM updates the board)
20. PM loads JIRA_UPDATE_CHECKLIST.md and CURSOR_AGENT_JIRA_OPERATIONS_PROTOCOL.md
21. PM updates all ticket statuses and may assign Cursor agents explicit Jira operations when needed
22. PM adds comments with cycle info, branch, and agent assignment
23. PM creates new tickets for discovered issues/bugs/rework
24. PM updates epic progress percentages
25. PM records AC/DoD progress ledger entries for touched tickets

## Phase 6: STATE UPDATE (PM updates the pack)
26. PM updates STATE_SNAPSHOT.md with current state
27. PM updates EPIC_STATUS_TRACKER.md with completion percentages
28. PM creates CYCLE_{NNN}.md entry in 10_cycle_log/
29. PM updates HYDRATION_HEADER.md if focus area shifted

## Phase 7: VALIDATE (PM checks reply)
30. PM runs PM_REPLY_CHECKLIST.md (all gates)
31. PM checks for uncommitted local work not represented in live PR
32. PM fixes any failures
33. PM confirms reply is ready

## Phase 8: DELIVER
34. Reply includes: review results, board audit findings or scope limits, Jira updates, 4 agent prompts, state summary, next cycle preview
35. Human executes agent prompts in Cursor (A then B then C then D sequentially)
36. Human pushes code, creates PR
37. Human reports results — next cycle begins

---

## Visual Flow
```
Human sends pack -> INGEST -> REVIEW prior work -> PLAN next tasks
     -> GENERATE 4 prompts -> UPDATE Jira -> UPDATE state -> VALIDATE reply -> DELIVER
          -> Human runs 4 agents -> reports back -> next cycle
```
