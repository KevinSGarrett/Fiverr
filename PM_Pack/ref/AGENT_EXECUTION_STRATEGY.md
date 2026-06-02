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
