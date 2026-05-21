# E03 to E04 Integration Guide

## Purpose

This guide is the anchor reference for wiring Epic 03 analysis outputs into Epic 04 scoring calculators.

## Current Mapping

- **Score 1 (Demand):** ClusterAssignment boost — DONE (Cycle 032 Agent A).
  - `src/scoring/demand.py` applies a config-gated boost when cluster membership is strong enough.
  - Demand explanation includes cluster label/size and `ClusterLabel.opportunity_narrative` when available.
  - Config keys: `scoring.demand.use_cluster_boost`, `scoring.demand.cluster_boost`, `scoring.demand.min_cluster_size`.
- **Score 2 (Competition):** CompetitorProfile benchmarks — Cycle 032 Agent B scope.
  - Confirmed Score 2 spec input: "LLM competitor strength rating (cluster synthesis)" from `SCORING_DIRECTION.md`.
- **Score 4 + Score 8 (Feasibility + GQW):** GigQualityAnalysis integration — Cycle 032 Agent D scope.
- **Score 7 (Saturation):** SaturationModel output wiring — after Cycle 032 Agent C deliverable is available.

## Implementation Principle

Use E03 tables as first-class scoring inputs (not passive side references), and preserve explanation text so every boost or deduction is traceable in persisted scoring artifacts.
