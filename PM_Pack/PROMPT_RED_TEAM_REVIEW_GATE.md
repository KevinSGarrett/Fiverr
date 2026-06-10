# PROMPT RED-TEAM REVIEW GATE
# Fiverr Research System PM Governance Correction 2026-06-09
# Required: PM reviews own prompts as adversary before releasing

## PURPOSE
After drafting prompts, PM performs adversarial self-review to catch filler,
stale state, false-large tasks, and insufficient production advancement.

## QUESTIONS TO ASK (ALL MUST HAVE HONEST ANSWERS)

1. Are any tasks filler?
   Filler = exists to satisfy line/task floor, not production outcome.
   If yes: remove or rewrite. Never fix by adding more words.

2. Are any tasks repeated from prior cycles without new evidence?
   Same import check, same smoke test, same golden parity = SMALL at best.
   If yes: cut to one instance, make it meaningful, or remove.

3. Are any tasks basic verification disguised as LARGE?
   Checking that a file exists with 50 lines of Python is still SMALL.
   If yes: reclassify or bundle into a genuine LARGE integration task.

4. Are any tasks documentation-only counted as XLARGE?
   Writing a report about what was done is SMALL/MEDIUM at best.
   If yes: cut to SMALL, do not count toward LARGE-XXLARGE floor.

5. Are any tasks disconnected from production readiness?
   If removing the task has zero impact on E2E production readiness: remove it.

6. Are any tasks not tied to the cycle +5%% target?
   Every task must contribute to the cycle-level +5%% E2E forecast.
   If yes: either add production outcome or remove the task.

7. Are any tasks based on stale project state?
   Check: does it reference old completion scores, stale wave status, old scores?
   If yes: update or remove.

8. Are any tasks duplicated across agents?
   E and C both verifying the exact same thing with no additional value = redundant.
   If yes: E observes, C gates with acceptance criteria. Never pure duplicates.

9. Are any tasks low-impact but included to satisfy the 55-task floor?
   If the cycle does not have 55 genuine LARGE-XXLARGE tasks: reduce scope or
   redesign the cycle. Do not pad.

10. Are any tasks missing acceptance criteria?
    Every task must state: what passes, what evidence proves it passed.
    If yes: add criteria or remove.

11. Are any tasks missing evidence requirements?
    Every task must say what artifact/output/measurement proves it done.
    If yes: add evidence or remove.

12. Are any agents overloaded with low-value checks?
    E and C are often overloaded with import checks. 70%%+ must be substantive.
    If yes: replace with genuine production-readiness verification.

13. Does the cycle produce real product capability?
    Ask: After this cycle, can the system do something it could not before?
    If no: rescope the cycle.

14. Would this cycle still matter if task count was ignored?
    If the answer is no (it only looks impressive by volume): completely rescope.

15. Does the +5%% E2E forecast hold up to scrutiny?
    Are the claimed credit amounts defensible with evidence?
    Credit requires evidence. Approval does not count as evidence.

## VERDICT
If any answer is unfavorable: fix the prompts before releasing.
Red-team review is complete only when all 15 questions have honest YES answers.

## C074 RED-TEAM RESULT
All 15 questions reviewed for corrected C074 prompts.
Result: PASS
  - No filler tasks (all map to TierD-2 infrastructure or S8.3 scaffold)
  - No repeated verification without new value
  - No documentation counted as LARGE
  - All tasks have acceptance criteria and evidence requirements
  - +5%% E2E forecast is defensible (collect-live/live-validate/logger)
  - Prompts use corrected scorecard and current project state