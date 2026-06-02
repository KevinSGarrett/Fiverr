# Agent Execution Strategy

Canonical reference for multi-agent cycle execution, regression packs, and handoff contracts.

---

## Section 7: Permanent Regression Pack

Accumulated regression selectors (20-name pack) plus cycle-specific permanent regressions.

### Current 20-name accumulated pack (Cycle 053 baseline)

These are the required regressions that must stay green during Cycle 053:

| # | Test name | File |
| --- | --- | --- |
| 1 | `test_extract_price_text_from_payload_uses_nested_price_amount` | `tests/unit/test_gig_detail.py` |
| 2 | `test_parse_gig_detail_from_html_keeps_zero_review_count` | `tests/unit/test_gig_detail.py` |
| 3 | `test_parse_seller_profile_from_html_keeps_zero_review_count_from_hydration` | `tests/unit/test_seller_profile.py` |
| 4 | `test_seller_profile_fetcher_maps_parser_fields_for_persistence` | `tests/unit/test_seller_profile.py` |
| 5 | `test_gig_detail_fetcher_does_not_overwrite_existing_optional_fields` | `tests/unit/test_gig_detail.py` |
| 6 | `test_seller_profile_live_markup_drift_regression_spec` | `tests/unit/test_seller_profile.py` |
| 7 | `test_scoring_fallback_queries_scope_to_active_run_id` | `tests/unit/test_scoring_db_integration.py` |
| 8 | `test_scoring_fallback_queries_recover_when_latest_run_unlinked` | `tests/unit/test_scoring_db_integration.py` |
| 9 | `test_demand_uses_search_result_total_result_count_when_available` | `tests/unit/test_scoring_db_integration.py` |
| 10 | `test_competition_score_session_falls_back_to_latest_profile_when_run_mismatch` | `tests/unit/test_competition_score.py` |
| 11 | `test_scoring_uses_card_urls_with_querystrings_for_sparse_links` | `tests/unit/test_scoring_db_integration.py` |
| 12 | `test_confidence_modifier_uses_current_run_context_not_none` | `tests/unit/test_confidence_score.py` |
| 13 | `test_weakness_multi_row_fallback_does_not_produce_extreme_value` | `tests/unit/test_weakness_multi_row_averaging.py` |
| 14 | `test_fiverr_search_url_always_includes_category_filter_for_production_niches` (REG-13) | `tests/unit/test_search_url_builder.py` |
| 15 | `test_unconstrained_search_result_applies_demand_confidence_deduction` (REG-14) | `tests/unit/test_search_url_builder.py` |
| 16 | `test_eligibility_ghost_hard_block_even_when_forced` (REG-15) | `tests/unit/test_recommendation_eligibility.py` |
| 17 | `test_demand_qualified_trc_when_rsv_below_080` (REG-16) | `tests/unit/test_demand_score_extended.py` |
| 18 | `test_sponsored_gigs_never_included_in_competition_top10` (REG-17) | `tests/unit/test_scoring_db_integration.py` |
| 19 | `test_zombie_gigs_never_used_in_feasibility_review_barrier` (REG-18) | `tests/unit/test_feasibility_extended.py` |
| 20 | `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20_percent` (REG-19) | `tests/unit/test_demand_score_extended.py` |

REG-15 and REG-16 are now active in the permanent pack for Cycle 053.

### Cycle 054 additions (2026-06-01) — pack now 23

| # | Test name | File | Purpose |
| --- | --- | --- | --- |
| 21 | `test_niche_profile_excludes_contaminated_keywords` (REG-20) | `tests/unit/test_competition_score.py` | Niche competitor profile builder drops keywords with RSV relevance < 0.40 |
| 22 | `test_opportunity_qualified_by_relevance` (REG-21) | `tests/unit/test_opportunity_extended.py` | Opportunity score multiplied by (0.5 + 0.5×RSV) when RSV < 0.70 |
| 23 | `test_price_outlier_excluded_from_competition_and_profitability` (REG-22) | `tests/unit/test_profitability_score_extended.py` | IQR-based price outlier filter applied in competition and profitability |

REG-20/21/22 added in Cycle 054 (R4 quality-aware scoring), PR #63, merged develop @ acff870. §7 update deferred from C054 PM review (not performed); backfilled in C055 PM review 2026-06-01.

### Cycle 055 additions — MERGED (pack now 26 after C055 close)

| # | Test name | File | Purpose |
| --- | --- | --- | --- |
| 24 | `test_ghost_discovery_recorded_as_invalid_not_miss` (REG-25) | `tests/unit/test_discovery_relevance_gates.py` | Ghost discovery outcome recorded as INVALID not a MISS |
| 25 | `test_feedback_excludes_contaminated_outcomes` (REG-26) | `tests/unit/test_discovery_relevance_gates.py` | Gate-4 feedback aggregation excludes is_invalid and is_contaminated rows |
| 26 | `test_low_specificity_hypothesis_rejected` (REG-27) | `tests/unit/test_discovery_relevance_gates.py` | Gate-1 rejects hypothesis with specificity_confidence < 0.65 |

NOTE: REG-25/26/27 are merged via PR #64 (squash fabdca9) and remain in the permanent 26-name pack.

### Cycle 057 additions — MERGED (pack now 28 after C057 close)

| # | Test name | File | Purpose |
| --- | --- | --- | --- |
| 27 | `test_llm_relevance_only_triggers_in_ambiguous_band` (REG-23) | `tests/unit/test_llm_relevance.py` | LLM Stage 7.5 trigger gate fires only in RSV band [0.40, 0.70) |
| 28 | `test_llm_ghost_verdict_blocks_recommendation` (REG-24) | `tests/unit/test_llm_relevance.py` | NOT_RELEVANT LLM verdict produces recommendation block |

REG-23/24 added in Cycle 057 (R5 LLM Relevance), PR #66, merged develop @ 325ef30304de320cb062cea02aeba16dc601a90e.

### Cycle 058 additions — MERGED (pack now 31 after C058 close)

| # | Test name | File | Purpose |
| --- | --- | --- | --- |
| 29 | `test_autocomplete_emerging_keyword_gets_neutral_not_zero_score` (REG-28) | `tests/unit/test_external_signal_integrity.py` | Emerging autocomplete -> 50 not penalized |
| 30 | `test_reddit_qualified_score_lower_than_raw_when_buyer_intent_low` (REG-29) | `tests/unit/test_external_signal_integrity.py` | Reddit qualified < raw when intent is low |
| 31 | `test_trends_platform_qualifier_applied_before_demand_score_calculation` (REG-30) | `tests/unit/test_external_signal_integrity.py` | Trends qualifier applied pre-demand |

REG-28/29/30 added in Cycle 058 (R7 External Signal Integrity), PR #67, merged develop @ a0471fb9247046fd913d57a8421d0bc715493192.

Carry-forward Codex-fix guards that must remain named and green:

| Test name | File | Purpose |
| --- | --- | --- |
| `test_demand_pairs_strictness_with_selected_total_result_count_row` | `tests/unit/test_scoring_db_integration.py` | Strictness/count row pairing guard |
| `test_demand_ignores_legacy_migration_default_none_strictness` | `tests/unit/test_scoring_db_integration.py` | Migration-default `'NONE'` guard in demand path |

### Cycle 049 additions (2026-05-29)

| Test name | File | Purpose |
| --- | --- | --- |
| `test_weakness_multi_row_fallback_does_not_produce_extreme_value` | `tests/unit/test_weakness_multi_row_averaging.py` | kw=96 combined-state weakness must not spike to 100.0 when a single OWS=10.0 penalty row is present alongside moderate rubric rows |
| `test_weakness_extreme_ows_row_does_not_dominate_average` | `tests/unit/test_weakness_multi_row_averaging.py` | OWS aggregation excludes ceiling rows when lower scores exist |
| `test_weakness_kw96_equivalent_consistent_before_after_combined_state` | `tests/unit/test_weakness_multi_row_averaging.py` | Historical fallback rejects transient 100.0 when stable 53.52 exists |
| `test_kw110_conditional_go_passes_all_recommendation_gates_when_analysis_complete` | `tests/unit/test_recommendation_eligibility.py` | Eligibility gate clears when GQS analysis_complete populated |

### Cycle 051 additions (2026-05-30)

| Test name | File | Purpose |
| --- | --- | --- |
| `test_fiverr_search_url_always_includes_category_filter_for_production_niches` | `tests/unit/test_search_url_builder.py` | Guarantees all production niches keep category/subcategory constraints under SUBCATEGORY strictness |
| `test_unconstrained_search_result_applies_demand_confidence_deduction` | `tests/unit/test_search_url_builder.py` | Guards the post-R1 NONE strictness confidence deduction and note attachment |

