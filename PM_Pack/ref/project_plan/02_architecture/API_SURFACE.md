# API Surface
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Purpose:** FastAPI endpoint design for dashboard integration. v1 is Streamlit reading directly from the database. v2 exposes this API for React dashboard and any external tooling.

---

## API Design Principles

1. All endpoints are read-only for data access. Mutation endpoints (run triggers, config updates) are POST only.
2. All responses use Pydantic v2 schemas — same schemas used internally in the scoring engine.
3. v1: Streamlit calls dashboard_data.py query functions directly (no HTTP overhead). This API is designed for v2.
4. v2: FastAPI + Uvicorn at localhost:8000. React dashboard calls this API.
5. Authentication: v1 = none (local only). v2 = Bearer token (single static token in .env, sufficient for local use).
6. All list endpoints support pagination (limit/offset) and filtering.

---

## Base URL

```
v1 (local only, no auth): http://localhost:8000/api/v1
```

---

## Endpoint Catalog

---

### Niches

**GET /api/v1/niches**
Returns all niche configurations with current runtime state.

```
Response 200:
[
  {
    "niche_id": "prd_ai_saas",
    "slot": 1,
    "name": "PRD / AI SaaS MVP Roadmap",
    "tier": 1,
    "current_depth": "full",
    "gate_passed": true,
    "launch_status": "GO",
    "last_run_at": "2026-05-11T23:14:22Z",
    "run_count": 5,
    "avg_final_score": 74.3,
    "keyword_count": 127,
    "strong_go_count": 8,
    "conditional_go_count": 14,
    "auto_promotion_eligible": false
  },
  ...
]
```

**GET /api/v1/niches/{niche_id}**
Returns full niche detail including score history.

**POST /api/v1/niches/{niche_id}/set-depth**
Manually override the runtime depth for a niche.
```
Request body: { "depth": "standard" }
Response 200: { "niche_id": "...", "previous_depth": "keyword_only", "new_depth": "standard" }
```

**POST /api/v1/niches/{niche_id}/pass-gate**
Mark a niche's gate as passed.
```
Response 200: { "niche_id": "...", "gate_passed": true }
```

---

### Keywords

**GET /api/v1/keywords**
Returns keywords with scores, filterable by niche, tag, intent class, and cluster.

```
Query params:
  niche_id (optional): filter by niche
  tag (optional): STRONG_GO | CONDITIONAL_GO | MONITOR | CAUTION | PASS
  intent_class (optional): INFORMATIONAL | CONSIDERATION | HIGH_INTENT | TRANSACTIONAL
  cluster_id (optional): filter by cluster
  min_score (optional): float — minimum final_score
  limit (default 50, max 500)
  offset (default 0)
  sort_by (default "final_score"): final_score | demand_score | opportunity_score | collected_at

Response 200:
{
  "total": 843,
  "limit": 50,
  "offset": 0,
  "keywords": [
    {
      "keyword_id": 1234,
      "keyword_text": "AI SaaS PRD",
      "niche_id": "prd_ai_saas",
      "niche_name": "PRD / AI SaaS MVP Roadmap",
      "intent_class": "HIGH_INTENT",
      "cluster_id": 3,
      "cluster_label": "PRD — MVP Scoping",
      "final_score": 81.4,
      "confidence_modifier": 0.87,
      "tag": "STRONG GO",
      "demand_score": 76.2,
      "competition_score": 44.1,
      "opportunity_score": 79.3,
      "feasibility_score": 68.5,
      "profitability_score": 72.0,
      "explanation_text": "High demand: 2,400+ Fiverr results...",
      "red_flags": [],
      "scored_at": "2026-05-12T01:22:11Z",
      "data_as_of": "2026-05-11T23:14:22Z"
    }
  ]
}
```

**GET /api/v1/keywords/{keyword_id}**
Returns full keyword detail including all 11 scores, score components, explanation, and linked recommendation if available.

**GET /api/v1/keywords/{keyword_id}/score-history**
Returns score history across all runs for this keyword.
```
Response 200:
{
  "keyword_id": 1234,
  "keyword_text": "AI SaaS PRD",
  "history": [
    { "run_id": "...", "run_date": "2026-05-04", "final_score": 79.1, "tag": "CONDITIONAL GO" },
    { "run_id": "...", "run_date": "2026-05-11", "final_score": 81.4, "tag": "STRONG GO" }
  ]
}
```

