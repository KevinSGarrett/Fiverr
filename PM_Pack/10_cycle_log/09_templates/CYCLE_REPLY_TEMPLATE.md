# CYCLE REPLY TEMPLATE
# The PM must follow this structure for every reply

---

```
============================================================
CYCLE {NNN} — {DATE}
Focus: {Primary epic(s) and phase}
Branch: cycle/{NNN}/integration
============================================================

## 1. REVIEW OF PRIOR AGENT WORK (Cycle {NNN-1})

### Agent A — {Role}
- Tasks reviewed: {list}
- Confidence: {score}/100
- Issues: {none | list}
- Rework needed: {none | list}

### Agent B, C, D — {same structure each}

### Review Summary
| Agent | Confidence | Tasks Done | Rework |
|---|---|---|---|
| A | {score} | {N} | {N} |
| B | {score} | {N} | {N} |
| C | {score} | {N} | {N} |
| D | {score} | {N} | {N} |

---

## 2. JIRA BOARD UPDATE

### Status Changes
| Ticket | Old Status | New Status | Comment |
|---|---|---|---|
| T{n}.{n}.{n} | {old} | {new} | [Cycle {NNN}] {details} |

### New Tickets Created
| Ticket | Type | Summary | Priority |
|---|---|---|---|
| {ID} | Bug/Task | {description} | P{N} |

### Epic Progress
| Epic | Previous | Current | Delta |
|---|---|---|---|
| 01 | {N}% | {N}% | +{N}% |

---

## 3. CYCLE {NNN} PLAN

| Agent | Tasks | Epic | Story |
|---|---|---|---|
| A | T{list} | {NN} | S{N}.{N} |
| B | T{list} | {NN} | S{N}.{N} |
| C | T{list} | {NN} | S{N}.{N} |
| D | T{list} | {NN} | S{N}.{N} |

---

## 4. AGENT PROMPTS

### Agent A Prompt
{Full prompt following PROMPT_TEMPLATE.md — >=500 words}

### Agent B Prompt
{Full prompt — >=500 words}

### Agent C Prompt
{Full prompt — >=500 words}

### Agent D Prompt
{Full prompt — >=500 words}

---

## 6. STATE UPDATE
- STATE_SNAPSHOT.md: {what changed}
- EPIC_STATUS_TRACKER.md: {what changed}
- CYCLE_LOG: CYCLE_{NNN}.md created

## 7. NEXT CYCLE PREVIEW
Cycle {NNN+1} will focus on: {description}

============================================================
END OF CYCLE {NNN}
============================================================
```


## 4. GITHUB OPERATOR WORKFLOW — REQUIRED EVERY CYCLE

### Branch Creation
```bash
cd C:\Fiverr
git checkout develop
git pull origin develop
git checkout -b cycle/{NNN}/integration
```

### Sequential Agent Commit Order
1. Run Agent A prompt, then commit Agent A files only.
2. Run Agent B prompt, then commit Agent B files only.
3. Run Agent C prompt, then commit Agent C files only.
4. Run Agent D prompt, then commit Agent D files only.

### Push After All Agents Complete
```bash
git status
git push -u origin cycle/{NNN}/integration
```

### Pull Request
- Source: `cycle/{NNN}/integration`
- Target: `develop`
- Title: `feat(cycle-{NNN}): {summary}`
- Merge: squash merge only after PM approval and green CI.
- Main: do not push or merge to `main`; `main` is promoted only by release PR from `develop` after release gates pass.

## 5. AGENT PROMPTS

### Agent A Prompt
```text
{Full prompt using PROMPT_TEMPLATE.md}
```