### Version history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-05-29 | Cycle 049 Agent B: added weakness multi-row OWS averaging regression + kw=110 eligibility gate regression |
| 1.1 | 2026-05-30 | Cycle 051 Agent B: added R1 search URL category-filter + unconstrained demand-deduction regressions |
| 1.3 | 2026-05-30 | Cycle 052 Agent B: added REG-17/18/19 (sponsored competition exclusion, zombie feasibility barrier exclusion, TRC sponsored-fraction multiplier). |
| 1.4 | 2026-05-31 | Cycle 053 Agent B: activated REG-15/16 (ghost hard block and RSV-qualified TRC demand path) and expanded permanent pack to 20 names. |
| 1.7 | 2026-06-01 | C055 PM review: backfilled C054 (R4) REG-20/21/22 into §7 (pack 20→23 verified merged @ acff870); noted C055 REG-25/26/27 pending merge (pack will be 26 after C055 D re-gate passes). |
| 1.8 | 2026-06-01 | C055 closeout: confirmed REG-25/26/27 merged with PR #64 (fabdca9), permanent pack is now 26 names. |
| 2.0 | 2026-06-02 | C057 (R5): REG-23/24 added to permanent pack. Pack now 28 names (36 passed). Tier-2 R5 complete. |
| 2.1 | 2026-06-02 | C058 (R7): REG-28/29/30 added. Pack now 31 names (39 passed). Tier-2 gate CLOSED. |

### 12-name accumulated pack (reference)

Run with:

```text
python -m pytest -q tests/unit/test_gig_detail.py \
  tests/unit/test_scoring_db_integration.py \
  tests/unit/test_scrapfly_workflow_integration.py \
  tests/unit/test_search_result.py \
  tests/unit/test_competition_score.py \
  tests/unit/test_confidence_score.py \
  -k "nested_price or zero_review or run_scoped or seller_profile_live_markup_drift \
      or rank or gig_id or latest_unlinked or total_result_count or profile_fallback \
      or signals_present or card_urls or current_run_context" \
  -v --no-header
```

Expected: 20 passed (12 named regressions + superset matches).

---

## Section 8: Task & Prompt-Length Standard (effective Cycle 052+)

This section is authoritative for per-agent task counts and prompt length minimums. It
supersedes the older "18+/20+ task" and prior length figures referenced anywhere else.

### 8.1 Task minimum (raised 20 -> 25)

Every cursor-agent prompt MUST contain **at least 25 tasks**, each sized LARGE, XLARGE,
XXLARGE, or **XXXLARGE**. No standalone small/medium tasks.

| Size | Sub-steps | Typical use |
| --- | --- | --- |
| LARGE | 4-6 | a single focused deliverable (one module section, one test group) |
| XLARGE | 6-8 | a multi-part deliverable with verification |
| XXLARGE | 8-12 | a subsystem + its tests + its wiring |
| XXXLARGE | 12+ (or spans >=2 files with cross-checks) | a full feature slice end-to-end, or a migration + model + wiring + tests |

### 8.2 Legitimacy rule (binding)

Every task must be **real, project-advancing work** that moves the system toward end-to-end
completion. Filler, busywork, or padding tasks invented only to reach the count of 25 are a
PM failure and an agent failure. Each task must map to: a spec requirement, an acceptance
criterion, a regression, a gate, a re-collection/validation need, or a concrete integration
step. If a cycle's real scope does not yield 25 substantive tasks for an agent, the PM splits
larger deliverables into legitimately separable verification-bearing steps -- never invents
hollow ones.

### 8.3 Prompt length minimum (raised +35%)

| Agent | Old min | New min (+35%) |
| --- | --- | --- |
| A | 600 | **810** |
| B | 700 | **945** |
| E | 600 | **810** |
| C | 500 | **675** |
| F | 600 | **810** |
| D | 700 | **945** |
| **Total** | 3,700 | **4,995** |

Length is a floor, not a target; it must be filled with substantive content (code skeletons,
test stubs, verbatim queries, deliverable matrices, decision records, trace ledgers, report
templates) -- never filler to hit a line count.

### 8.4 Prompt-sizing enforcement (BLOCKING self-gate on the PM's own work)

Before the PM may declare a cycle's prompt-writing complete -- and before any prompt is handed
to an agent -- the PM MUST verify EVERY agent prompt against BOTH §8.1 (>=25 substantive
LARGE-XXXLARGE tasks) AND §8.3 (per-agent line floor). Verification is mechanical and recorded,
never eyeballed:

1. Run `(Get-Content <prompt_path>).Count` on all six prompts and record the ACTUAL line counts
   next to their floors (A810 / B945 / E810 / C675 / F810 / D945; total 4995).
2. Count the numbered tasks in each prompt; confirm >=25, each genuinely LARGE-XXXLARGE -- not a
   one-line stub masquerading as a task.
3. ANY prompt under its line floor OR under 25 substantive tasks is **NOT DONE**. The PM MUST
   expand it with GENUINE content per §8.3 -- full inline code/dataclass skeletons, full inline
   test-file skeletons with every test-function stub, verbatim command/query/gate blocks,
   per-niche and per-file procedures, deliverable + Definition-of-Done matrices, worked numeric
   examples, and report templates -- then re-verify the count. Padding to hit the number is
   itself a §8.2 legitimacy failure.
4. This gate is HARD and BLOCKING. The v3.0 Post-Cycle PM Review self-audit item "every prompt
   meets minimum line count and task minimum" is BLOCKING, not advisory. The PM may NOT conclude
   cycle prep, and may NOT release prompts to the agents, until all six PASS both checks with
   recorded counts.
5. The recorded count table (actual vs floor, per agent) MUST be included in the cycle's prep
   notes / PM closeout so the check is auditable by the next PM review.

Rationale: Cycle 053 prep initially shipped all six prompts far under floor
(A487 / B271 / E157 / C161 / F156 / D184 vs the 4995 total) even though each held 25 tasks.
Under-length prompts systematically omit the inline skeletons, command blocks, and acceptance
detail the agents need to execute without guesswork. This gate makes that omission impossible
to ship.

### 8.4.1 Zero-tolerance, write-time, per-prompt enforcement (supersedes any "batch" framing)

The §8.4 self-gate failed TWICE: Cycle 053 shipped all six prompts under floor, and Cycle 054's
Agent A first draft was 379 lines against an 810 floor. Both share one root cause: treating the line
count as an END-OF-BATCH step and accepting "complete in content" / "I'll expand later" as a
substitute for the floor. This subsection removes that loophole. It is binding on the PM.

1. **PER-PROMPT, AT WRITE TIME.** The line count is verified the MOMENT a prompt is finished —
   BEFORE the next prompt is started, and BEFORE the prompt is described, surfaced, committed, or
   handed off as "done." Not "after all six." Per prompt, every time.
2. **RECORDED + SHOWN.** For each prompt, run `(Get-Content <path>).Count`, record the number next
   to its floor, and SHOW it (in the reply to the user AND in the cycle prep notes). A prompt whose
   count has not been shown is not done.
3. **UNDER FLOOR = DOES NOT EXIST.** A prompt below its floor (A810/B945/E810/C675/F810/D945) is NOT
   WRITTEN. It may not be called complete, surfaced as a deliverable, committed as final, or handed
   to an agent. There is no "draft now, expand later." Content completeness is necessary but NOT
   sufficient; the floor is the minimum bar, not a target to approach.
4. **BANNED COMPLETION RATIONALIZATIONS.** These phrases may NOT be used to call an under-floor
   prompt done: "complete in content," "I'll expand at the end," "the content already covers it,"
   "under floor but done," "good enough," "the deep detail belongs elsewhere." If the PM catches
   itself writing one about a prompt under floor, the prompt is NOT done — expand it now.
5. **UNDER FLOOR ⇒ A MISSING MANDATORY BLOCK.** A short prompt omitted one of the §8.4.2 blocks — it
   is never because "the cycle doesn't have enough." Find the missing block and add it as REAL
   content. (Padding to a number is the opposite failure and violates §8.2 — both are forbidden.)

### 8.4.2 Mandatory content-block manifest (what legitimately fills the floor)

Every prompt MUST contain, INLINE (never "go read X"): header/role/branch/base-SHA/strategy pointer;
mission tied to the cycle's Jira story keys; project context + connector-only auth note (no secrets);
verified starting state (SHAs, counts, config flags, the 9 real niche_ids); 6-agent architecture +
file zones + the hard gates verbatim (G-001..G-004, CONFIG, PARITY); a mandatory preflight command
block (real commands); 25+ tasks each LARGE-XXXLARGE with numbered sub-steps; the FULL accumulated
regression list by exact name (not "see §7"); a completion-standard checklist.

Agent-type-specific mandatory blocks (their absence is why a prompt is under floor):
- **A (planner):** the six handoff packages with file-by-file detail + new function SIGNATURES; exact
  command blocks (git Invoke-Exe pattern, Jira connector calls, golden-run per toggle); toggle
  inventory; file-impact map; worked numeric example(s) of the cycle's core invariant; a full
  fill-in report template.
