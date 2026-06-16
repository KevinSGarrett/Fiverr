# ADR 028: Autonomous Stage Execution

## Status
Accepted ? Cycle 082

## Context
Stages 2-7 are the production go-live proving sequence. Manual advancement creates latency and introduces unnecessary human bottlenecks.

## Decision
- Stage 2-7 execution is automated through `automation/stage_executor.py`.
- Stage advancement criteria are evidence-based and encoded in stage evidence artifacts.
- Stage 2 -> 3: single-agent docs-safe dispatch completes with AGENT_COMPLETE.
- Stage 3 -> 4: full six-agent cycle completes and PR opens.
- Stage 4 -> 5: failure injection + repair loop succeeds and merge evidence is produced.
- Stage 5 -> 6: post-cycle review succeeds and next-cycle prompts are generated.
- Stage 6 -> 7: one unattended 24h cycle completes with no crashes/main pushes/stuck agents.
- Stage 7 complete: seven consecutive clean daily reports and aggregate trial evidence.

## Claude PM Review Model
`DAILY_STAGE_REPORT.json` is generated daily. During stages 6-7, Kevin only needs to upload this file once per day to Claude PM and read the assessment. No human approval is required for stage transitions in stages 2-5.

## Consequences
- Faster and consistent stage progression.
- Objective criteria for promotion between stages.
- Human role reduced to daily report handoff during observation windows.
