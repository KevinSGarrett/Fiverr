# LIVE VALIDATION MASTER GATE
# Fiverr Research System — Live Collection Validation Requirements
# Created: 2026-06-09 | PM Governance Correction

## PURPOSE
Defines the required stages for live collection validation before production readiness
credits above 50% E2E can be claimed. This gate prevents overcounting ScrapFly/TierD-2
approval as production advancement without evidence.

## VALIDATION STAGES AND CREDIT

### Stage V-1: TierD-2 Approved + Budget Set
Credit: Small unlock only (+0.5% E2E)
Evidence: TierD-2 approval recorded with conditions A-J
Status at C074: EARNED

### Stage V-2: ScrapFly Configured and Smoke-Tested
Credit: +1-2% E2E
Evidence: collect-live command exists, cost_budget_credits enforced, PilotLogger active
Status at C074: EARNED (infrastructure built by B)

### Stage V-3: First Live Collection Succeeds
Credit: +3-5% E2E
Evidence: data/live_pilot_log.jsonl has entries, gigs_collected > 0
Status: PENDING — user must run: python run.py collect-live --niche python_automation

### Stage V-4: Live Data Persists Correctly in DB
Credit: +1-2% E2E
Evidence: data/live_validation_evidence.json shows stages.db_validation.gigs > 0
Status: PENDING — requires V-3 success

### Stage V-5: Live Data Flows Into Scoring
Credit: +1-2% E2E
Evidence: evidence stages.scoring.success == true
Status: PENDING — requires V-4 success

### Stage V-6: Live Data Flows Into Recommendations
Credit: +1-2% E2E
Evidence: evidence stages.recommendations.count > 0
Status: PENDING — requires V-5 success

### Stage V-7: Recommendations Flow Into Playbook
Credit: +1-2% E2E
Evidence: evidence stages.playbook.has_full_data == true
Status: PENDING — requires V-6 success

### Stage V-8: Dashboard/Export/Report Updated With Live Data
Credit: +2-4% E2E
Evidence: data/exports/live_pilot/ has recommendation files
Status: PENDING — requires V-7 success

### Stage V-9: Repeated Unattended Runs Pass
Credit: Full production-readiness credit
Evidence: Multiple live-validate runs passing without manual intervention
Status: FUTURE — requires all previous stages

## CREDIT SUMMARY TABLE
Stage | Requirement | E2E Credit | Status (C074)
V-1   | TierD-2 approved | +0.5% | EARNED
V-2   | Infrastructure built | +1-2% | EARNED (C074)
V-3   | First live collection | +3-5% | PENDING
V-4   | DB persistence | +1-2% | PENDING
V-5   | Scoring from live | +1-2% | PENDING
V-6   | Recommendations | +1-2% | PENDING
V-7   | Playbook from live | +1-2% | PENDING
V-8   | Dashboard/export | +2-4% | PENDING
V-9   | Repeated runs | Full credit | FUTURE

## HARD CAP RULES
- Without V-3: E2E cannot exceed 50%
- Without V-5: E2E cannot exceed 60%
- Without V-6: E2E cannot exceed 65%
- Without V-9: E2E cannot exceed 82%

## HOW TO ADVANCE THROUGH STAGES
After C074 merges:
  python run.py live-validate --niche python_automation
  Review: data/live_validation_evidence.json
  Report results to PM for score update

Each passing stage unlocks the next credit tier.