- **B (implementer):** for EACH story, an inline code/dataclass/function skeleton (signature +
  docstring + key branches) + its toggle/default + an inline test-function stub per new behavior
  (name + arrange/act/assert outline). This is the bulk of B's length and is non-negotiable.
- **E (validation):** the §10 ScrapFly runbook verbatim; exact live commands; the sample set; the
  "[SEED — no live signal]" fallback; a full report template.
- **C (integration):** every verification command inline; the toggle-OFF parity command per toggle;
  the drift-check procedure; a report template.
- **F (coverage):** each new test by name with an arrange/act/assert stub; the 3 REG stubs; the
  coverage-measurement commands; a report template.
- **D (merge gate):** the full merge-gate checklist; the Codex GraphQL query verbatim; the
  attribution/zone commands; the regression-by-name list; the post-merge Jira plan; a report template.

A prompt missing its agent-type blocks is under floor BY CONSTRUCTION — add the blocks, then re-count.

### Version history (continued)

| Version | Date | Change |
| --- | --- | --- |
| 1.2 | 2026-05-30 | Post-Cycle-051 PM: task minimum 20 -> 25 (LARGE-XXXLARGE); prompt length minimums +35% (A810/B945/E810/C675/F810/D945; total 4995); added explicit legitimacy rule (no filler tasks). |
| 1.4 | 2026-05-31 | Added §8.4 prompt-sizing enforcement: blocking self-gate requiring `(Get-Content).Count` verification of every prompt against its floor + 25-task minimum, recorded in prep notes, before prompts may be released. Triggered by Cycle 053 under-floor prompts. |
| 1.6 | 2026-05-31 | Added §8.4.1 (zero-tolerance, write-time, per-prompt enforcement; under-floor = not written; banned rationalizations) + §8.4.2 (per-agent mandatory content-block manifest). Triggered by C054 Agent A shipping under floor despite §8.4. Closes the "expand later"/"complete in content" loophole. |


---

## Section 9: PM Direct-Action Authority (effective Cycle 054+)

This section defines what the Project Manager may do **directly** — immediately after a cycle
or between cycles — versus what must be handed to a cursor agent. The goal is to let the PM
resolve small, safe, reversible project-management and repo-hygiene items itself (Jira, GitHub,
docs, cleanup, verification) instead of waiting a full agent cycle, **without** eroding the
disciplines that keep cycles clean.

### 9.1 Governing principle

The PM directly handles **reversible, non-code, orchestration / project-management / repo-hygiene**
actions. The PM **never** directly changes product behavior (`src/`), test assertions (`tests/`),
or runtime config behavior (`config.yaml`). Those flow through **Agent B and the gate sequence**,
which preserves two hard-won invariants:

- **Attribution invariant:** every `src/`-touching commit in a cycle range is an Agent B
  `feat/`|`fix/` commit. Agent D's merge gate enforces this; the c6489b9 (C edited src/) and
  c7b9b52 (D no-op attribution touch) failures are kept closed by it.
- **Gate invariant:** anything that must pass CI / codecov / Codex or be merged into `develop`
  as cycle scope goes through the cursor-agent + Agent-D gated path (G-001..G-004).

Irreversible or cost/security/account-impacting actions are **never** taken without explicit
user consent.

### 9.2 The four tiers

**Tier A — PM acts immediately (no agent, no permission needed):**
- **Jira:** transition statuses to match verified reality; add/edit comments; create the cycle
  control + story tickets; link issues to epics; fix labels / sprint assignment; revert a story
  that is marked Done but whose DoD is not met.
- **GitHub (non-merge, non-destructive):** delete the *merged* cycle branch on origin; prune
  stale *already-merged* remote cycle branches; comment on a PR/issue; inspect/re-read CI; read
  Codex review threads.
- **Local docs / PM_Pack / governance:** edit any file under `PM_Pack/`, the strategy doc,
  hydration header, epic tracker, cycle log, prep notes; refresh templates; add a steward note to
  a cycle report (agent reports stay agent-authored).
- **Repo hygiene (reversible):** remove untracked PM scratch litter; `git rm --cached` an
  accidentally-tracked artifact that should be ignored (coverage.xml, `*.log`, `*.db`) **and** add
  it to `.gitignore` in the same commit; extend `.gitignore` to cover PM scratch / live configs.
- **Read-only verification:** run the test suite (file-scoped or full), `--cov`, `config-check`,
  smoke checks, git/gh read commands, the Codex GraphQL query. Running tests changes nothing in
  the repo and is always allowed.
- **Commit + push the PM's own doc/governance changes to `develop`** with a `docs(...)` /
  `chore(...)` conventional commit — **provided the commit touches ZERO files under `src/` or
  `tests/` and makes ZERO `config.yaml` behavior change.** This is how between-cycle governance
  lands cleanly without waiting for Agent A.

**Tier B — PM acts, but records a safeguard (Tier A + write it down):**
- Large or multi-file doc/governance commits: record the commit SHA + one-line rationale in the
  cycle log / prep notes so the next review can see it.
- Created Jira tickets: record the created keys in the prep notes.
- `git rm --cached` of a tracked artifact: must be paired with a `.gitignore` entry in the same
  commit and recorded.

**Tier C — PM never acts directly; hand to a cursor agent:**
- **ANY change under `src/`** (production logic). Even a one-line, obvious fix goes to Agent B with
  a defect note. This is the bright line that keeps the attribution invariant and the c6489b9
  failure closed.
- **ANY add/modify under `tests/`** that asserts product behavior — Agent B (logic) or Agent F
  (coverage). The PM does not author tests into the suite.
- **ANY `config.yaml` runtime-behavior change** (toggles, thresholds, weights, enabling ScrapFly in
  the committed file) — goes through Agent B with parity + config gate + CI + Codex + D-merge.
- **ANYTHING that must pass a gate or be merged as cycle scope** — the gated cursor-agent path.

**Tier D — PM never acts; surface to the user for an explicit yes/no:**
- Irreversible/destructive git: dropping/clearing stashes (the 6 stale stashes), history rewrite,
  force-push, deleting a non-cycle or unmerged branch, hard resets that discard commits.
- Cost / security / account impact: rotating secrets, changing repo settings / branch protection,
  anything that spends money at scale, anything touching the live Fiverr account credentials.
- A **large** live ScrapFly collection run (significant credit burn). A *small* operator/Agent-E
  live validation sample is normal Tier-A/B activity; a big burn is confirmed first.

### 9.3 The one-line decision test

> Is it reversible, AND does it leave `src/` + `tests/` + config-behavior untouched, AND does it
> not need to pass a gate or a merge? → **PM does it now (Tier A).**
> Does it touch code / tests / config-behavior, or need a gate? → **cursor agent (Tier C).**
> Is it irreversible, or does it have cost / security / account impact? → **ask the user (Tier D).**

### 9.4 What this changes in practice

After each cycle the PM now **directly**: corrects Jira to match merged reality, deletes the merged
cycle branch, removes scratch litter, fixes accidentally-tracked artifacts, reruns verification,
and commits governance/doc updates to `develop` — then writes the next cycle's prompts. It does
**not** patch `src/`, write tests, flip config toggles, or merge code; those remain cursor-agent +
Agent-D work. Every direct action stays inside Tier A/B; anything else is escalated per 9.2.


---

## Section 10: ScrapFly Collection Backend Policy (effective Cycle 054+)

Authoritative policy for the ScrapFly fetch transport. Written from a verified code/config review
(Cycle 053 close): `src/config/models.py::ScrapFlyCollectionConfig`, `src/collection/orchestrator.py`
(`run_collection_pipeline`), `src/collection/http_fetcher.py::build_fetcher`, `config.yaml`,
`run.py`, and `.env`.

### 10.1 What ScrapFly is (verified)

ScrapFly is the **production fetch transport for live Fiverr pages, used to bypass PerimeterX**
(Fiverr's anti-bot system). The config docstring states it directly: *"ScrapFly API settings for
PerimeterX bypass. When enabled, collection workflows use ScrapFly instead of Playwright for page
fetching; all existing HTML parsers are untouched."* The `asp: true` setting (ScrapFly Anti-Scraping
Protection) is the bypass. **Without ScrapFly, live Fiverr fetches fall back to the Playwright /
authenticated-session path, which PerimeterX blocks with 403s.** Treat "no ScrapFly" as "no live
Fiverr data."

### 10.2 How it is wired (verified)

- The orchestrator only builds a fetcher when the run is **live** (`dry_run=False`). It reads
  `collection.scrapfly.enabled`:
  - `true` → opens a `ScrapFlyClient` (API key read from the env var named by `api_key_env_var`,
    default `SCRAPFLY_API_KEY`) and calls `build_fetcher(prefer_scrapfly=True)`.
  - `false` → `build_fetcher(prefer_scrapfly=False, scrapfly_client=None)` → Playwright/session
    fetcher → PerimeterX → 403.