---

### Opportunities

**GET /api/v1/opportunities**
Returns ranked opportunity list — the primary dashboard view.

```
Query params:
  niche_id (optional)
  tag (optional): default shows STRONG_GO + CONDITIONAL_GO
  min_confidence (optional): float 0.0–1.0
  limit (default 25, max 100)
  offset (default 0)

Response 200:
{
  "total": 22,
  "opportunities": [
    {
      "rank": 1,
      "keyword_id": 1234,
      "keyword_text": "AI SaaS PRD",
      "niche_id": "prd_ai_saas",
      "final_score": 81.4,
      "confidence_modifier": 0.87,
      "tag": "STRONG GO",
      "has_recommendation": true,
      "niche_viability_assessment": "This niche offers strong opportunity...",
      "red_flags": [],
      "missing_data_warnings": []
    }
  ]
}
```

---

### Recommendations

**GET /api/v1/recommendations**
Returns all generated recommendations, filterable by niche and tag.

```
Query params:
  niche_id (optional)
  tag (optional)
  limit (default 25)
  offset (default 0)
```

**GET /api/v1/recommendations/{keyword_id}**
Returns the full recommendation object for a specific keyword.

```
Response 200:
{
  "keyword_id": 1234,
  "keyword_text": "AI SaaS PRD",
  "niche_id": "prd_ai_saas",
  "tag": "STRONG GO",
  "final_score": 81.4,
  "gig_titles": [
    "I will write a developer-ready AI SaaS MVP PRD and technical roadmap",
    "I will create a complete AI product requirements document for your SaaS startup",
    ...
  ],
  "tag_sets": [
    ["PRD", "AI SaaS", "MVP roadmap", "product requirements", "technical spec"],
    ...
  ],
  "package_structure": {
    "basic": {
      "name": "Idea-to-Scope Audit",
      "price": 95,
      "deliverables": ["...", "..."],
      "delivery_days": 3,
      "revisions": 1
    },
    "standard": { ... },
    "premium": { ... }
  },
  "description_outline": { "sections": [...] },
  "faq_entries": [...],
  "differentiation_angle": "Top 10 gigs in this niche have generic descriptions...",
  "buyer_persona": { ... },
  "thumbnail_direction": "...",
  "upsell_structure": [...],
  "red_flags": [],
  "niche_viability_assessment": "...",
  "generated_at": "2026-05-12T01:45:00Z"
}
```

---

### Competitors

**GET /api/v1/competitors**
Returns competitor analysis per niche.

```
Query params:
  niche_id (required)

Response 200:
{
  "niche_id": "prd_ai_saas",
  "clusters": [
    {
      "cluster_id": 3,
      "cluster_label": "PRD — MVP Scoping",
      "synthesis_narrative": "The top 10 sellers in this cluster are dominated by...",
      "entry_feasibility_rating": 7.2,
      "dominant_sellers": [...],
      "positioning_gaps": [...]
    }
  ],
  "top_sellers": [
    {
      "seller_username": "...",
      "seller_level": "Level 2",
      "total_reviews": 847,
      "authority_score": 8.1,
      "authority_signals": [...],
      "weakness_list": [...],
      "gig_count": 3
    }
  ]
}
```

---

### Run History

**GET /api/v1/runs**
Returns run history list.

```
Query params:
  limit (default 10)
  offset (default 0)

Response 200:
{
  "total": 5,
  "runs": [
    {
      "run_id": "uuid",
      "mode": "full",
      "started_at": "2026-05-11T23:00:00Z",
      "completed_at": "2026-05-12T02:14:33Z",
      "duration_seconds": 11673,
      "keywords_expanded": 847,
      "gigs_collected": 412,
      "llm_cost_usd": 3.47,
      "llm_cache_hit_rate": 0.64,
      "errors_count": 2,
      "new_strong_go_count": 3,
      "summary_text": "Weekly run completed across all 9 niches...",
      "auto_promotion_changes": []
    }
  ]
}
```

**GET /api/v1/runs/{run_id}**
Returns full run detail including all errors, job stats, and auto-promotion changes.

**GET /api/v1/runs/revenue-gates**
Returns revenue gate tracker data.

