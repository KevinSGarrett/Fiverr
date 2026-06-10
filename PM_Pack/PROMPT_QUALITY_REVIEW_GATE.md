# PROMPT QUALITY REVIEW GATE
# Fiverr Research System — Required Gates Before Any Cycle Prompt Is Approved
# Created: 2026-06-09 | PM Governance Correction

## GATE PQ-1: PROMPT PRE-FLIGHT SOURCE GATE
Before writing prompts, PM must verify these are current:
  Current cycle number
  Active wave and completed waves
  Single active source of truth (CURRENT_STATE_CANONICAL.md)
  Internal Build Progress score (from PRODUCTION_READINESS_SCORECARD.md)
  E2E Production-Grade Readiness score (same)
  Active blockers (TierD-1, TierD-2, G-D status)
  EPIC_STATUS_TRACKER.md is current (not stale)
  HYDRATION_HEADER.md has no contradictions
  No unresolved placeholders in any active document

FAILURE = prompts may not be generated.

## GATE PQ-2: TASK SUBSTANCE GATE (per task)
Every task must score >= 4 in these dimensions:
  Production Outcome Score: 4+ (direct production capability or blocker reduction)
  Evidence Strength Score: 3+ (test/command evidence minimum)
  End-to-End Readiness Score: 3+ (prerequisite readiness minimum)

Tasks failing ANY dimension are REJECTED as filler.
See TASK_SUBSTANCE_GATE.md for full scoring matrix.

## GATE PQ-3: ANTI-FILLER GATE (per prompt)
Reject any task that is:
  - "Verify file exists" with no production consequence
  - Repeated verification from prior cycle with no new evidence
  - Documentation-only with no production outcome
  - Status update without an associated implementation
  - Line padding to reach floor count
  - Generic import check with no functional verification

Production implementation must be >= 70% of all tasks.
Verification-only tasks must be <= 15%.
Documentation/governance tasks must be <= 10%.

## GATE PQ-4: +5% E2E PRODUCTION ADVANCEMENT GATE (per cycle)
Every cycle must include a production-readiness forecast showing:
  Current E2E score
  Target E2E after cycle
  Minimum expected increase: +5%
  Task groups supporting each score increase
  Evidence needed to claim the increase
  Risks to the increase

If the cycle cannot credibly target +5%, the PM must:
  a. Rescope the cycle around higher-impact work
  b. Request user approval for lower-gain cycle
  c. Convert to blocker-removal cycle with formal exception

## GATE PQ-5: LARGE-XXLARGE CLASSIFICATION GATE (per task)
Every task claimed as LARGE/XLARGE/XXLARGE must pass the definition in
LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md:

LARGE: Changes a production subsystem, has durable artifact, clear acceptance criteria
XLARGE: Satisfies LARGE + integrates 2+ subsystems + advances end-to-end workflow
XXLARGE: Satisfies XLARGE + closes major production gate or proves full E2E path

Tasks are classified by their production impact, not by word count or checklist length.

## GATE PQ-6: NO-STALE-SOURCE GATE
No prompt may reference:
  Completion percentages from before the most recent scorecard correction
  Story status before the most recent EPIC_STATUS_TRACKER update
  Unresolved placeholders from completed cycle logs
  Superseded hydration state

## GATE PQ-7: PROMPT RED-TEAM REVIEW
After drafts are written, PM performs red-team review asking:
  1. Are any tasks filler?
  2. Any tasks repeated from prior cycle without new evidence?
  3. Any tasks basic verification disguised as LARGE?
  4. Any tasks disconnected from production readiness?
  5. Any tasks missing acceptance criteria?
  6. Any tasks missing evidence requirements?
  7. Does the cycle produce real product capability?
  8. Would this cycle matter if task count was ignored?

Any task failing = removed or rewritten before prompts are released.

## APPROVAL RULE
A prompt package is approved ONLY when all 7 gates pass.
See PROMPT_RED_TEAM_REVIEW_GATE.md for gate 7 details.
See LARGE_XLARGE_XXLARGE_TASK_DEFINITION.md for classification details.