- In **`dry_run=True`** (every automated test, CI, and the `*-dry-run` CLI modes) **no fetcher is
  built and no network occurs.** ScrapFly is irrelevant to dry-run/CI by design.
- **There is no CLI flag to enable ScrapFly.** It is enabled through the **config file** used for a
  live run (`--config-path`), plus the `SCRAPFLY_API_KEY` env var. (`run.py`'s `--config-override`
  exists only on the `score` parity helper and parses only `relevance.enable_stage_3_5`.)

### 10.3 Verified current state

- Committed `config.yaml`: `collection.scrapfly.enabled: false` (with `asp: true`, `render_js: true`
  already configured).
- `.env`: `SCRAPFLY_API_KEY` is **present** (a real `scp-` key; `.env` is gitignored). The key was
  never the blocker.

### 10.4 Why it has been `false` — and the failure it caused

- **Correct part:** the committed default is `false` so that automated tests/CI (which run dry) make
  **zero** live calls and spend **zero** credits, and so no agent accidentally triggers live scraping
  in CI. The "scrapfly stays false" config gate protects the **committed file**.
- **The failure:** live work — Agent E sampling real Fiverr result sets, DL-207 URL-shape capture,
  any real collection run — **requires** ScrapFly. When that work ran against the default disabled
  config it fell back to Playwright and 403-degraded. The disabled committed default was wrongly
  read as "never use ScrapFly," conflating *"committed-off for CI"* with *"off for live work."* That
  is the root cause of the recurring "live sweeps 403-degraded" symptom (incl. Agent E's).

### 10.5 Policy (the durable rule)

1. **ScrapFly is REQUIRED for any live Fiverr fetch.** No ScrapFly → expect 403 → no live data.
2. **The committed `config.yaml` MUST keep `collection.scrapfly.enabled: false`.** Deliberate: keeps
   CI/tests dry and credit-free; this is what the config gate enforces. Committing `enabled: true`
   is a config-gate violation.
3. **Automated tests MUST NEVER make live ScrapFly calls.** They mock `build_fetcher` / the ScrapFly
   client (as existing tests do) or run dry. No live network in CI. (Already a binding rule.)
4. **Live work enables ScrapFly at RUNTIME via a local, uncommitted config — never by committing
   `enabled: true`:**
   - Confirm `SCRAPFLY_API_KEY` is set in the environment (it is, in `.env`).
   - Copy `config.yaml` → `config.live.yaml` (gitignored), set `collection.scrapfly.enabled: true`
     there, and run the live mode with `--config-path config.live.yaml`.
   - Confirm the run is live (`dry_run=False`), then check the ScrapFly session log line
     (`ScrapFly session: requests=… credits=…`) to confirm the bypass transport was actually used.
   - Mind credits (`cost_budget_credits` can cap spend). A **large** live run is a Tier-D action
     (§9.2) — confirm with the user first.
5. **Agent E's live-validation prompt MUST state this explicitly:** live sampling requires ScrapFly
   enabled via a local config + the env key. If ScrapFly is unavailable, Agent E records the
   affected niches as **"[SEED — no live signal]"** and does **not** fabricate counts — rather than
   silently 403-degrading and reporting empty/blocked.
6. **Distinguish the two states everywhere:** committed-config ScrapFly = **OFF** (correct,
   permanent, for CI); live-run ScrapFly = **ON via local override** (required for real Fiverr data).
   The config gate forbids *committing* `enabled: true`; it does **not** forbid *live use*.

### 10.6 `.gitignore`

Add `config.live.yaml` and `config.*.local.yaml` to `.gitignore` so a live (ScrapFly-on) config can
never be committed by accident.

### Version history (Sections 9-10)

| Version | Date | Change |
| --- | --- | --- |
| 1.5 | 2026-05-31 | Added §9 PM Direct-Action Authority (4-tier model: PM directly handles reversible Jira/GitHub/docs/hygiene/verification + commits governance docs; never touches src/, tests/, config-behavior, gates, or irreversible/cost actions). Added §10 ScrapFly Collection Backend Policy (verified PerimeterX-bypass transport; committed-off for CI is correct; live work enables it via local uncommitted config + SCRAPFLY_API_KEY; root-caused the 403-degraded live sweeps). |


---

## Section 11: MODEL-MIGRATION PARITY RULE (effective Cycle 056+)

**Root cause:** C055 BLOCK — Agent B added ORM `Mapped[]` columns to `discovery_outcome.py`
(`run_id`, `niche_id`, `keyword_text`, `created_at`) but wrote "Migration added: No (existing
R8 columns populated)" because the runtime write paths only touched pre-existing columns.
Agent C confirmed "footprint: clean" because no new migration FILE was added. Both checks were
wrong-directional. Only Agent D's G7 PRAGMA probe caught it. Full analysis: see
`PM_Pack/01_pm_instructions/AGENT_B_MIGRATION_PARITY_ROOT_CAUSE.md`.

### 11.1 The invariant (binding on every cycle)

> **Every `Mapped[X]` column in every `src/models/*.py` file that is modified in a cycle MUST
> have a corresponding migration `ADD COLUMN` (or be part of the original table-creation DDL).
> "Tests pass" and "no new migration file" are NOT evidence of compliance. PRAGMA is the test.**

### 11.2 Agent B — pre-commit MODEL-MIGRATION PARITY TABLE (BLOCKING)

Applies whenever any `src/models/*.py` file appears in the cycle diff.

**STEP 1 — Enumerate.** For every `F` in `git diff --name-only develop..HEAD -- src/models/`:
  Open F. List every line matching `Mapped[` with a `mapped_column(...)` assignment.
  Record: column_name | Python type | nullable | has_default

**STEP 2 — Map to migrations.** For each column, find the migration that provides it:
  - Either an `ALTER TABLE <table> ADD COLUMN <column_name>` in any migration_NN file, OR
  - The `CREATE TABLE IF NOT EXISTS` statement that originally defined the table.

**STEP 3 — Build the parity table** (mandatory in HANDOFF_B / AGENT_B report):

  | Column | ORM type | Migration file | DDL line | Present? |
  |--------|----------|----------------|----------|---------|
  | run_id | str|None | migration_10   | ADD COLUMN run_id VARCHAR(64) | YES |
  | ...    | ...      | ...            | ...      | ...     |

**STEP 4 — For any row where Present=NO:** Immediately write a new migration file using the
  idempotent `_add_column()` pattern from `migration_06` or `migration_09`:

```python
"""MNN: add <column(s)> to <table>."""
from sqlalchemy import Engine

def _add_column(connection, table_name, ddl):
    try:
        connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
    except Exception:
        return

def apply(engine: Engine) -> None:
    with engine.begin() as connection:
        _add_column(connection, "<table>", "<col_name> <TYPE> [DEFAULT ...]")
```

  Register it in `run_srdi_r8_migrations.py` after the highest-numbered existing import+call.
  Run `apply()` against `data/foundation_gate_ci.db`. Verify via PRAGMA. Include in commit.
  DO NOT commit any src/models change without a complete, all-YES parity table.

### 11.3 Agent C — mandatory PRAGMA cross-check (GO/NO-GO, BLOCKING)

Applies whenever any `src/models/*.py` file appears in the cycle diff.

For every modified model file, run:

```bash
py -3.12 -c "
from sqlalchemy import create_engine, inspect
e = create_engine('sqlite:///data/foundation_gate_ci.db')
cols = {c['name'] for c in inspect(e).get_columns('<tablename>')}
print('DB columns:', sorted(cols))
"
```

Then list ORM Mapped[] columns from the model file. Every ORM column must appear in DB cols.
ANY gap = IMMEDIATE NO-GO. Route fix to Agent B. Record result in AGENT_C report.

### 11.4 Table name map

| Model file | Table name |
|------------|------------|
| discovery_outcome.py | discovery_outcomes |
| keyword_score.py | keyword_scores |
| keyword.py | keywords |
| gig.py | gigs |
| search_result.py | search_results |
| external_signal.py | external_signals |
| result_set_validation.py | result_set_validations |
| market.py | markets |
| competitor_profile.py | competitor_profiles |

### 11.5 C056 one-time retroactive audit

C056 Agent B MUST run the MODEL-MIGRATION PARITY AUDIT on ALL 9 model files above.
Produce one consolidated parity table in CYCLE_056_AGENT_B.md. Any gap found = write migration.
Document results even if all rows are YES — the audit itself is the deliverable.

### Version history (Section 11)

| Version | Date | Change |
| --- | --- | --- |
| 1.8 | 2026-06-01 | Added §11 MODEL-MIGRATION PARITY RULE: root-caused C055 G7 block; added §11.2 Agent B pre-commit parity table (BLOCKING) + §11.3 Agent C PRAGMA cross-check (BLOCKING) + §11.4 table map + §11.5 C056 retroactive audit. Ref: AGENT_B_MIGRATION_PARITY_ROOT_CAUSE.md. |

