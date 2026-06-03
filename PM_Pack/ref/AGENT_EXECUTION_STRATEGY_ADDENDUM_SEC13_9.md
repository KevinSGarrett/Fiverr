# POST-CYCLE PM REVIEW — ADDENDUM: Full Project Plan Review Protocol
# Created: 2026-06-03 (corrective action after C060 PM review)
# Status: PERMANENT RULE ADDITION — append to strategy §13

## ROOT CAUSE

POST_CYCLE_PM_REVIEW v4.2 Part 5.3 only instructed reading 13_srdi spec files.
It never required reading the 14-directory project plan at:
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\

Result: C051-C060 PM reviews were SRDI-complete but project-plan-blind.
The PM validated SRDI sequencing correctly while entirely missing:
  - 13 non-SRDI plan tracks (00_meta through 12_dashboard_ux)
  - Dashboard live-data gap (all 9 pages still use build_dashboard_demo_data())
  - 3 missing SRDI launch artifacts (11/12/13 in 00_SRDI_INDEX.md)
  - Waves 9-12 unstarted (Pricing, Discovery, Playbook, Dashboard UX)
  - Disabled production toggles (LLM relevance, external signals)

## CORRECTIVE RULE (strategy §13 addition — effective C061+)

### §13.9 FULL PROJECT PLAN REVIEW (mandatory every PM review cycle)

Before determining CYCLE_NEXT scope, the PM MUST:

Step 1: List all 14 plan tracks:
  dir C:\Fiverr\Fiverr\PM_Pack\ref\project_plan
  Expected: 00_meta, 01_vision, 02_architecture, 03_data, 04_collection,
            05_scoring, 06_analysis, 07_reporting, 08_roadmap, 09_pricing,
            10_discovery, 11_playbook, 12_dashboard_ux, 13_srdi

Step 2: Read the wave schedule to understand full scope:
  C:\Fiverr\Fiverr\PM_Pack\ref\project_plan\00_meta\ENHANCEMENT_WAVE_SCHEDULE.md
  This is the master schedule. Waves 0-8 are DESIGN COMPLETE. Waves 9-12 are NEXT/PLANNED.
  "Design complete" != "implemented". Always check implementation vs. spec.

Step 3: For each of the 14 tracks, answer 3 questions:
  a) Is the spec fully implemented in src/?
  b) If implemented, is it running in PRODUCTION MODE (live data, toggles ON)?
  c) Are there blocking technical debts (deferred TCs, disabled toggles)?

Step 4: Run this gap check EVERY cycle:
  [ ] src/dashboard/pages/*.py — do any call build_dashboard_demo_data()? (demo = not production)
  [ ] config.yaml — are any feature toggles still false that should be production-on?
  [ ] PM_Pack/ref/project_plan/13_srdi/00_SRDI_INDEX.md — do all listed files exist on disk?
  [ ] src/analysis/result_set_validator.py NICHE_VALIDATION_CONFIG matches config.yaml niches
  [ ] src/playbook/ — does implementation match 11_playbook/ spec depth?
  [ ] src/discovery/ — does implementation match 10_discovery/ spec depth?
  [ ] src/pricing/ — does implementation match 09_pricing/ spec depth?

Step 5: Build a full-project gap list before writing any cycle task.
  Gap list format: | Track | Gap | Production Ready? | Blocking? |
  A gap that is "Blocking" prevents full-product production readiness.

## HARD RULE

"SRDI complete" DOES NOT mean "project complete".
SRDI is one initiative within the full project plan.
The PM review must track BOTH dimensions every cycle:
  1. SRDI/initiative status (closed with C060)
  2. Full project plan status (still in progress)

Every CYCLE_NEXT scope decision must be made against the full project gap list,
not just the SRDI roadmap.

## C061+ SCOPE CORRECTION

C061 was initially scoped as "Post-SRDI Collection Hardening (TC-1 + DL-207)."
This is correct but INSUFFICIENT. The complete C061 scope must also address:

Priority ordering (per ENHANCEMENT_WAVE_SCHEDULE.md implementation priority):
  P0: TC-1 ExternalSignal schema (blocks live signals — finish what was started)
  P0: DL-207 URL shape fix (blocks live collection)
  P0: Dashboard live-data wiring (9 pages use demo data — not production)
  P0: SRDI launch artifacts 11/12/13 (referenced in index but missing on disk)
  P1: Enable external_signals_enabled: false → true (once TC-1 done)
  P1: Wave 9 — Pricing Strategy Engine implementation start
  P2: Wave 10 — LLM-Powered Niche Discovery start
  P2: Wave 11 — Gig Creation Playbook implementation
  P2: Wave 12 — Dashboard UX Overhaul

This is a multi-cycle backlog. C061 will address P0 items.
C062+ will address P1/P2 items.

## HOW TO PREVENT THIS AGAIN

1. Part 5.3 of POST_CYCLE_PM_REVIEW must explicitly require reading all 14 plan tracks
   (current text only reads 13_srdi files — must be expanded)
2. HYDRATION_HEADER must track ALL 14 plan tracks (not just SRDI)
3. EPIC_STATUS_TRACKER must have a "Full Project Plan Status" section
4. Every PM review checklist (Part 8) must include:
   [ ] All 14 project plan tracks reviewed (not just active SRDI epic)
   [ ] Dashboard demo-data dependency checked
   [ ] Production toggle posture verified
   [ ] Full project gap list built before determining CYCLE_NEXT scope
