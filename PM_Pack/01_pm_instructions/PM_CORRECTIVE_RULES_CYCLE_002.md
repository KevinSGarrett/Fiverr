# PM Corrective Rules — Cycle 002

These rules were added after the operator identified that Cycle 001 corrective handling did not include the next-cycle Cursor prompts.

## Mandatory Rules

1. Every cycle reply must include four Cursor agent prompts unless the operator explicitly says not to generate prompts.
2. A process-correction reply does not replace the next-cycle handoff.
3. Each Cursor prompt must contain 5-8 substantive tasks unless a written TASK-COUNT WAIVER is included.
4. Each prompt must include exact file ownership, no-overlap rules, validation commands, and commit instructions.
5. Every cycle reply must include the GitHub workflow: source branch, cycle branch, per-agent commit order, push command, PR target, merge strategy, and main-branch policy.
6. No Cursor agent pushes directly to main. Main is release-only after approved release gates.
7. Short prompts that technically exceed 500 words are still rejected if they lack implementation substance.

## Active PM Process Issue

SCRUM-246 — [PM PROCESS] Cycle 001 prompts lacked required depth and PR workflow detail.
