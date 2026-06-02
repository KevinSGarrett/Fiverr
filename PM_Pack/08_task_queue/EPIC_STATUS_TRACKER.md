# EPIC STATUS TRACKER — Fiverr Research System
# Last updated: 2026-06-02 (C059 PM review — C060 Tier-4 active)

## SRDI INITIATIVE STATUS

| Epic | Title | Tier | Status | Cycle | Squash SHA |
|---|---|---|---|---|---|
| R8 | Data Schema Extensions | 0 | DONE | C049 | (C049 SHA) |
| R1 | Search URL Hardening | 0 | DONE | C051 | (C051 SHA) |
| R3 | Sponsored & Zombie Filtering | 0 | DONE | C052 | (C052 SHA) |
| R2 | Result-Set Relevance Validation | 0 | DONE | C053 | (C053 SHA) |
| **Tier-0 Gate** | | - | **COMPLETE** | C053 | - |
| R4 | Scoring System Integrity | 1 | DONE | C054 | acff870 |
| R6 | Discovery Engine Relevance Gates | 1 | DONE | C055 | fabdca9 |
| R9 | Testing & Validation Framework | 1 | DONE | C056 | 3617ce4 |
| **Tier-1 Gate** | | - | **COMPLETE** | C056 | - |
| R5 | LLM Relevance Classification | 2 | DONE | C057 | 325ef30304de320cb062cea02aeba16dc601a90e |
| R7 | External Signal Integrity | 2 | DONE | C058 | a0471fb9247046fd913d57a8421d0bc715493192 |
| **Tier-2 Gate** | | - | **CLOSED** | C058 | - |
| R10 | Dashboard & Alerting Integration | 3 | **DONE** | C059 | 1fd62250ff04704d36b2a8606689c596e82a1545 |
| **Tier-3 Gate** | R10 primary | - | **COMPLETE** | C059 | - |
| **R11** | **Edge Cases & Maintenance** | 4 | **ACTIVE (C060)** | C060 | - |

## REGRESSION PACK STATUS

Current pack (after C059 + governance): **37 names, ~78 passed** — strategy §7 v2.3
REG-1..34 (prior) + REG-34/35/36 (C059 R10)
REG-37/38 PENDING (C060 — Codex P2 fixes)

## C059 STATUS — COMPLETE

PR #68: merged=true | squash SHA: 1fd62250ff04704d36b2a8606689c596e82a1545
Issues Done: SCRUM-634/635/636/637/638/897/639/640/1013 all Done
Suite: 3971 passed | Coverage: 95.62% | Golden: PASS | All gates: G1-G10 PASS
Codex timing: §15.5 rule added — mark PR ready BEFORE starting 15-min Codex wait
Post-merge: 2 Codex P2 threads UNRESOLVED on PR #68 — carry to C060 Agent B
§7: v2.3 (REG-34/35/36). Strategy §16 added (C059 known issues). §15.5 added (Codex draft-PR rule).
foundation-gate niche seeding: UNRELIABLE (yields 0 niches) — §16.1 correction
KeywordScore.run_id: does NOT exist as ORM attribute — §16.2 correction
TC-2 dry-run fix: PARTIAL (ValueError in keyword_expansion but runtime still contaminated)

## C060 SCOPE

Epic: SRDI R11 — Edge Cases, Future-Proofing & Maintenance (Wave L) — Tier-4
Jira stories: SCRUM-641 through SCRUM-648 (and/or others per EPIC_BREAKDOWN_MASTER §R11)
SRDI spec: PM_Pack\ref\project_plan\13_srdi\03_EPIC_BREAKDOWN_MASTER.md §R11

MANDATORY C059 CARRY-FORWARD (Agent B Tier-C — must be in C060):
  P2-1: Fix relevance_dashboard.py:86 ghost filter + REG-37 regression
  P2-2: Fix alert_generator.py:113 LLM alert query + REG-38 regression
  §16.1: Add run.py seed-niches command (fix foundation-gate niche seeding gap)
  §16.4: Fix TC-2 dry-run sentinel URL injection site

## NEW GOVERNANCE RULES ADDED IN C059 (strategy doc reference)

§15.5 CODEX TRIGGER ANCHOR (added after C059):
  The Codex bot is triggered by PR `ready_for_review` event, NOT by CI completion.
  Agent D must: mark PR ready → record ready_for_review timestamp → start 15-min wait.
  Do NOT start Codex wait while PR is still in draft state.

§16 C059 KNOWN ISSUES (added in C059 PM review):
  §16.1: foundation-gate doesn't seed niches (workaround: manual insert)
  §16.2: KeywordScore.run_id doesn't exist (use ResultSetValidation.run_id)
  §16.3: Codex P2-1/P2-2 from PR #68 unresolved — C060 Agent B fixes
  §16.4: TC-2 dry-run contamination partial — sentinel URL injection site not yet fixed