---

## Section 12: PARALLEL EXECUTION CONTRACT (effective Cycle 057+)

Added after C056 failures: Agent E panicked at Agent B's commits on the shared branch;
Agent C was told to wait for Agent F (which runs AFTER C); Agent D had no playbook for
known GitHub operational issues.

### 12.1 Stage-2 parallel execution (B + E)

Agents B and E run simultaneously on the same branch (`cycle/[N]/integration`). They are
aware of each other. Each prompt MUST state explicitly at the top:

> **PARALLEL EXECUTION NOTICE — YOU ARE RUNNING IN PARALLEL WITH AGENT [X].**
> Agent [X] is simultaneously committing [their zone] to this same branch.
> When you run `git log`, you WILL see Agent [X]'s commits. This is EXPECTED and CORRECT.
> DO NOT halt, alarm, or report unexpected commits — they are Agent [X]'s normal work.

#### 12.1.1 Zone verification rule (binding — fixes the C056 E panic)

Zone compliance MUST be verified by checking only the agent's OWN commit SHA(s), not the
entire branch diff. The correct command is:

```powershell
# Get your own commit SHA (the one you just pushed):
$MY_SHA = Invoke-Exe git `rev-parse HEAD`
# Verify only YOUR commit's files:
Invoke-Exe git `show --name-only $MY_SHA`
# Expected: only YOUR zone files. B's or E's commits elsewhere on the branch = NORMAL.
```

NEVER use `git diff --name-only origin/develop..HEAD` for zone compliance — that command
shows ALL commits on the branch, including the parallel agent's commits, and will produce
false positives.

#### 12.1.2 What each parallel agent commits (B and E must know each other's zone)

| Agent | May commit | Must NEVER commit |
|-------|-----------|-------------------|
| B | `src/` files + `CYCLE_[N]_AGENT_B.md` | `tests/`, `PM_Pack/`, `config.yaml`, `.env` |
| E | `docs/cycle_reports/CYCLE_[N]_AGENT_E.md` only | `src/`, `tests/`, `config.yaml` |

Both agents see each other's commits in `git log`. Both verify only their own commits.

#### 12.1.3 Startup sync for parallel agents

Each agent MUST run `git pull origin cycle/[N]/integration` before beginning any work and
again before committing. This ensures each agent is building on the most recent state.
If a pull brings in new commits from the parallel agent: acknowledge, do not act on them.

### 12.2 Stage order and inter-agent dependencies (DEFINITIVE)

The 5-stage execution order is:
```
Stage 1:  Agent A (solo)
Stage 2:  Agent B + Agent E (parallel, independent)
Stage 3:  Agent C (after BOTH B AND E — NOT after F)
Stage 4:  Agent F (after Agent C issues GO)
Stage 5:  Agent D (after ALL of A, B, E, C, F)
```

**Agent C prerequisites = B AND E only.** C runs BEFORE F. C NEVER waits for F.
**Agent F prerequisite = C's GO verdict.** F creates the artifacts C cannot verify.
**Agent D verifies F's artifacts.** D verifies all 5 prior agents' work.

Any prompt that lists F as a prerequisite for C is WRONG. Any prompt that lists C as a
prerequisite for F is correct.

#### 12.2.1 What each stage verifies

| Agent | Verifies | Does NOT verify |
|-------|----------|----------------|
| C | B's parity audit, ruff, mypy, regressions, golden parity, config gate, §11.3 PRAGMA | F's fixture factories, F's suite guard, F's integration tests |
| D | Everything: B, E, C, F, and D's own gate battery | Nothing is assumed from prior agents |

C's prompt must NOT include verification tasks for F's artifacts. D's prompt includes
verification of both C's and F's work.

### 12.3 Agent D: known GitHub operational issues playbook

Agent D encounters these issues on every 2-3 cycles. The playbook is mandatory in D's prompt.

#### 12.3.1 PR too large (>1000 lines changed)

GitHub rejects the merge with:
```
Error: PR is too large: N lines changed (max 1000). Consider splitting or add override:large-pr label.
```

**Fix (30 seconds):**
```powershell
Invoke-Exe gh `api -X POST repos/KevinSGarrett/Fiverr/issues/<PR_NUM>/labels --field "labels[]=override:large-pr"`
```
After adding the label, re-attempt the squash merge. The label bypasses the size check.
Note: cycle PRs accumulate fixtures, migration files, and test files — they will routinely
exceed 1,000 lines. Always check for this before the merge attempt.

#### 12.3.2 Codex review thread resolution

