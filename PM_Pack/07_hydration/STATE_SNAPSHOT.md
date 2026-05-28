# State Snapshot - Cycle 047

Updated: 2026-05-27 | Agent A setup in progress on branch `cycle/047/integration`

## Repository and Branch Baseline

- Canonical working directory: `C:\Fiverr\Fiverr`
- Active branch: `cycle/047/integration`
- Branch created from develop SHA: `429b953ccc9cadfd2622e032d733d8be79f974bb`
- PR #53 merge commit verified on develop history: `96807ed9edada4deea34c416a4ce58060b14fa69`
- Worktree count: `1` (`C:/Fiverr/Fiverr`)
- Config safety check: ScrapFly default remains disabled

## Test and CLI Baseline

- Focused preflight bundle: `205 passed`
- 11-regression selector bundle currently resolves to `16 passed` (`324 deselected`) with zero failures
- Current `tests/unit` baseline in this environment: `3077 passed in 373.14s`
- Full baseline pytest run: `3141 passed in 379.89s`
- CLI checks: `config-check`, `phase2-smoke`, `collect-only --help`, `quality-analysis --help`, `recommendations-only --help` all pass
- `quality-analysis --help` subprocess exit code: `0`

## Score State Baseline

- Current cycle baseline target context:
  - `composite=45.46`
  - `CM stored=0.95`
  - `CM live=0.775`
  - `final=42.21`
- Historical best row details from DB:
  - `kw=96 final=44.22 composite~46.53 CM~0.950`
  - `demand=1.02 contrib=0.15`
  - `competition=60.6 contrib=3.94`
  - `opportunity=16.37 contrib=3.27`
  - `feasibility=100.0 contrib=25.0`
  - `profitability=31.67 contrib=1.58`
  - `intent=54.29 contrib=2.71`
  - `weakness=49.4 contrib=9.88`

## Database Table Baseline

- `keywords: 129`
- `search_results: 103`
  - `ranked=73`
  - `gig_linked=89`
  - `trc=87`
- `gigs: 438`
- `sellers: 230`
- `gig_quality_analysis: 84`
- Stage 11 run splits:
  - `cycle038_agentb_live: 20 rows`
  - `cycle041_agentb_live_stage34: 42 rows`
  - `cycle044_agentb_stage45_backfill: 22 rows`

## GigQualityAnalysis OWS Distribution

- `OWS count=84 min=4.5 max=8.0 avg=4.8`
- Sample rows (truncated):
  - `...a911cd15-ee23-45a5-b6a1-e3719428e3a9 | ows=4.5 | run=cycle038_agentb_live`
  - `...f642f15a-80d0-46c9-af19-747353e7eeae | ows=4.5 | run=cycle038_agentb_live`
  - `...b12dc12d-19b8-4a69-b4a2-9857dbdd0eb9 | ows=4.5 | run=cycle038_agentb_live`
  - `...1c28ef25-22b9-47de-93be-dc36bd34920c | ows=4.5 | run=cycle038_agentb_live`
  - `...b0f2b196-a7e8-4ed6-bfbd-d789b8809789 | ows=8.0 | run=cycle038_agentb_live`

## Feasibility Anomaly Evidence

- Isolation run (`NewSellerFeasibilityCalculator`) for `kw=96` returns `47.79`
- Component visibility in isolation:
  - `level1_or_new_ratio: 0.0`
  - `lowest_ranked_review_barrier: 39.1308`
  - `price_diversity: missing`
  - `llm_gig_weakness: missing`
  - `llm_entry_gap: missing`
  - `profile_gap_boost: +30.0`
- Confidence deductions in feasibility path:
  - `missing_llm_gig_weakness: -0.10`
  - `missing_llm_entry_gap: -0.10`
- Data visibility snapshot for `kw=96` ranked search results:
  - `Ranked SR rows for kw96: 1`
  - `rank=1 gig_id=150 price=150.0 cards=20`

## Confidence Modifier Discrepancy Evidence

- Latest stored score row (`kw=96`) metadata:
  - `final=42.21`
  - `scored_at=2026-05-28 00:47:31.685772`
  - `profile=aggressive_new_seller`
  - `depth=all_11`
  - `stored confidence_modifier column=0.95`
  - `stored confidence_breakdown base=1.0, deduction=-0.05, remaining=0.95`
- Live confidence recomputation for same keyword:
  - `base_modifier=0.825`
  - `missing_reddit_signals=-0.05`
  - `remaining_modifier=0.775`
- Working discrepancy statement:
  - Stored run had full completeness/source ratios at score time.
  - Live recomputation now sees reduced completeness/source diversity ratios.

## Cycle 047 Agent Targets

- **Agent B:** restore feasibility toward `>=90` for `kw=96`; investigate gig linkage path and CM drift root cause; evaluate Stage 11 LLM pathway activation.
- **Agent E:** run Stage 11 across all 9 niches with new run ID (`cycle047_agent_e_stage11`), refresh stale Stage 3 search data, backfill Stage 4 gig links.
- **Agent C:** validate combined B+E outcomes, re-run scoring/recommendations, publish progression deltas and gate decision.
- **Agent F:** raise targeted module coverage (weakness/rubric/model compatibility areas) with tests only.
- **Agent D:** enforce merge gate checklist, Codex review-thread double query, config gate diff, and final release-readiness verdict.
