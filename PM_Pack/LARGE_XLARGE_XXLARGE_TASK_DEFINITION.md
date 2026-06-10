# LARGE, XLARGE, XXLARGE TASK DEFINITIONS
# Fiverr Research System PM Governance Correction 2026-06-09

## CORE PRINCIPLE
A task size is determined by its production impact, not by word count or checklist length.
A 500-word task description of checking an import is SMALL.
A 30-word task that implements a live collection stop condition is LARGE.

## WHAT IS NOT LARGE BY DEFAULT
These are SMALL or MEDIUM unless attached to a meaningful production outcome:
  Verify file exists | Check import | Run smoke test | Update report
  Add comment | Post Jira note | Confirm no changes | Check line count
  Confirm config value | Repeat golden parity | Observe current state
  Write summary | Update hydration | Create handoff | Restate known issue

## LARGE TASK DEFINITION
A LARGE task must satisfy ALL:
  1. Changes, builds, validates, or integrates a production subsystem
  2. Has a durable artifact (code, test, migration, CLI behavior, pipeline)
  3. Has clear acceptance criteria
  4. Has objective evidence
  5. Maps to a production-readiness category
  6. Is not merely repeated verification
  7. Would still matter if task counts were ignored

LARGE examples:
  Implement PilotLogger that logs ScrapFly requests to JSONL with stop conditions
  Add collect-live CLI command with budget ceiling and niche scoping
  Connect live collection output to scoring pipeline via run.py live-validate
  Build generate_playbook() with 5 sections, graceful empty-state, Wave 11 S8.3

LARGE non-examples:
  Verify pilot_logger.py exists | Check PilotLogger imports | Write notes about playbook

## XLARGE TASK DEFINITION
An XLARGE task must satisfy ALL LARGE criteria plus at least two of:
  1. Touch multiple files or modules
  2. Integrate at least two subsystems
  3. Close a full story acceptance criterion
  4. Add tests across more than one behavior
  5. Produce user/operator-visible functionality
  6. Reduce a major production blocker
  7. Advance an end-to-end production workflow
  8. Convert a stubbed path into working path

XLARGE examples:
  Build TierD-2 pilot orchestrator (live_pilot.py): one niche, cost ceiling, DB seed,
    run_collection_pipeline(dry_run=False), stop conditions, evidence bundle
  Connect recommendations -> playbook: has_full_data=True path with tests

## XXLARGE TASK DEFINITION
An XXLARGE task must satisfy ALL XLARGE criteria plus at least one of:
  1. Prove a full end-to-end workflow
  2. Close a major production-readiness blocker
  3. Make a major operator capability usable
  4. Enable a repeated unattended run
  5. Validate live data through downstream outputs
  6. Advance E2E Production-Grade Readiness by a measurable amount

XXLARGE examples:
  Live collection -> DB persistence -> scoring -> recommendations -> playbook -> evidence
  First production-grade playbook from live scored recommendation
  Resume/checkpoint recovery for interrupted live collection with zero data loss

## 6-DIMENSION TASK SCORING MATRIX
Score each task 0-5 on:
  1. Production Outcome Score: 0=none ... 5=direct E2E advancement
  2. Complexity/Substance Score: 0=filler ... 5=XLARGE/XXLARGE
  3. Integration Depth Score: 0=isolated ... 5=end-to-end workflow
  4. Evidence Strength Score: 0=none ... 5=live/E2E evidence
  5. Novelty/Non-Duplication Score: 0=duplicate ... 5=new critical work
  6. End-to-End Readiness Score: 0=no impact ... 5=proves production path

Classification:
  SMALL: total < 16 or any core category < 3
  MEDIUM: total 16-21
  LARGE: total 22-25, no category below 4 (except Novelty can be 3)
  XLARGE: total 26-28, Production/Integration/Evidence all >= 4
  XXLARGE: total 29-30, or closes major production gate with E2E evidence

HARD REJECTION: Task cannot be LARGE/XLARGE/XXLARGE if:
  Production Outcome Score < 4 | Evidence Strength < 3
  End-to-End Readiness < 3 | It is a duplicate verification task
  It has no durable artifact | It has no acceptance criteria
  It exists to satisfy task count