Codex review threads must be resolved BEFORE merge (G-002). Steps:
1. Run GraphQL reviewThreads query (see D's prompt for exact query).
2. For each `isResolved: false` thread:
   a. Read the thread body to understand what it flagged.
   b. If the code issue was already fixed by Agent B: reply to the thread citing the fix commit SHA.
   c. Mark the thread resolved:
      ```powershell
      # Via GitHub web UI: navigate to PR → find thread → click "Resolve conversation"
      # Or via API if the thread nodeId is known:
      Invoke-Exe gh `api graphql -f "mutation { resolveReviewThread(input: {threadId: \"<nodeId>\"}) { thread { isResolved } } }"`
      ```
   d. If the code issue was NOT fixed: route to Agent B for a real fix before merging.
3. Run the GraphQL query a SECOND time to confirm all threads resolved.

#### 12.3.3 codecov/patch failing (advisory — not a merge blocker)

`codecov/patch` failing does NOT block the merge. The ENFORCED gates are:
- CI "Lint, Typecheck, Tests, and Gates" = success
- `codecov/project` = success (project floor ≥ 90%)

If `codecov/patch` fails:
1. Record the state in CYCLE_[N]_AGENT_D.md.
2. Determine whether the uncovered diff is real logic or migration boilerplate/defensive branches.
3. If real logic: route to Agent F as a coverage gap for the next cycle.
4. If migration boilerplate/defensive `except` blocks: document the judgment call and proceed.
5. Do NOT block the merge solely due to `codecov/patch`.

#### 12.3.4 CI check-run not yet complete (pending)

If CI checks show `status: in_progress` when D queries them:
```powershell
# Wait 60 seconds and re-query:
Start-Sleep -Seconds 60
Invoke-Exe gh `api repos/KevinSGarrett/Fiverr/commits/<HEAD_SHA>/check-runs --jq ".check_runs[] | {name,status,conclusion}"`
```
Repeat up to 5 times (5 minutes total). If still pending after 5 minutes: check GitHub for
a stuck runner. Do NOT proceed to merge while any enforced check shows `in_progress`.

#### 12.3.5 mergeable_state: "blocked" vs "unstable"

- `mergeable_state: "blocked"` = branch protection rule is failing (enforced check failed). DO NOT merge.
- `mergeable_state: "unstable"` = only a non-required check failed (typically `codecov/patch`). Merge is allowed.
- `mergeable_state: "clean"` = all required checks pass. Proceed.
- `mergeable_state: "unknown"` = GitHub is still computing. Wait 30 seconds and re-query.

### 12.4 SRDI project plan reference protocol

The SRDI initiative specs live in BOTH:
- `PM_Pack/ref/project_plan/13_srdi/` — SRDI-specific specs (epics, roadmap, DoD, migrations, test plan)
- `PM_Pack/ref/project_plan/` (other directories) — base system specs (collection, scoring, analysis)

When an agent's cycle scope is SRDI work (R1-R11), it MUST read the relevant epic file:
  `PM_Pack/ref/project_plan/13_srdi/epics/R[N]_[EPIC_NAME].md`

AND cross-reference with the base spec for the affected subsystem:
  - R1 (search URL): `04_collection/` + `13_srdi/epics/R1_SEARCH_URL_HARDENING.md`
  - R2 (relevance): `06_analysis/` + `13_srdi/epics/R2_RELEVANCE_VALIDATION_STAGE_3_5.md`
  - R4 (scoring): `05_scoring/` + `13_srdi/epics/R4_SCORING_INTEGRITY_EXTENSIONS.md`
  - R5 (LLM): `06_analysis/` + `13_srdi/epics/R5_LLM_RELEVANCE_STAGE_7_5.md`
  - R6 (discovery): `10_discovery/` + `13_srdi/epics/R6_DISCOVERY_RELEVANCE_GATES.md`
  - R7 (external): `06_analysis/` + `13_srdi/epics/R7_EXTERNAL_SIGNAL_INTEGRITY.md`
  - R9 (testing): `06_test_plan/` + `13_srdi/epics/R9_TESTING_VALIDATION_FRAMEWORK.md`

The sequencing roadmap for all SRDI cycles is:
  `PM_Pack/ref/project_plan/13_srdi/07_SEQUENCING_ROADMAP.md`

Agents writing prompts or doing planning MUST read both sources. "Go read the project plan"
without specifying both the base spec directory and the 13_srdi epic file is insufficient.

### 12.5 Revised prompt-length floors (replaces §8.3 — effective Cycle 057+)

After C056 analysis: the previous floors (A810/B945/E810/C675/F810/D945 = 4,995 total) caused
excessive generation time and encouraged padding over substance. The floors are recalibrated to
what 25 LARGE-XXXLARGE tasks with full inline content actually require.

The quality gate shifts from "line count" to "Depth + Line count":

**Revised floors:**

| Agent | Old floor | New floor | Rationale |
|-------|-----------|-----------|-----------|
| A | 810 | 500 | Planner/scaffold: context + handoffs + 25 tasks |
| B | 945 | 650 | Implementer: needs inline code templates + parity audit tables |
| E | 810 | 500 | Live validation: ScrapFly runbook + report template + 25 tasks |
| C | 675 | 425 | Verifier: verification commands + PRAGMA + report template |
| F | 810 | 525 | Coverage: fixture code + test stubs + 25 tasks |
| D | 945 | 650 | Merge gate: all 10 gates + ceremony + Jira plan |
| **Total** | **4,995** | **3,250** | 35% reduction |

**Depth Quality Gate (replaces pure line counting as the primary quality signal):**

Every prompt MUST pass ALL of the following before release:
1. **Line floor**: meets the per-agent line floor above
2. **Task count**: ≥ 25 tasks, each LARGE-XXXLARGE with numbered sub-steps
3. **Specificity**: every task names ≥ 1 specific file path, command, Jira key, or function name
4. **No duplication**: no two consecutive tasks share the same command structure
5. **Inline content**: code templates, command blocks, or report templates are INLINE (not "go read X")
6. **Stage correctness**: agent's prerequisites and stage number match §12.2 exactly
7. **Parallel awareness**: B and E prompts contain the §12.1 parallel execution notice
8. **Operational playbook**: D's prompt contains the §12.3 known-issues playbook (PR size, Codex, codecov)

A prompt that passes the depth quality gate but is slightly under the line floor: acceptable if
the PM documents why (all mandatory blocks are present, content is complete).
A prompt at or above the line floor but failing any depth quality check: NOT DONE.

### Version history (Section 12)

| Version | Date | Change |
| --- | --- | --- |
| 1.9 | 2026-06-01 | Added §12 PARALLEL EXECUTION CONTRACT: §12.1 B+E parallel awareness rule + zone verification fix (use `git show --name-only <OWN_SHA>`, never `git diff origin/develop..HEAD`); §12.2 definitive stage order + inter-agent dependency table (C runs before F, not after); §12.3 Agent D operational issues playbook (PR too large, Codex resolution, codecov/patch, mergeable_state); §12.4 SRDI project plan reference protocol (13_srdi + base spec cross-reference); §12.5 revised prompt-length floors (4,995 → 3,250 total; depth quality gate replaces pure line counting). Root cause: C056 multi-agent failures. |

---

## Section 13: PM OPERATING RULES (effective Cycle 057+)

Added after C056 session failures. These are binding rules on the PM role — not guidelines.
Every rule exists because a specific mistake was made. Each one is enforced by a concrete
check, not by good intentions.

### 13.1 VERIFY STATE BEFORE ANSWERING (binding — no exceptions)

Before answering ANY question about execution order, current cycle, what to run next, or
what has been completed: the PM MUST run these two commands and read the output.

```powershell
# Command 1: What is actually on develop?
Invoke-Exe git `log origin/develop --oneline -5`

# Command 2: Are any PRs open?
Invoke-Exe gh `api "repos/KevinSGarrett/Fiverr/pulls?state=open" --jq ".[].number + \": \" + .title"`
```

If both commands show no open PRs and the develop HEAD matches the last known squash SHA:
  → The prior cycle is COMPLETE. Do not reference prior cycle prompts.
  → The current cycle is whatever is NEXT. Reference only that cycle's prompts.

If a PR is open:
  → That cycle is IN PROGRESS. Reference that cycle's agents.

**Never answer "what do I run next" from memory. Always check git first.**

Root cause this prevents: Told user to run C055 + C056 prompts when both were already merged.

### 13.2 SHA PLACEHOLDERS MUST BE RESOLVED BEFORE PROMPTS ARE PUBLISHED (binding)

When a new cycle's prompts are written, they contain `[CXXX_SQUASH_SHA]` placeholders.
The PM MUST resolve these placeholders BEFORE the prompts are considered ready to use.

Resolution steps (PM does these directly — Tier A):
1. Get the actual squash SHA: `Invoke-Exe gh `api repos/KevinSGarrett/Fiverr/pulls/<PR> --jq .merge_commit_sha``
2. Run the SHA resolver: `PM_Pack\03_cursor_agent_system\SHA_RESOLVER_SCRIPT.ps1`
3. Verify no placeholders remain: `Select-String '\[C0\d\d_SQUASH_SHA\]' <prompt_file>`
4. Only after step 3 confirms clean: prompts are ready to hand to agents.

A prompt with an unresolved `[CXXX_SQUASH_SHA]` placeholder is NOT ready to use.
If the squash SHA is not yet known (prior cycle not yet merged): the prompts are not ready.
Do not hand them to agents until the SHA is known and replaced.

Root cause this prevents: Agent A was told to do the SHA replacement, creating unnecessary work.

### 13.3 SCRATCH FILES ARE CLEANED IMMEDIATELY (binding)

Any .ps1, .txt, or .md file created as scratch/audit/temporary work must be deleted
the moment it is no longer needed — not at the end of a session, not "later."

Pattern:
  Create scratch file → use it → delete it → THEN continue to next task.
  Never: Create scratch → create more scratch → create more scratch → cleanup at end.

Before ending any session or answering any "is everything done?" question:
  List PM_Pack\*.ps1, PM_Pack\*.txt → must be empty or only permanent files.
  List PM_Pack\03_cursor_agent_system\*.ps1, *.txt → must be empty.

Root cause this prevents: Accumulated ping.txt, counts_out.txt, audit_check.ps1, go.ps1, etc.

### 13.4 STRUCTURAL RULES FOR CURSOR AGENT PROMPTS (binding)

Every cursor agent prompt MUST comply with all of the following. Any violation means
the prompt is not done.

a) "END OF PROMPT" marker appears EXACTLY ONCE, at the very last line.
   If it appears twice: the file has duplicate sections. Fix before releasing.

b) "TASK 0" (if present) must appear in the first 30 lines of the file, BEFORE PREFLIGHT.
   A "do this first" instruction buried at line 400 after two "END OF PROMPT" markers
   will be missed or read too late. If it's critical enough to be Task 0, it must be first.

c) No instruction says "run this command yourself" or "paste this PowerShell" when the
   PM can run it directly via Desktop Commander. The PM uses Desktop Commander. The PM
   does not ask the user to run scripts.

d) All cross-references are to specific file paths, not to "the project plan" generically.
   If the agent needs to read a spec: name the exact file. (§12.4 codifies SRDI nav.)

Root cause this prevents: Task 0 at bottom of A prompt; multiple END OF PROMPT markers;
asking user to run PowerShell commands.

### 13.5 STAGE ORDER VERIFICATION BEFORE PROMPT RELEASE (binding)

Before releasing any set of 6 prompts, the PM verifies the stage order is consistent
across ALL 6 files. The definitive check:

```powershell
$dir = 'C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system'
$cycle = '057'  # update per cycle
foreach ($a in @('A','B','C','D','E','F')) {
    $f = "$dir\CYCLE_0${cycle}_AGENT_${a}_PROMPT.md"
    $stage = (Get-Content $f | Select-String "Stage [0-9]" | Select-Object -First 1).Line
    $waitfor = (Get-Content $f | Select-String "after.*Agent" | Select-Object -First 1).Line
    Write-Output "${a}: $stage | $waitfor"
}
```

Expected output pattern:
  A: Stage 1 (solo)
  B: Stage 2 (parallel with E) | after Agent A
  C: Stage 3 (after BOTH B AND E — NOT after F)
  F: Stage 4 (after C issues GO)
  D: Stage 5 (after all 5 agents)
  E: Stage 2 (parallel with B)

If Agent C says "after F" or "after Agent F": fix it before releasing. This is the exact
error that broke C056.

Root cause this prevents: Agent C's prompt listing F as a prerequisite.

### 13.6 PARALLEL AGENT NOTICE IS MANDATORY IN B AND E PROMPTS (binding)

Every Agent B prompt and every Agent E prompt MUST contain the §12.1 parallel execution
notice within the first 25 lines. The notice must name the other parallel agent explicitly.

Check before releasing:
```powershell
Get-Content "CYCLE_0${cycle}_AGENT_B_PROMPT.md" | Select-Object -First 25 | Select-String "PARALLEL"
Get-Content "CYCLE_0${cycle}_AGENT_E_PROMPT.md" | Select-Object -First 25 | Select-String "PARALLEL"
```
Both must return a match. If either returns nothing: the parallel notice is missing or in
the wrong position. Fix before releasing.

