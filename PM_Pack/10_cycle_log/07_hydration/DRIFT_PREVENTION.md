# DRIFT PREVENTION
# Rules to detect and correct PM drift before it causes problems

---

## What Is Drift?
Drift occurs when the PM gradually loses alignment with the project plan, introduces inaccuracies, skips processes, or makes decisions inconsistent with established rules.

---

## 10 Drift Signals (If ANY appear, run correction protocol)

| # | Signal | How to Detect |
|---|---|---|
| 1 | PM cannot state the current cycle number | If unsure, drift has occurred |
| 2 | PM assigns tasks from wrong epic or phase | Cross-check EPIC_STATUS_TRACKER + CYCLE_PLANNER |
| 3 | PM generates prompts without following template | Missing sections, under 500 words, no spec refs |
| 4 | PM skips Jira updates or provides incomplete updates | Check JIRA_UPDATE_CHECKLIST compliance |
| 5 | PM assigns overlapping files to multiple agents | Check FILES CREATED tables across all 4 prompts |
| 6 | PM marks tasks done without verifying tests | Check QA_GATES compliance |
| 7 | PM references files or specs that don't exist | Verify paths against REF_INDEX.md |
| 8 | PM contradicts prior cycle decisions | Check CYCLE_LOG for consistency |
| 9 | PM gives different task counts than TASK_BACKLOG shows | Compare stated progress vs actual |
| 10 | PM generates vague prompts after previously detailed ones | Compare to PROMPT_RULES standards |

---

## Drift Correction Protocol

### Immediate Actions (run if drift detected)
1. STOP — Do not send the current reply
2. Re-read HYDRATION_HEADER.md in full
3. Re-read STATE_SNAPSHOT.md in full
4. Re-read the latest CYCLE_LOG entry
5. Verify the current cycle number
6. Verify which epics are active and which phase we're in
7. Re-check TASK_BACKLOG.md for accurate status counts
8. Re-generate the reply from scratch

### Preventive Measures (do EVERY cycle)
1. Always load HYDRATION_HEADER.md first — never skip
2. Always verify cycle number against STATE_SNAPSHOT.md
3. Always cross-reference task selections against DEPENDENCY_MAP.md
4. Always run PM_REPLY_CHECKLIST.md before sending
5. Never rely on memory — always read from pack files
6. If human says something contradicts your understanding, re-read the relevant spec

---

## Drift Risk Factors

| Factor | Risk Level | Mitigation |
|---|---|---|
| Long conversation (many cycles) | High | Hydration header + state snapshot every cycle |
| Context window pressure | High | Modular files, load only what's needed |
| Changing focus (new epic) | Medium | Update HYDRATION_HEADER focus section |
| Agent rework cascading | Medium | Track rework in CYCLE_LOG |
| Human changing requirements | Low | Document in CYCLE_LOG, update specs if needed |
