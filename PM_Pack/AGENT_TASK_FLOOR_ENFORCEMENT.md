# AGENT TASK FLOOR ENFORCEMENT -- NEVER-BREAK HARD RULE
# Fiverr Research System | Created 2026-06-09
# This rule cannot be waived for any reason.

## THE RULE
Every agent prompt MUST contain >= 55 tasks, every task qualifying as
LARGE, XLARGE, or XXLARGE under the 6-dimension scoring matrix.

## ROOT CAUSE OF 2026-06-09 VIOLATION (commit 1428a92)
Actual LARGE+ task counts at 1428a92:
  A: 39 tasks, ~24 LARGE+ -- FAILED (need 55)
  B: 34 tasks, ~23 LARGE+ -- FAILED (need 55)
  E: 53 tasks, ~40 LARGE+ -- FAILED (need 55)
  C: 57 tasks, ~47 LARGE+ -- marginal quality
  F: 43 tasks, ~34 LARGE+ -- FAILED (need 55)
  D: 62 tasks, ~46 LARGE+ -- marginal quality

Root causes:
  1. No task-count verification loop during prompt writing.
  2. Planning/observation/gate tasks counted as LARGE when structurally SMALL.
  3. No enforcement mechanism inside the prompt-writing workflow.

## WHAT QUALIFIES AS LARGE BY AGENT ROLE

AGENT A (Planning): LARGE requires a SPEC ARTIFACT with:
  complete API contract, acceptance criteria, test requirements,
  failure mode analysis, named output file, production-readiness connection.
  SMALL: read file, verify import, golden parity run, gap check, git pull,
  Jira note, SHA recording, config check, test suite run, status report.

AGENT B (Implementation): LARGE requires implementing a function/class/module,
  writing a test class, adding a CLI command, connecting two subsystems,
  writing integration tests, implementing error handling paths.
  SMALL: git pull, file existence check, SHA recording, Jira note.

AGENT E (Observation): LARGE requires a PRODUCTION VALIDATION PROBE that:
  runs actual code, records specific measured values in E.md,
  has acceptance criteria, uses E.md as durable artifact,
  catches real production failure modes.
  SMALL: import X print PASS, check file exists, basic assert, git pull.

AGENT C (Quality Gates): LARGE requires a PRODUCTION VALIDATION PROBE that:
  runs code with test data, records measured values, has remediation path.
  SMALL: basic assert importable, CLI help check, file existence.

AGENT F (Edge Cases): LARGE requires an actual test implementation with:
  setup, execute, assert, cleanup, covering a real production failure mode.
  SMALL: golden parity after F, baseline check after F, test count check.

AGENT D (Merge Gate): LARGE requires integration verification with:
  durable artifact and acceptance criterion that blocks merge on failure.
  SMALL: SHA recording, push to origin, Jira comment, branch creation.

## MANDATORY ENFORCEMENT MECHANISM
A must run this check as TASK 1 before authorizing B:

  import re
  floors = {'A':55,'B':55,'E':55,'C':55,'F':55,'D':55}
  for ag in ['A','B','E','C','F','D']:
      content = open(f'PM_Pack/03_cursor_agent_system/CYCLE_NNN_AGENT_{ag}_PROMPT.md').read()
      count = len(re.findall(r'## (?:TASK|GATE) \d', content))
      assert count >= floors[ag], f'HARD STOP: Agent {ag} = {count} tasks (need {floors[ag]})'
      print(f'Agent {ag}: {count} tasks PASS')

If any agent fails the check: HALT. Fix the prompt. Never proceed with under-count.

## NEVER-BREAK ENFORCEMENT
This requirement is absolute:
  Cannot be waived for time pressure.
  Cannot be waived for simplicity.
  Cannot be waived because a role 'does not lend itself to large tasks'.
  Cannot be satisfied by padding SMALL tasks with verbose wording.
  Cannot be satisfied by repeating verification tasks under different names.
If 55 genuine LARGE tasks cannot be written: cycle is under-scoped.
Redesign the cycle with higher-impact work before generating prompts.

## PER-CYCLE CHECKLIST
Before releasing any agent prompt package, verify:
  [ ] Agent A: >= 55 LARGE tasks (each a named spec artifact)
  [ ] Agent B: >= 55 LARGE tasks (each a production implementation unit)
  [ ] Agent E: >= 55 LARGE tasks (each a production validation probe)
  [ ] Agent C: >= 55 LARGE tasks (each a full production gate with remediation)
  [ ] Agent F: >= 55 LARGE tasks (each an edge case test implementation)
  [ ] Agent D: >= 55 LARGE tasks (each an integration verification)
  [ ] Run the enforcement script above, confirm all 6 PASS
  [ ] Commit only after all 6 pass