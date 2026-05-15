# CYCLE 001 CORRECTIVE REVIEW — PROMPT DEPTH AND GITHUB WORKFLOW

Date: 2026-05-13
Related Jira: SCRUM-246
Status: Corrective guardrails added to PM Pack

## What Went Wrong

Cycle 001 generated prompts that were too short and assigned too few tasks compared with the intended high-substance autonomous Cursor execution standard. The prompts followed the old mechanical template floor, but they did not satisfy Kevin's expected quality bar for detailed, lengthy, high-context agent instructions.

## Root Cause

The PM Pack contained a conflict:

- `PROMPT_TEMPLATE.md` allowed a prompt with **minimum 3 tasks** and **>=500 words**.
- `TASK_SIZING.md` stated the real target was **5-8 tasks per agent** and high-volume execution.

The PM incorrectly treated the lower floor as acceptable instead of enforcing the higher target. The cycle reply also failed to print the full GitHub operator workflow even though the GitHub protocol files contained it.

## Binding Corrections

1. Every active agent prompt must contain at least **5 substantive tasks**, target **6-8**.
2. Every active agent prompt must be at least **1,500 words**, target **2,000-3,500**.
3. Every implementation task must include exact files, exact method/class/function expectations, edge cases, validation behavior, test names, DOD references, and source references.
4. Every cycle reply must include a dedicated **GitHub Operator Workflow** section.
5. The workflow must state: agents do not push to main; the human pushes `cycle/{NNN}/integration`; PR goes to `develop`; `main` is promoted only by approved release PR after release gates pass.
6. A prompt with fewer than 5 tasks requires explicit `TASK-COUNT WAIVER`, reason, risk, and next-cycle backfill plan.

## Main Branch Strategy

Cursor agents do not push to `main`. In normal cycles, they should not push at all. They commit locally on `cycle/{NNN}/integration`. Kevin/human operator pushes the cycle branch once after all four agents complete. The PR targets `develop`. `main` is updated only at release checkpoints by a separate `develop -> main` PR after PM review, CI, QA gates, and release approval.

First planned main promotion: Foundation Release `v0.1.0`, after Epic 01 release gates pass.

## Files Updated

- `03_cursor_agent_system/PROMPT_TEMPLATE.md`
- `03_cursor_agent_system/PROMPT_RULES.md`
- `03_cursor_agent_system/TASK_SIZING.md`
- `01_pm_instructions/PM_REPLY_CHECKLIST.md`
- `02_cycle_protocol/PR_BATCH_STRATEGY.md`
- `05_github_protocol/BRANCH_WORKFLOW.md`
- `05_github_protocol/GITHUB_RULES.md`
- `09_templates/CYCLE_REPLY_TEMPLATE.md`

## Non-Negotiable PM Rule Going Forward

Passing the mechanical checklist is not enough. Before sending any cycle reply, the PM must verify that the prompts are genuinely production-grade, long-form, detailed, and execution-ready for autonomous Cursor agents.
