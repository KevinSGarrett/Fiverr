# CYCLE_074_PROMPT_CORRECTION_PROTOCOL.md
# Fiverr Research System — C074 Prompt Correction Protocol
# Created: 2026-06-09 (PM Governance Correction)

---

## STATUS: ALL C074 PROMPTS ARE FROZEN

All C074 agent prompts created before 2026-06-09 are invalid pre-correction drafts.
They must NOT be executed in Cursor or sent to any agent.
They are archived for reference only.

Reason: They were created before the PM Governance Correction and:
1. Use the old mislabeled ~67% "production-ready" number (should be two separate scores)
2. Target only +1% production readiness advancement (falls below the +5% gate)
3. Do not include a Task Substance Matrix or LARGE-XXLARGE classification per new definitions
4. Do not include a +5% E2E Production Readiness forecast
5. Contain many tasks that are verification-only, documentation-only, or repeated checks
6. Do not address the TierD-2 blocker that prevents reaching the +5% gate
7. Do not pass the Prompt Red-Team Review Gate

---

## FROZEN PROMPT FILES

| File | Status | Issue |
|---|---|---|
| CYCLE_074_AGENT_A_PROMPT.md | FROZEN — pre-correction draft | Old scorecard; many SMALL tasks counted as LARGE |
| CYCLE_074_AGENT_B_PROMPT.md | FROZEN — pre-correction draft | Content is substantive but lacks +5% E2E context |
| CYCLE_074_AGENT_E_PROMPT.md | FROZEN — pre-correction draft | Observation-only cycle advances ~0% E2E readiness |
| CYCLE_074_AGENT_C_PROMPT.md | FROZEN — pre-correction draft | Gate checks mostly SMALL; old scorecard |
| CYCLE_074_AGENT_F_PROMPT.md | FROZEN — pre-correction draft | Edge case tests advance ~0.1% E2E readiness each |
| CYCLE_074_AGENT_D_PROMPT.md | FROZEN — pre-correction draft | Post-merge governance advances ~0% E2E readiness |

Archive location: Files remain at PM_Pack/03_cursor_agent_system/ but with FROZEN header.
The first line of each file will be marked: SUPERSEDED — DO NOT USE — PRE-CORRECTION DRAFT

---

## ROOT CAUSE ANALYSIS: WHY C074 PROMPTS CANNOT MEET THE +5% GATE AS SCOPED

### C074 current scope: Wave 11 S8.3 Seller Setup Playbook Scaffold

What S8.3 delivers:
- src/playbook/generator.py: 9 functions generating playbook from recommendation + pricing data
- src/reports/templates/playbook.html: Jinja2 PDF template
- run.py playbook command: CLI for Markdown/PDF export
- RecommendationOutput: +2 Optional[dict] fields
- tests/unit/test_playbook_generator.py: 40+ tests

Internal Build Progress impact: +1% (Track 10: 8% → 15%, Track 07: 75% → 77%)

End-to-End Production-Grade Readiness impact: ~+1% or less
Why: The playbook scaffold uses {} defaults for visual and profile data.
It generates playbooks from mock/empty recommendation objects.
No live data flows through it. No live collection. No real recommendations.
It is a working scaffold that will be valuable once live data exists,
but it does not advance the live production path.

### The cap rule problem
Current hard cap: E2E score cannot exceed ~50% until live collection is validated.
Current E2E score: ~45%
Maximum gain without TierD-2: ~5% (gets to the cap but does not break through)
Actual expected gain from S8.3 alone: ~1%

### To reach +5% E2E gain, C074 needs one of:
1. TierD-2 live collection approval + first live run validation
2. Significant live data pipeline work beyond playbook scaffold
3. Formal blocker exception with documented rationale

---

## C074 CORRECTION OPTIONS

### Option A: Rescope C074 to include TierD-2 live collection (RECOMMENDED)
If TierD-2 is approved:
- Add live collection setup and first successful run for one niche
- Add live data persistence validation
- Add live data flow through scoring
- Add first live recommendation generated from real data
- Playbook scaffold then demonstrates with real data

Projected E2E gain: +8–12%
Projected internal build gain: +3–5%
Gate status: PASSES +5% requirement

### Option B: Blocker exception — document TierD-2 as the critical blocker
If TierD-2 is NOT being approved now:
- Execute C074 as Wave 11 S8.3 scaffold only
- Formally document that C074 advances internal progress only
- Acknowledge E2E gain is ~+1% (below +5% gate — documented exception)
- Commit to TierD-2 decision before C075 executes
- Document that the project is essentially in a "building toward production" phase

Gate status: FAILS +5% — blocker exception required and documented

### Option C: Hold C074 execution pending TierD-2 decision
- Do not execute C074 until TierD-2 is decided
- If approved: use Option A
- If deferred: use Option B with explicit timeline

---

## REQUIRED BEFORE C074 CAN EXECUTE

1. User decision on TierD-2 (ScrapFly live collection)
2. C074 rescoped per selected option (A, B, or C)
3. All 6 C074 prompts rewritten with:
   - Corrected two-score model (internal build progress + E2E production readiness)
   - Task Substance Matrix for every task
   - +5% E2E forecast OR formal blocker exception
   - LARGE-XXLARGE classification per new definitions
   - Red-team review gate passed
   - No filler tasks
   - Tasks mapped to production outcomes
4. PM certification that corrected prompts pass all gates

---

## WHAT THE CORRECTED C074 PROMPTS MUST INCLUDE

Regardless of which option is chosen:

### Required header in every corrected C074 prompt:
```
CYCLE 074 — [Agent X]
Current state (corrected):
  C073: COMPLETE | C074: CURRENT | Wave 10: COMPLETE | Wave 11: STARTING
  G-D: OPEN | TierD-1: OPEN (12 stashes) | TierD-2: [STATUS]
  Internal Engineering Build Progress: ~66%
  End-to-End Production-Grade Readiness: ~45% (range 42-50%)
  Hard cap: E2E score capped at ~50% until live collection validated (TierD-2)

C074 production objective:
  [Description of what live production capability this cycle advances]

C074 +5% E2E gate status:
  [PASSES with TierD-2 scope / DOCUMENTED EXCEPTION — TierD-2 blocker]
  [Forecast: +X% E2E from: task group 1 (+X%), task group 2 (+X%)]
```

### Required Task Substance Matrix in Agent A:
Every task must be scored and classified before inclusion.
No task classified SMALL or MEDIUM may be counted in the LARGE-XXLARGE minimum.

### Required absence of:
- Repeated verification of the same state (scrapfly=false more than once per agent)
- Line-count padding blocks
- Tasks that exist solely to hit numerical floors
- Report-writing tasks counted as LARGE
- Any reference to "~67% production-ready" without the two-score distinction

---

## CERTIFICATION REQUIRED BEFORE EXECUTION

The PM must certify:
[ ] All C074 prompts use the corrected two-score model
[ ] All C074 prompts include a Task Substance Matrix
[ ] All C074 prompts include a +5% E2E forecast or formal exception
[ ] All C074 tasks are classified under the new LARGE-XXLARGE definitions
[ ] No C074 task is a duplicate, pure verification, or filler
[ ] The C074 cycle package maps to real production-grade advancement
[ ] TierD-2 decision has been made and prompts reflect the decision
[ ] Frozen pre-correction prompts are archived and cannot be accidentally executed

PM Certification date: [to be filled after correction complete]