Zone verification in each prompt must use `git show --name-only <OWN_SHA>` NOT
`git diff --name-only origin/develop..HEAD`. Verify this is the pattern in both prompts:
```powershell
Get-Content "CYCLE_0${cycle}_AGENT_B_PROMPT.md" | Select-String "show --name-only"
Get-Content "CYCLE_0${cycle}_AGENT_E_PROMPT.md" | Select-String "show --name-only"
```
Both must return a match.

Root cause this prevents: Agent E halting when it saw Agent B's commits on the branch.

### 13.7 AGENT D OPERATIONAL PLAYBOOK IS MANDATORY (binding)

Every Agent D prompt MUST contain procedures for all four known operational issues:
1. PR too large (override:large-pr label command)
2. Codex thread resolution (reply with fix SHA + resolve)
3. codecov/patch advisory (document, proceed if project floor passed)
4. mergeable_state values (clean/unstable/blocked/unknown)

Check before releasing:
```powershell
$d = Get-Content "CYCLE_0${cycle}_AGENT_D_PROMPT.md" -Raw
@("override:large-pr","Codex","codecov/patch","mergeable_state") | ForEach-Object {
    if ($d -match [regex]::Escape($_)) { "PRESENT: $_" } else { "MISSING: $_" }
}
```
All four must show PRESENT. Any MISSING = prompt is not done.

Root cause this prevents: Agent D having no playbook for "PR is too large: 2637 lines."

### 13.8 PRE-RELEASE CHECKLIST (blocking — run before handing any prompt to an agent)

This is the complete pre-release gate the PM runs before marking any prompt ready.
All items must be checked. No prompt ships until every item is YES.

```
BEFORE RELEASING CYCLE_0NN PROMPTS:

STATE VERIFICATION
[ ] git log origin/develop --oneline -5 run and output read → prior cycles confirmed merged
[ ] gh api open PRs run → no unexpected open PRs

SHA RESOLUTION
[ ] All [CXXX_SQUASH_SHA] placeholders replaced → Select-String confirms no matches
[ ] SHA resolver ran successfully → output showed "N file(s) updated"

STRUCTURAL
[ ] "END OF PROMPT" appears exactly once in each file (not twice)
[ ] Task 0 (if present) is in first 30 lines (not appended at end)
[ ] No "paste this script yourself" instructions in any prompt
[ ] All spec references name exact file paths

STAGE ORDER
[ ] A: solo | B: parallel with E | C: after B+E (NOT F) | F: after C | D: after all 5
[ ] Verified via stage-order check script (§13.5)

PARALLEL AGENTS
[ ] B prompt: §12.1 parallel notice in first 25 lines, names Agent E
[ ] E prompt: §12.1 parallel notice in first 25 lines, names Agent B
[ ] Both B and E use `git show --name-only <OWN_SHA>` for zone verification

AGENT D PLAYBOOK
[ ] override:large-pr command present
[ ] Codex x2 resolution present
[ ] codecov/patch advisory present
[ ] mergeable_state guide present

LINE FLOORS AND DEPTH (§12.5)
[ ] A≥500, B≥650, E≥500, C≥425, F≥525, D≥650
[ ] All 7 depth quality checks pass per file

SCRATCH CLEANUP
[ ] No .ps1 or temporary .txt files in PM_Pack\ or PM_Pack\03_cursor_agent_system\
```

### 13.9 WHAT THE PM NEVER DOES (hard prohibitions)

These actions by the PM are ALWAYS wrong. No circumstance justifies them.

1. NEVER answers "what do I run next" without first running the git state verification (§13.1).
2. NEVER publishes a prompt with an unresolved `[CXXX_SQUASH_SHA]` placeholder.
3. NEVER tells the user to run a PowerShell command when the PM can do it via Desktop Commander.
4. NEVER leaves scratch files on disk after the task that created them is complete.
5. NEVER gives a list of prompts to run that includes already-completed cycles.
6. NEVER writes "Task 0 — do this first" at the bottom of a file.
7. NEVER writes a stage-order prompt that has Agent C waiting for Agent F.
8. NEVER assumes the current cycle without reading the hydration header and git log.

### Version history (Section 13)

| Version | Date | Change |
| --- | --- | --- |
| 1.9 | 2026-06-01 | §13 PM OPERATING RULES added: §13.1 verify-state-before-answering; §13.2 SHA resolution before publish; §13.3 immediate scratch cleanup; §13.4 structural prompt rules; §13.5 stage order verification; §13.6 parallel notice mandatory; §13.7 D operational playbook mandatory; §13.8 pre-release checklist; §13.9 hard prohibitions. All rules traced to specific C056 failures. |

---

## Section 14: ENVIRONMENT CONFIGURATION & LIVE COLLECTION PROTOCOL (effective Cycle 059+)

Added after C058 — three consecutive cycles where Agent E ran in SEED mode despite a valid
SCRAPFLY_API_KEY being present. Root cause: agents checked `$env:SCRAPFLY_API_KEY` (Windows
system environment) instead of reading from the `.env` file. The key is in the file, not the
system environment on this machine.

### 14.1 .ENV FILE IS THE AUTHORITATIVE SECRET SOURCE

All API keys, tokens, and configuration values for this project live in:
  `C:\Fiverr\Fiverr\.env`

Current documented keys (presence only — never print values):
  OPENAI_API_KEY         prefix: sk-  (len≈164) — used by R5 LLM classifier
  SCRAPFLY_API_KEY       prefix: scp- (len≈41)  — used by Agent E live collection
  DATABASE_URL           prefix: sqlite (len≈33) — default DB path
  REDDIT_CLIENT_ID       present — Reddit API access
  REDDIT_CLIENT_SECRET   present — Reddit API access
  REDDIT_USER_AGENT      present — Reddit API user agent string

**The system `$env:SCRAPFLY_API_KEY` will be EMPTY unless explicitly loaded from `.env`.**
Checking `$env:SCRAPFLY_API_KEY` directly will return null and agents will falsely report SEED.

### 14.2 MANDATORY ENV LOADING STEP (§10.5 addendum)

Every Agent E prompt and every cursor agent that does live collection MUST include this step
as the FIRST action in any collection task:

```powershell
# Load .env into current PowerShell session (§14.2 — mandatory before any API call)
Get-Content 'C:\Fiverr\Fiverr\.env' | ForEach-Object {
  if ($_ -match '^([A-Z0-9_]+)=(.+)$') {
    [System.Environment]::SetEnvironmentVariable($Matches[1], $Matches[2], 'Process')
  }
}
# Verify the key is now accessible
$k = $env:SCRAPFLY_API_KEY
if ($k -and $k.StartsWith('scp-')) { Write-Output "SCRAPFLY_API_KEY: LOADED (prefix=$($k.Substring(0,6)))" }
else { Write-Output "SCRAPFLY_API_KEY: MISSING OR WRONG PREFIX — CHECK .env" }
```

If the key is loaded successfully: proceed with live collection.
If the key is missing from .env: fallback to [SEED — key missing from .env] per §10.5.

Python equivalent (for use in run.py scripts):
```python
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  # loads C:\Fiverr\Fiverr\.env into os.environ
```

The codebase already uses python-dotenv (check requirements). load_dotenv() is the correct
Python-side approach. Agents should confirm dotenv is loaded before assuming keys are in env.

Root cause this prevents: 3 consecutive SEED cycles (C056/C057/C058) despite key being present.

### 14.3 THROWAWAY DB SEEDING REQUIREMENT

**The pipeline CANNOT collect data into an empty DB.** If the throwaway DB has no niche rows,
the pipeline falls back to the `dry_run` niche ID, emits `https://dry-run-test.invalid/` URLs,
and silently skips all niche-resolved keyword writes.

Evidence from C058 Agent E:
  "Unable to resolve niche 'prd_ai_saas' to a DB primary key; skipping keyword writes."
  "Unknown or missing niche_id='dry_run'; falling back to NONE strictness URL."
  "<-- 400 | Invalid hostname, given https://dry-run-test.invalid/"

**The dry-run fallback is NOT a ScrapFly error. It is a missing-niche-seed error.**

Mandatory seeding step before any throwaway DB live collection:
```powershell
# Run foundation-gate to initialize the throwaway DB with all migrations + niche rows
py -3.12 run.py foundation-gate --database-url sqlite:///data/cycle0NN_e2e_validation.db
# Verify niches are seeded
py -3.12 -c "
from sqlalchemy import create_engine
e=create_engine('sqlite:///data/cycle0NN_e2e_validation.db')
r=e.connect().exec_driver_sql('SELECT COUNT(*) FROM niches').fetchone()
print('niches seeded:', r[0], '(must be 9)')
"
```
If `niches seeded: 9` → proceed with live collection.
If `niches seeded: 0` → DB is empty; run foundation-gate first.

Root cause this prevents: dry-run fallback contamination in Agent E's throwaway DB runs.

