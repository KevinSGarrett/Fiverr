
### 13.10 FULL PROJECT PLAN REVIEW (binding every PM review — effective C061+)

**Root cause this fixes:** POST_CYCLE_PM_REVIEW v4.2 Part 5.3 only read 13_srdi/ spec files.
The 13 other plan directories (00_meta through 12_dashboard_ux) were never reviewed.
C051-C060 validated SRDI deliverables correctly while being completely blind to:
  - Dashboard pages still using build_dashboard_demo_data() (not live DB)
  - TC-1 ExternalSignal schema deferred for 10 cycles
  - Missing SRDI launch artifacts (11_AI_AGENT_HANDOFF, 12_LAUNCH_READINESS, 13_RISK_COMPLIANCE_COST)
  - Waves 9-12 unstarted (Pricing Engine, Discovery, Playbook, Dashboard UX)
  - LLM relevance toggle OFF for 10+ cycles despite R5 being complete
  - External signals toggle OFF despite R7 being complete

Hard rule: "SRDI complete" does NOT equal "project complete". These are different dimensions.
Every PM review must track BOTH and build a full-project gap list before determining CYCLE_NEXT scope.

Mandatory steps (blocking before any cycle scope decision):

STEP 1: List the 14 plan track directories.
  dir C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
  Expected: 00_meta, 01_vision, 02_architecture, 03_data, 04_collection, 05_scoring,
            06_analysis, 07_reporting, 08_roadmap, 09_pricing, 10_discovery,
            11_playbook, 12_dashboard_ux, 13_srdi

STEP 2: Read the master wave schedule:
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\00_meta\ENHANCEMENT_WAVE_SCHEDULE.md
  This is the full product scope. Design-complete (spec written) != implementation-complete (code in src/).
  Always distinguish the two.

STEP 3: For each of the 14 tracks, answer 3 questions:
  a) Is the spec implemented in src/? (check actual files, not claimed)
  b) Is it running in PRODUCTION MODE? (live data? toggles ON? not demo data?)
  c) What are the blocking technical debts?

STEP 4: Run these mandatory gap checks EVERY cycle before writing any task:
  Check 1: Dashboard demo-data -- any page calling build_dashboard_demo_data() is NOT production
  Check 2: Feature toggle posture -- external_signals_enabled, llm_relevance_enabled in config.yaml
  Check 3: Missing SRDI launch artifacts -- do 11/12/13 exist in 13_srdi directory?
  Check 4: NICHE_VALIDATION_CONFIG drift (see Part 2.8)

STEP 5: Build and update the full-project gap table before writing cycle tasks.
  Use the 14-row table in EPIC_STATUS_TRACKER.md "Full Project Plan Status" section.

The 4 production-readiness release gates:
  G-A: Governance completeness -- launch docs 11/12/13 complete -- FAIL until created
  G-B: Data/model closure -- TC-1 ExternalSignal schema closed -- FAIL until merged
  G-C: Dashboard runtime readiness -- all 9 pages use live DB -- FAIL until live-data wiring done
  G-D: Roadmap balance -- non-SRDI waves actively shipping -- FAIL until Wave 9+ begins

### Version history (Section 13)

| Version | Date | Change |
| --- | --- | --- |
| 1.9 | 2026-06-01 | §13.1-13.9 PM OPERATING RULES added. All rules traced to specific C056 failures. |
| 2.0 | 2026-06-03 | §13.10 FULL PROJECT PLAN REVIEW added. Root cause: C051-C060 PM reviews read only 13_srdi specs, leaving 13 other plan tracks invisible for 10 cycles. SRDI-complete does not equal project-complete. Effective C061+. |