```
Response 200:
{
  "target_net_usd": 30000,
  "target_gross_usd": 37500,
  "gates": [
    {
      "month": 4,
      "target_gross": 1720,
      "floor_gross": 1200,
      "actual_gross": 970,
      "status": "YELLOW",
      "on_track": false
    },
    ...
  ],
  "orders": [
    { "order_date": "2026-04-15", "niche": "PRD", "gross_usd": 95 },
    ...
  ]
}
```

**POST /api/v1/runs/revenue-gates/add-order**
Manually records a completed order for revenue gate tracking.
```
Request body: { "order_date": "2026-05-10", "niche_id": "prd_ai_saas", "gross_usd": 225 }
Response 201: { "order_id": "uuid", "cumulative_gross": 1195 }
```

---

### LLM Costs

**GET /api/v1/llm-costs**
Returns LLM usage and cost summary.

```
Query params:
  period: today | week | month | all (default: month)

Response 200:
{
  "period": "month",
  "total_cost_usd": 12.47,
  "total_calls": 4821,
  "cache_hits": 3089,
  "cache_hit_rate": 0.64,
  "by_model": {
    "gpt-4o": { "calls": 892, "cost_usd": 9.81 },
    "gpt-4o-mini": { "calls": 3929, "cost_usd": 2.66 },
    "text-embedding-3-small": { "calls": 0, "cost_usd": 0.00 }
  },
  "by_stage": {
    "stage_07_gig_quality": { "calls": 1240, "cost_usd": 4.22 },
    "stage_13_recommendations": { "calls": 330, "cost_usd": 3.61 },
    ...
  },
  "by_niche": {
    "prd_ai_saas": { "calls": 2100, "cost_usd": 5.83 },
    ...
  },
  "by_run": [
    { "run_id": "uuid", "run_date": "2026-05-11", "cost_usd": 3.47 }
  ]
}
```

---

### Pipeline Control

**POST /api/v1/pipeline/trigger**
Triggers a pipeline run (equivalent to python run.py --mode {mode}).
```
Request body: { "mode": "full" }
Response 202: { "run_id": "uuid", "status": "QUEUED", "message": "Run queued successfully" }
```

**GET /api/v1/pipeline/status**
Returns current run status (if a run is active).
```
Response 200:
{
  "run_active": true,
  "run_id": "uuid",
  "mode": "full",
  "current_stage": 4,
  "current_niche": "prd_ai_saas",
  "progress_pct": 28.4,
  "started_at": "2026-05-12T01:00:00Z",
  "estimated_completion": "2026-05-12T04:30:00Z",
  "jobs_complete": 847,
  "jobs_total": 3420,
  "errors_so_far": 1
}
```

**POST /api/v1/pipeline/stop**
Gracefully stops the active run (writes checkpoint, completes current job).

---

## Pydantic Response Models (Key Schemas)

```python
# src/schemas/api_responses.py

class NicheSummary(BaseModel):
    niche_id: str
    slot: int
    name: str
    tier: int
    current_depth: str
    gate_passed: bool
    launch_status: str
    last_run_at: datetime | None
    run_count: int
    avg_final_score: float | None
    keyword_count: int
    strong_go_count: int
    conditional_go_count: int

class KeywordSummary(BaseModel):
    keyword_id: int
    keyword_text: str
    niche_id: str
    intent_class: str
    cluster_label: str | None
    final_score: float
    confidence_modifier: float
    tag: str
    explanation_text: str | None
    red_flags: list[dict]
    scored_at: datetime

class RecommendationFull(BaseModel):
    keyword_id: int
    keyword_text: str
    niche_id: str
    tag: str
    final_score: float
    gig_titles: list[str]
    tag_sets: list[list[str]]
    package_structure: dict
    description_outline: dict
    faq_entries: list[dict]
    differentiation_angle: str
    buyer_persona: dict
    thumbnail_direction: str
    upsell_structure: list[dict]
    red_flags: list[dict]
    niche_viability_assessment: str
    generated_at: datetime

class RunSummary(BaseModel):
    run_id: str
    mode: str
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: float | None
    keywords_expanded: int
    gigs_collected: int
    llm_cost_usd: float
    llm_cache_hit_rate: float
    errors_count: int
    new_strong_go_count: int
    summary_text: str | None
    auto_promotion_changes: list[dict]
```