### 14.4 EXTERNAL SIGNAL SCHEMA REALITY (not the spec — the actual db columns)

The `external_signals` table as built by C058 Agent B uses THESE column names:
  PRESENT:  id, keyword_id, run_id, signal_type, signal_value, signal_json, source_url,
            collected_at, ttl_hours, is_stale, collection_method, error_message,
            created_at, updated_at
  ABSENT (spec names that were NOT implemented):
    raw_value        → use signal_value instead
    relevance_score  → NOT a column; compute from external context if needed
    trend_direction  → NOT a column; stored inside signal_json
    buyer_intent_posts / total_posts → NOT columns; stored inside signal_json

**All Agent E diagnostic SQL queries MUST use `signal_value`, NOT `raw_value`.**
**Trend direction and buyer intent ratio must be extracted from `signal_json`, not a column.**

The spec-vs-implementation gap is a Tier-C carry-forward item for Agent B in a future cycle.
C059 Agent B should add the missing columns as a follow-up if needed for R10 display.
For now: Agent E prompts use `signal_value` and `signal_json` extraction for all queries.

### 14.5 LIVE COLLECTION VALIDATION CHECKLIST (§10.5 replacement)

The §10.5 ScrapFly Live-Enable Runbook is extended with these mandatory steps:

```
AGENT E LIVE COLLECTION CHECKLIST (run in order — all must PASS):

[ ] 1. Load .env: Get-Content .env | ForEach-Object { if ($_ -match ...) { SetEnv } }
        Confirm: SCRAPFLY_API_KEY loaded with scp- prefix

[ ] 2. Seed throwaway DB: py -3.12 run.py foundation-gate --database-url sqlite:///data/cycle0NN_e2e.db
        Confirm: SELECT COUNT(*) FROM niches → 9

[ ] 3. Write config.live.yaml with collection.scrapfly.enabled: true

[ ] 4. Run collection against throwaway DB (NOT cycle037_live.db):
        py -3.12 run.py [collection_mode] --niche [target_niche] \
          --config-path config.live.yaml \
          --database-url sqlite:///data/cycle0NN_e2e.db

[ ] 5. Check for dry-run contamination:
        If "Unable to resolve niche" appears in logs: DB not seeded → re-run step 2
        If "dry-run-test.invalid" appears: fallback triggered → check niche seeding
        If "ScrapFly attempt N/3 failed" with invalid hostname: dry-run fallback → step 2

[ ] 6. Confirm live data: SELECT signal_type, COUNT(*) FROM external_signals GROUP BY signal_type
        If 0 rows all types + [SEED]: ScrapFly key not loaded or collection mode wrong
        If some rows: PARTIAL — record which types have data

[ ] 7. Per §10.5: never fabricate counts. Record exact status per type.
        If any step fails: document as SEED or PARTIAL with specific failure reason.
```

---

## Section 15: AGENT D MERGE TIMING AND REPORT PLACEMENT PROTOCOL (effective Cycle 059+)

Added after C058 — Agent D merged PR #67 before the Codex review bot completed, resulting in
two P2 findings after the merge that required a post-merge follow-up commit. The correct
protocol requires waiting for Codex to complete BEFORE merging.

### 15.1 CODEX REVIEW BOT TIMING

The chatgpt-codex-connector bot runs ASYNCHRONOUSLY. It may take 5-15 minutes after CI
completes to post its review threads. If D queries GraphQL and sees 0 threads, it does NOT
mean the bot has finished — it may not have started yet.

**Before merging, D MUST confirm Codex has completed:**

```powershell
# Check that Codex has run by looking for its review submissions
Invoke-Exe gh 'api repos/KevinSGarrett/Fiverr/pulls/<PR>/reviews --jq ".[] | {user:.user.login, state, submitted_at}"'
```

Expected: at least one entry from `chatgpt-codex-connector` with `state: "COMMENTED"`.
If Codex has not appeared: wait up to 15 minutes after CI "Lint, Typecheck, Tests, and Gates" = success.
After 15 minutes with no Codex review: document "Codex bot did not run — proceed after 15min wait."

**D's merge gate is BLOCKED until Codex has either:**
  a) Run and found 0 threads (all clear), OR
  b) Run, found threads, and all are resolved, OR
  c) Not appeared after 15+ minutes (documented non-blocking skip)

Root cause this prevents: PR #67 had two P2 findings appear 14 minutes post-merge.

### 15.2 POST-MERGE CODEX MONITORING (mandatory — 1 hour window)

Even when D merges with 0 Codex threads, D MUST:
1. Check Codex threads again 30-60 minutes after merge
2. If new threads appear: immediately route to Agent B (or whichever agent owns src/)
3. B fixes the issue, adds regression tests, commits to develop directly
4. D resolves the threads and records the fix SHA in D's report

This is exactly what happened in C058 (correctly — but it must be in the protocol).
The fix commit should follow the pattern: `fix(scope): [description of codex p2 fix]`
Regression tests for the fix are mandatory — they prevent the same issue from recurring.

Root cause this prevents: undocumented post-merge fixes that bypass the gate process.

### 15.3 AGENT CYCLE REPORT PLACEMENT — HARD RULE

Every cursor agent's cycle report MUST be committed to:
  `docs/cycle_reports/CYCLE_0NN_AGENT_[LETTER].md`

NOT to:
  `CYCLE_0NN_AGENT_B.md` (repo root)  ← C058 B report was placed here — WRONG
  `PM_Pack/05_cycle_reports/` (plan files go here, not reports)
  Any other location

**The PM review checklist reads from `docs/cycle_reports/` only.**
A report at the repo root will NOT be found by the PM review and will appear as MISSING.

In every Agent B prompt: the zone check must explicitly state:
  "B commits `docs/cycle_reports/CYCLE_0NN_AGENT_B.md` — NOT to the repo root."

In every Agent D prompt: before squash-merge, verify all 6 report paths:
  Get-ChildItem `docs/cycle_reports` -Filter "CYCLE_0NN_AGENT_*.md" | Measure-Object → Count=6

Root cause this prevents: CYCLE_058_AGENT_B.md appearing at repo root, PM review showing MISSING.

### 15.4 POST-MERGE REGRESSION TESTS ARE PERMANENT (§7 update protocol)

If any Codex P2 finding is fixed post-merge AND regression tests are added:
  - Those tests become PERMANENT regression pack members
  - D or PM must update §7 within the same session as the fix
  - Tests added post-merge as Codex fixes follow the same REG-NN naming convention

Example: C058 commit `7fcfe41` added 3 tests that should be REG-31/32/33.
These protect against the datetime naive/aware bug and confidence blend bug.
They were not added to §7 v2.1 because they occurred after D's governance commit.
This section requires that such tests be added retroactively in the PM review.

### Version history (Sections 14-15)

| Version | Date | Change |
| --- | --- | --- |
| 2.0 | 2026-06-02 | §14+§15 added: env/ScrapFly protocol; throwaway DB seeding; external signal schema; Codex timing; report placement; post-merge regression tracking. All traced to C058 failures. |

### Cycle 058 post-merge Codex-fix additions — MERGED (pack now 34 after 7fcfe41)

Two P2 Codex findings from PR #67 were fixed post-merge in commit `7fcfe41`
(`fix(scoring): harden external-signal confidence context edge cases`).
Regression tests added in that commit are permanent pack members:

| # | Test name | File | Purpose |
| --- | --- | --- | --- |
| 32 | `test_external_signal_quality_not_blended_without_signal_context` (REG-31) | `tests/unit/test_confidence_score.py` | Freshness×relevance blend must be SKIPPED when external_signal_context_present=False (Codex P2 fix: confidence was incorrectly raised even without real signal data) |
| 33 | `test_external_signal_quality_blended_when_signal_context_present` (REG-32) | `tests/unit/test_confidence_score.py` | Freshness×relevance blend APPLIES when external_signal_context_present=True (positive path) |
| 34 | `test_confidence_context_handles_naive_external_signal_timestamp` (REG-33) | `tests/unit/test_scoring_pipeline.py` | Pipeline confidence context handles naive (non-UTC-aware) ExternalSignal.collected_at without TypeError (Codex P2 fix: naive datetime cannot be subtracted from UTC-aware datetime.now()) |

REG-31/32/33 added post-merge in C058 commit `7fcfe413afe1b8d7d5425941dfae1c3e91957847`,
backfilled to permanent pack in C058 PM review 2026-06-02.

**Pack status after C058 PM review: 34 names (expected passed: 42)**

---

### §7 Version history update

| Version | Date | Change |
| --- | --- | --- |
| 2.2 | 2026-06-02 | C058 PM review: backfilled post-merge Codex P2 fix regressions REG-31/32/33 (datetime normalization + confidence blend guard). Pack now 34 names (42 passed). §14+§15 added (env loading; throwaway DB seeding; external signal schema; Codex timing; report placement). |

