# Analysis Output Field Contracts (Cycle 015 Agent C)

## Purpose

This document defines stable analysis field names that dashboard query/page consumers can rely on without guessing payload shapes. It is the explicit handoff contract for `SCRUM-225`, `SCRUM-214`, and `SCRUM-215` dependencies.

## Shared Stage Metadata (`AnalysisStageSummary.metadata`)

- `source_id`: stable source identifier for the analyzed payload.
- `result_count`: deterministic count of result rows/items produced by the stage.
- `warning_count`: warning count emitted by the stage.
- `missing_field_count`: count of missing upstream fields observed by the stage.
- `stage_status`: normalized placeholder status (`ready`, `sparse`, `empty`, `blocked`).
- `source_availability`: dictionary of source-signal booleans for downstream diagnostics.
- `explanation`: stage-level explanation string safe for dashboard display.
- `readiness_contract`: stage-specific contract object with deterministic keys per stage.
- `started_at`, `finished_at`, `duration_ms`: deterministic timing metadata for run history pages.

## Run Metadata (`AnalysisRunSummary.metadata`)

- `stage_order`: source-defined stage execution order.
- `successful_stages`, `failed_stages`, `skipped_stages`: explicit stage outcome buckets.
- `stage_contracts`: `{stage_name: readiness_contract}` map for page/query consumers.
- `stage_log_summary`: flattened stage rows (`stage`, `status`, `readiness_status`, `warning_count`, `error_code`, `duration_ms`).
- `dashboard_handoff_contract`: dashboard adapter metadata for opportunity cards, keyword table, and run-history surfaces.
- `scoring_readiness`: downstream scoring readiness and interface status map.

## Stage-Specific Contracts

### Keyword Clustering (`keyword_clustering`)

- Stage metadata additions:
  - `cluster_count`
  - `unclustered_count`
  - `cluster_metrics`
  - `top_cluster_labels`
- Result contract additions (`KeywordClusterResult`):
  - `clusters[]` (`cluster_id`, `label`, `keywords`, `size`, `cohesion_score`, `explanation`)
  - `unclustered_keywords[]`
  - `cluster_metrics` (`keyword_count`, `cluster_count`, `unclustered_count`)

### Gig Quality (`gig_quality`)

- Stage supports null-safe numeric coercion for:
  - `package_count`
  - `rating`
  - `review_count`
  - `image_count`
- Malformed numeric values emit `gig_numeric_field_invalid` warnings and do not fail stage execution.

### Intent Classification (`intent_classification`)

- Supports optional structured `metadata.llm_response` adapter:
  - expected keys: `category`, `confidence`, `explanation`
  - valid response emits `matched_rules=["llm_contract:parsed_response"]`
  - malformed response emits `intent_llm_response_malformed` and falls back to lexical rules
  - low confidence emits `intent_llm_low_confidence` and blocks downstream readiness

## Minimal Sample Payload (Dashboard Adapter)

```json
{
  "stage_contracts": {
    "keyword_clustering": {
      "status": "ready",
      "cluster_count": 3,
      "unclustered_count": 1,
      "source_availability": {
        "keywords": true,
        "cluster_outputs": true
      }
    },
    "intent_classification": {
      "status": "sparse",
      "source_availability": {
        "intent_keyword": true,
        "payload_keyword": false,
        "keywords_array": true
      }
    }
  },
  "dashboard_handoff_contract": {
    "opportunity_cards": {
      "saturation_status": "ready",
      "competitor_status": "ready",
      "intent_status": "partial"
    },
    "keyword_table": {
      "cluster_status": "ready"
    },
    "run_history": {
      "stage_count": 7,
      "failed_stage_count": 0,
      "warning_count": 2
    }
  }
}
```
