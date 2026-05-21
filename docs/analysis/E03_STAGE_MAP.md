# E03 Stage Dependency Map

## Scope

This document captures the implemented dependency contract for Epic 03 analysis stages (Stages 9-12) and how outputs flow into Epic 04 scoring.

## Stage Execution Map

### Stage 9 — Keyword Clustering
- **Module:** `src/analysis/keyword_clusterer.py`
- **Entry point:** `run_clustering_for_niche(...)`
- **Runs after:** Stage 2 keyword expansion
- **Requires:**
  - `keywords.embedding_vector` (non-null vectors)
  - Active niche keywords
- **Writes:**
  - `cluster_assignments`
  - `cluster_labels`
  - `keywords.cluster_id` updates

### Stage 10 — Competitor Profiling
- **Module:** `src/analysis/competitor_profiler.py`
- **Entry point:** `run_competitor_profiling_for_niche(...)`
- **Runs after:** Stage 5 seller profile collection
- **Requires:**
  - `gigs` rows for niche/run
  - `sellers` rows for participating sellers
  - Optional `gig_quality_scores` supplements
- **Writes:**
  - `competitor_profiles`

### Stage 11 — GigQuality Analysis
- **Module:** `src/analysis/gig_quality_rubric.py`
- **Entry point:** `run_gig_quality_analysis_for_niche(...)`
- **Runs after:** Stage 4 gig detail collection (or any point after Stage 4/5 where top-gig rows are available)
- **Requires:**
  - `gig_quality_scores` rows for current `run_id`
  - `gigs` detail fields (`description_text`, `faq_text`, media metadata)
  - `search_results` top-rank scope (`rank <= 10`, same `run_id`)
- **Writes:**
  - `gig_quality_analyses`
- **Scoping rule:** Stage 11 joins are run-scoped to prevent stale legacy `gig_quality_scores` rows from leaking into current analysis.

### Stage 12 — Review Analysis
- **Module:** `src/analysis/review_analyzer.py`
- **Entry point:** `run_review_analysis_for_niche(...)`
- **Runs after:** Stage 4 gig detail collection
- **Requires:**
  - Gig review payload fields (`review_count`, `rating`, `review_snippets`)
  - `search_results` top-rank scope (`rank <= 10`, same `run_id`)
- **Writes:**
  - `review_analyses`

## E03 -> E04 Scoring Boundary

- **Current primary weakness input:** `GigQualityScore` (read by `src/scoring/weakness.py`).
- **Stage 11 compatibility path:** `GigQualityWeaknessScoreCalculator` includes fallback reads from `gig_quality_analyses` when Stage 7 `gig_quality_scores` rows are absent.
- **ClusterAssignment consumption:** `DemandScoreCalculator` now consumes `cluster_assignments` and `cluster_labels` as a config-gated boost signal in Cycle 032.
- **CompetitorProfile consumption:** Not consumed yet by `src/scoring/pipeline.py` or `src/scoring/orchestrator.py`.
- **GigQualityAnalysis consumption:** Partially consumed only through the Stage 11 fallback branch in `src/scoring/weakness.py`; not yet used as a first-class weighted input in scoring orchestration.
- **Cycle 032 integration gap:** Promote Stage 9/10/11 table reads (`cluster_assignments`, `competitor_profiles`, `gig_quality_analyses`) into explicit scoring context inputs so E04 scoring can directly leverage E03 outputs.

## E03->E04 Integration Status

| E03 Output | Score Using It | Status |
| --- | --- | --- |
| `ClusterAssignment` / `ClusterLabel` | Score 1 — Demand Score | Cycle 032 Agent A complete (`get_cluster_demand_boost`, config-gated boost, explanation wiring) |
| `CompetitorProfile` | Score 2 — Competition Score | Cycle 032 Agent B scope |
| `GigQualityAnalysis` | Score 4 — Feasibility, Score 8 — GQW | Cycle 032 Agent D scope |
| `ReviewAnalysis` | Not yet wired | Cycle 032 backlog |
| `SaturationModel` | Score 7 — Saturation Score | Cycle 032 Agent C scope |

### Cycle 032 Demand Integration Notes

- Demand cluster boost defaults:
  - `scoring.demand.use_cluster_boost = true`
  - `scoring.demand.cluster_boost = 5.0`
  - `scoring.demand.min_cluster_size = 3`
- Boost rule: apply configured boost when the keyword has a non-noise cluster assignment and cluster size meets the minimum threshold; clamp final demand score to `<= 100`.
- Explanation contract when applied: include cluster label, keyword count, and `ClusterLabel.opportunity_narrative` context so downstream score persistence retains rationale for the boost.

## Operational Notes

- `run.py` includes direct E03 stage commands:
  - `cluster-only`
  - `profile-only`
  - `quality-analysis`
  - `review-analysis`
- Collection dry-run orchestration (`run_collection_pipeline`) registers Stage 11 and Stage 12 alongside existing Stage 9/10 summary outputs.
