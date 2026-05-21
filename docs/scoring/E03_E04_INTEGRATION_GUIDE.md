# E03 to E04 Integration Guide

## Purpose

This guide is the anchor reference for wiring Epic 03 analysis outputs into Epic 04 scoring calculators.

## Current Mapping

- **Score 1 (Demand):** ClusterAssignment boost — DONE (Cycle 032 Agent A).
  - `src/scoring/demand.py` applies a config-gated boost when cluster membership is strong enough.
  - Demand explanation includes cluster label/size and `ClusterLabel.opportunity_narrative` when available.
  - Config keys: `scoring.demand.use_cluster_boost`, `scoring.demand.cluster_boost`, `scoring.demand.min_cluster_size`.
- **Score 2 (Competition):** CompetitorProfile benchmarks — DONE (Cycle 032 Agent B).
  - `src/scoring/competition.py` now consumes Stage 10 `CompetitorProfile` benchmarks (`mean_reviews`, `seller_level_distribution`, `median_price`) when available.
  - Config guard: `scoring.competition.use_competitor_profile` (default `true`).
  - Score 2 retains Stage 3/4 fallback behavior when no profile exists.
- **Score 3 (Opportunity):** Automatically updated via Score 2 output.
  - `src/scoring/opportunity.py` remains formula-stable and reads the updated competition payload without additional score-logic changes.
- **Score 4 (Feasibility):** CompetitorProfile gap flag boost — DONE (Cycle 032 Agent B).
  - `src/scoring/feasibility.py` now reads `CompetitorProfile.new_seller_gap.gap_flags` via `get_feasibility_gap_signal(...)`.
  - Config keys: `scoring.feasibility.gap_boost_per_flag`, `scoring.feasibility.max_gap_boost`.
- **Score 8 (GQW):** GigQualityAnalysis integration — Cycle 032 Agent D scope.
- **Score 7 (Saturation):** SaturationModel output wiring — after Cycle 032 Agent C deliverable is available.

## Implementation Principle

Use E03 tables as first-class scoring inputs (not passive side references), and preserve explanation text so every boost or deduction is traceable in persisted scoring artifacts.
