# HYDRATION HEADER — Fiverr Research System
# Read this file first in every session to orient before any action.
# Updated: 2026-06-02 (C059 PM review)

## CYCLE STATE
CYCLE_DONE: 059
CYCLE_NEXT: 060
CYCLE_STATUS_059: COMPLETE - PR #68 squash-merged to develop
CYCLE_BRANCH_059: DELETED
TIER_GATE: Tier-2 CLOSED. Tier-3 R10 COMPLETE. Tier-4 next (R11 Edge Cases, Wave L).

## DEVELOP HEAD (after all post-merge governance commits)
develop HEAD: 25fdaa2 (docs(governance): enforce D codex trigger snippet in template)
C059 SQUASH SHA: 1fd62250ff04704d36b2a8606689c596e82a1545
C058 SQUASH SHA: a0471fb9247046fd913d57a8421d0bc715493192
C057 SQUASH SHA: 325ef30304de320cb062cea02aeba16dc601a90e

## SUITE STATE (C059 gate close)
Tests: 3971 passed
Coverage: 95.62% | Floor: 90% enforced

## REGRESSION PACK (strategy §7 v2.3 - 37 names)
Pack version: v2.3 (C059 closeout — REG-34/35/36 added for R10 dashboard)
37 permanent names (see strategy §7 for full list).
REG-34: test_ghost_market_excluded_from_opportunities_by_default
REG-35: test_all_non_ghost_tags_render_correctly
REG-36: test_empty_run_returns_no_alerts

## C059 VERIFIED FACTS
Epic: SRDI R10 - Dashboard & Alerting Integration (Wave K)
PR: #68 | Squash: 1fd62250ff04704d36b2a8606689c596e82a1545
Jira Done: SCRUM-634/635/636/637/638/897/639/640/1013 all Done
Gate results: G1-G10 all PASS (D report verified)
G4: 3971 passed, 95.62%
G5 golden: kw=110 62.7/1.0/CONDITIONAL_GO; kw=96 35.8; kw=3 56.66
Config: scrapfly=false; llm=false; external_signals_enabled=false
§7: v2.3 (REG-34/35/36). Strategy §15.5 added (Codex trigger anchor for draft PRs). v2.4 row.
Strategy §16 added: C059 known issues (foundation-gate seeding, KeywordScore.run_id, Codex P2 findings, TC-2 partial).
Codex timing: Bot triggered by ready_for_review event, not CI completion.
  D followed 15-min wait rule but PR was draft during wait.
  New §15.5: mark PR ready BEFORE starting Codex wait. D's PROMPT_TEMPLATE.md updated.
  Post-merge: 2 Codex P2 threads remain UNRESOLVED (no src/ fix committed in C059).

## C059 KNOWN ISSUES (carry to C060 — strategy §16)
ISSUE-1: Codex P2-1 — relevance_dashboard.py:86 ghost filter incomplete → C060 Agent B fix required.
  Regression: test_ghost_filter_handles_null_and_legacy_rows (REG-37 candidate)
ISSUE-2: Codex P2-2 — alert_generator.py:113 LLM alert query incorrect → C060 Agent B fix required.
  Regression: test_llm_alert_counts_actual_stage_7_5_executions (REG-38 candidate)
ISSUE-3: foundation-gate DOES NOT seed niches (yields niches=0). §14.3 correction in strategy §16.1.
  Agent E must manually backfill 9 niches after foundation-gate in C060.
ISSUE-4: KeywordScore.run_id attribute does NOT exist on model. All E queries using this will fail.
  Use ResultSetValidation.run_id as source instead. §16.2.
ISSUE-5: TC-2 (dry-run fix) partially done — ValueError exists but runtime still emits dry-run URLs.
  Root cause: sentinel URL injected at different stage than the ValueError. §16.4.
ISSUE-6: RSV band: SEED for 3rd consecutive cycle (C057/C058/C059). ScrapFly key now loads correctly
  but pipeline never reaches live collection due to niche-seeding failure + dry-run contamination.
ISSUE-7: External signals: 0/4 families in C059 throwaway DB (C058 had 2/4).
ISSUE-8: TC-1 ExternalSignal schema: still DEFERRED. raw_value/relevance_score/trend_direction absent.

## .ENV KEY INVENTORY (presence only)
OPENAI_API_KEY:    PRESENT (sk- prefix, len=164)
SCRAPFLY_API_KEY:  PRESENT (scp- prefix, len=41) - must load from .env (§14.2)
DATABASE_URL:      PRESENT (sqlite prefix, len=33)
REDDIT_CLIENT_ID/CLIENT_SECRET/USER_AGENT: PRESENT
REDDIT_DEVVIT_* and REDDIT_BRIDGE_*: multiple keys PRESENT (len=44,22,25)

## C060 SCOPE
Epic: SRDI R11 — Edge Cases, Future-Proofing & Maintenance (Wave L) — Tier-4
PLUS mandatory C059 Codex P2 fixes (Tier-C carry-forward for Agent B):
  - Fix Codex P2-1: relevance_dashboard.py:86 ghost filter + regression REG-37
  - Fix Codex P2-2: alert_generator.py:113 LLM alert query + regression REG-38
  - Fix foundation-gate niche seeding (add run.py seed-niches command)
  - Fix TC-2 dry-run contamination (find sentinel URL injection site)
SRDI spec: PM_Pack\ref\project_plan\13_srdi\03_EPIC_BREAKDOWN_MASTER.md §R11
           PM_Pack\ref\project_plan\13_srdi\04_DOD_AND_ACCEPTANCE.md §R11
C060 branch: cycle/060/integration (not yet created)
C060 dev head at start: 25fdaa2 (after PM review governance commit)

## GOLDEN ANCHORS (READ-ONLY FOREVER)
data/cycle037_live.db
kw=110: 62.7 / 1.0 / CONDITIONAL_GO
kw=96:  35.8 / 0.8389 / CAUTION
kw=3:   56.66 / 0.95 / MONITOR

## SRDI ROADMAP
Tier-0: DONE (R8/R1/R3/R2)
Tier-1: DONE (R4/R6/R9)
Tier-2: CLOSED (R5+R7)
Tier-3: COMPLETE (R10 — C059)
Tier-4: NEXT -> R11 (C060)

## OPEN TIER-D ITEMS
TierD-1: 6 stale git stashes (cycle051/047/043/036/029/012) - irreversible; confirm with user
TierD-2: SCRAPFLY full live collection - requires user to confirm credit budget
TierD-3: DL-207 (search URL shape) - deferred C057/C058/C059; blocked by niche seeding issue

## TOGGLE INVENTORY
analysis.external_signals_enabled: false (R7)
relevance.llm_relevance_enabled: false (R5)
collection.scrapfly.enabled: false (always false in committed config)

## 9 PRODUCTION NICHE IDS
prd_ai_saas | support_kb_readiness | gumloop_lindy_workflow | mcp_ai_agent | python_automation
ai_tool_llm_integration | ai_agent_development | workflow_automation | python_web_scraping
