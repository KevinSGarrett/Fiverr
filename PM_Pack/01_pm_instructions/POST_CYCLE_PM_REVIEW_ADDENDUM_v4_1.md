## PART 7 LINE FLOOR UPDATE (v4.1 — 2026-06-01)

REVISED PROMPT LENGTH MINIMUMS (§12.5 of AGENT_EXECUTION_STRATEGY.md — effective C057+):
  A>=500, B>=650, E>=500, C>=425, F>=525, D>=650 | TOTAL >= 3,250

This replaces the prior floors: A810/B945/E810/C675/F810/D945 = 4,995 total.
Root cause of change: prior floors caused excessive padding without improving agent
performance, and took excessive generation time. New floors calibrated to what 25
LARGE-XXXLARGE tasks with full inline content actually require.

DEPTH QUALITY GATE (§12.5 — supplements line counting):
Every prompt must pass ALL 7 of these checks before release:
  1. LINE FLOOR: meets the per-agent floor above
  2. TASK COUNT: ≥25 tasks, each LARGE-XXXLARGE with numbered sub-steps
  3. SPECIFICITY: every task names ≥1 specific file, command, Jira key, or function
  4. NO DUPLICATION: no two consecutive tasks share the same command structure
  5. INLINE CONTENT: code/command/report templates are INLINE (not "go read X")
  6. STAGE CORRECTNESS: agent prerequisites match §12.2 exactly (C before F, not after)
  7. OPERATIONAL COMPLETENESS: D's prompt contains §12.3 operational issues playbook

A prompt at/above floor but failing any depth check = NOT DONE.
A prompt slightly below floor but passing all depth checks = acceptable if PM documents why.

PARALLEL EXECUTION RULE (§12.1 — MANDATORY IN ALL B AND E PROMPTS):
Both B and E prompts MUST contain the §12.1 parallel execution notice at the top:
  "YOU ARE RUNNING IN PARALLEL WITH AGENT [X]. [X]'s commits WILL appear in git log.
   This is EXPECTED. DO NOT halt or alarm."
Zone verification in parallel mode: use `git show --name-only <OWN_SHA>` ONLY.
NEVER use `git diff --name-only origin/develop..HEAD` — shows other agent's commits.

STAGE ORDER RULE (§12.2 — verified in every prompt):
A → B+E (parallel) → C → F → D
Agent C prerequisite: B AND E only. C NEVER waits for F.
Agent F prerequisite: C's GO verdict.
Agent D prerequisite: all 5 agents complete.
Any prompt listing F as a C prerequisite is WRONG — fix it before releasing.

OPERATIONAL ISSUES PLAYBOOK (§12.3 — mandatory in Agent D prompt):
D's prompt must include procedures for:
  - PR too large (>1000 lines): override:large-pr label command
  - Codex thread resolution: reply + resolve (GraphQL or UI)
  - codecov/patch advisory: document and proceed if project floor passed
  - mergeable_state values: clean/unstable/blocked/unknown
  - CI pending: wait up to 5 minutes, re-query

These items are also required in the Part 8 self-audit checklist below.

