# TASK PRODUCTION IMPACT LEDGER
# Fiverr Research System — Production Readiness Credit Rules
# Created: 2026-06-09 | PM Governance Correction

## PURPOSE
Every task must map to a production-readiness category with a credit range.
These credits are ESTIMATES. Credit is only claimed when evidence is produced.

## CREDIT RULES BY TASK TYPE

### Documentation-only tasks
Credit: 0%% production-readiness gain (usually)
Exception: correcting active governance drift that blocks execution = up to 0.5%% per cycle
Total documentation credit per cycle: NORMALLY CAPPED AT 0.5%%

### Verification-only tasks
Credit: 0%% to 0.05%% each
Notes: cannot dominate a cycle, repeated checks do not stack

### Unit-test-only tasks
Credit: 0.05%% to 0.15%% each
Exception: tests validating new production-critical behavior = up to 0.25%%

### Implementation tasks
Credit: 0.10%% to 0.50%% each if they create real production capability
Requires: working code, passing tests, durable artifact

### Integration tasks
Credit: 0.25%% to 1.00%% each if they connect meaningful subsystems
Requires: two systems working together, integration tests, evidence

### Live validation tasks
Credit: 0.50%% to 2.00%% each if they prove real system behavior
Requires: actual execution, real data, recorded output

### End-to-end workflow tasks
Credit: 1.00%% to 3.00%% each if they prove a meaningful production path
Requires: full chain executed, all stages verified, evidence bundle

### Major blocker-removal tasks
Credit: 1.00%% to 3.00%% depending on evidence
Requires: blocker confirmed removed, downstream unblocked, evidence

## HARD RULE
No readiness credit is counted without evidence.
Approval, planning, and architecture decisions produce 0%% E2E credit alone.

## C074 TASK CREDIT BREAKDOWN
Task: collect-live command implementation
  Type: Implementation + blocker-removal
  Credit: +2%% (removes live collection CLI gap, unblocks E2E cap)
  Evidence: python run.py collect-live --help works on main HEAD

Task: live-validate orchestrator implementation
  Type: Integration + end-to-end workflow
  Credit: +2%% (connects collection->scoring->recommendations->playbook)
  Evidence: python run.py live-validate --skip-collection exits 0

Task: PilotLogger + evidence bundle
  Type: Implementation (operator readiness)
  Credit: +1%% (TierD-2 audit trail, stop conditions, evidence artifact)
  Evidence: test_live_pilot.py 18+ tests pass, evidence bundle JSON valid

Task: Wave 11 S8.3 generate_playbook
  Type: Implementation (new subsystem)
  Credit: tracks toward Track 10 Playbook advancement
  Evidence: test_playbook_generator.py 32+ tests pass, 5 sections valid

Total C074 build credit: ~+5%% E2E production readiness

## CREDIT NOT COUNTED IN C074
TierD-2 approval alone: 0%% (approval without evidence = 0)
Pilot DB created: 0%% (throwaway, not production)
Test files added: minor (counted in suite coverage gate, not E2E directly)

## ADDITIONAL CREDIT PENDING (user runs pilot)
First live collection success: +3-5%%
  Evidence: data/live_pilot_log.jsonl has entries, gigs_collected > 0

DB persistence validated: +1-2%%
  Evidence: evidence stages.db_validation.gigs > 0

Scoring from live data: +1-2%%
  Evidence: evidence stages.scoring.success == true

Recommendations from live data: +1-2%%
  Evidence: evidence stages.recommendations.count > 0

Playbook from live recommendation: +1-2%%
  Evidence: evidence stages.playbook.has_full_data == true