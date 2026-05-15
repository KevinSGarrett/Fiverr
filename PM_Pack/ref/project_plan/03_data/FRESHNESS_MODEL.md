# Freshness Model
# Fiverr Research System — Wave 3

**Document Status:** Complete
**Wave:** 3 — Data Schema and Source Design
**Purpose:** TTL by data type, staleness detection queries, re-queue logic, LLM cache invalidation, freshness scoring for the Confidence Modifier, and dashboard freshness display.

---

## Freshness Design Principles

1. Every collected record has `collected_at` (when it was fetched) and `ttl_hours` (how long it stays fresh)
2. A record is **stale** when `collected_at + ttl_hours < now()`
3. Stale records are re-queued automatically on the next run start — the user never manually refreshes data
4. LLM cache entries are invalidated when their source data records go stale
5. Different data types have different TTLs because they change at different rates
6. Priority of re-queue matches the priority of the niche (PRD stale data → CRITICAL queue)
7. The Confidence Modifier penalizes scores built on stale data via the `data_freshness_score` component

---

## TTL Reference Table

| Data Type | Table | Default TTL | Rationale | Config Key |
|---|---|---|---|---|
| Keyword expansion results | keywords | 168h (7 days) | Seeds don't change often; autocomplete shifts slowly | `freshness.ttl.keywords` |
| Fiverr search results | search_results | 72h (3 days) | Competitor rankings shift frequently | `freshness.ttl.search_results` |
| Gig detail — top 5 gigs | gigs | 72h (3 days) | Top gigs change fastest (reviews, pricing) | `freshness.ttl.gigs_top` |
| Gig detail — gigs 6–20 | gigs | 120h (5 days) | Mid-range gigs change less frequently | `freshness.ttl.gigs_mid` |
| Gig detail — gigs 21+ | gigs | 168h (7 days) | Lower-ranked gigs change slowly | `freshness.ttl.gigs_lower` |
| Seller profiles | sellers | 168h (7 days) | Seller levels, bio, gig count change slowly | `freshness.ttl.sellers` |
| Google Trends | external_signals (google_trends) | 24h (1 day) | Trends update daily | `freshness.ttl.google_trends` |
| Reddit signals | external_signals (reddit_demand) | 72h (3 days) | Post volume stable over days | `freshness.ttl.reddit` |
| YouTube counts | external_signals (youtube_count) | 72h (3 days) | YouTube counts stable | `freshness.ttl.youtube` |
| Gig quality scores | gig_quality_scores | Matches source gig TTL | LLM analysis is as fresh as the gig data it analyzed | Derived |
| Seller scores | seller_scores | Matches sellers TTL | Same reasoning | Derived |
| Keyword scores | keyword_scores | Recalculated whenever any input changes | Scores are always current | — |
| Opportunity rankings | opportunity_rankings | Same run as keyword_scores | Rankings follow scores | — |
| LLM cache entries | llm_cache | 72h (3 days) default | Should outlast the TTL of source data to avoid redundant calls | `llm.cache_ttl_hours` |
| Recommendations | recommendations | Recalculated when scores change significantly (> 5 points) | Recommendations follow opportunities | — |

---

## Staleness Detection Query

Run at the start of every full or collect-only run to identify which records need refreshing:

```sql
-- Keywords needing re-expansion
SELECT k.id, k.keyword_text, k.niche_id
FROM keywords k
WHERE k.is_active = true
  AND datetime(k.collected_at, '+' || k.ttl_hours || ' hours') < datetime('now')
ORDER BY k.niche_id, k.collected_at ASC;

-- Search results needing refresh
SELECT sr.keyword_id, sr.niche_id, k.keyword_text
FROM search_results sr
JOIN keywords k ON k.id = sr.keyword_id
WHERE datetime(sr.collected_at, '+' || sr.ttl_hours || ' hours') < datetime('now')
  AND k.is_active = true
ORDER BY sr.niche_id, sr.collected_at ASC;

-- Gig detail pages needing refresh
SELECT g.id, g.gig_url, g.niche_id, g.keyword_id
FROM gigs g
WHERE g.detail_collected = true
  AND datetime(g.collected_at, '+' || g.ttl_hours || ' hours') < datetime('now')
ORDER BY g.niche_id, g.collected_at ASC;

-- Sellers needing refresh
SELECT s.id, s.seller_username
FROM sellers s
WHERE datetime(s.collected_at, '+' || s.ttl_hours || ' hours') < datetime('now')
ORDER BY s.collected_at ASC;

-- External signals needing refresh
SELECT es.id, es.signal_type, es.niche_id, es.keyword_id
FROM external_signals es
WHERE datetime(es.collected_at, '+' || es.ttl_hours || ' hours') < datetime('now')
ORDER BY es.niche_id, es.signal_type, es.collected_at ASC;
```

**Python helper:**
```python
from datetime import datetime, timedelta

def is_stale(collected_at: datetime, ttl_hours: int) -> bool:
    return datetime.utcnow() > collected_at + timedelta(hours=ttl_hours)

def staleness_ratio(collected_at: datetime, ttl_hours: int) -> float:
    """Returns 0.0 (just collected) to 1.0+ (at or past TTL expiry)."""
    age_hours = (datetime.utcnow() - collected_at).total_seconds() / 3600
    return age_hours / ttl_hours
```

---

## Re-Queue Logic

When stale records are found at run start, the Orchestrator creates collection jobs for them:

```python
def enqueue_stale_records(stale_records: list, niche_configs: dict) -> list[Job]:
    jobs = []
    for record in stale_records:
        niche = niche_configs[record.niche_id]
        priority = assign_priority(niche.slot)  # PRD = CRITICAL, etc.

        job = Job(
            job_id=str(uuid4()),
            run_id=current_run_id,
            job_type=record_to_job_type(record),  # "FIVERR_SEARCH", "GIG_DETAIL", etc.
            stage=record_to_stage(record),
            niche_id=record.niche_id,
            priority=priority,
            status="QUEUED",
            payload=record_to_payload(record),   # {"keyword_id": 123} etc.
        )
        jobs.append(job)

    # Sort by priority tier, then by staleness ratio (most stale first within tier)
    return sorted(jobs, key=lambda j: (PRIORITY_ORDER[j.priority],
                                        -staleness_ratio(j.created_at, DEFAULT_TTL)))
```

**Priority assignment for stale re-queue:**
- PRD niche stale data → CRITICAL
- Tier 2 high-priority (Slots 5–7) stale data → HIGH
- Tier 2 standard (Slots 8–9) stale data → STANDARD
- Gated Tier 1 (Slots 2–3) stale data → LOW (they're keyword_only depth anyway)
- MCP (Slot 4) stale data → BACKGROUND

---

## LLM Cache Invalidation

The LLM cache uses source data hashing to detect when the underlying data has changed and the cached LLM analysis is no longer valid.

### Source Data Hash Calculation

```python
import hashlib
import json

def compute_source_data_hash(contributing_records: list[dict]) -> str:
    """
    Computes a hash of the source data records that will be used to build
    a prompt. When any record changes (new collection), the hash changes
    and the corresponding cache entry is invalidated.
    """
    # Normalize: sort keys, round floats, exclude timestamp fields
    normalized = []
    for record in contributing_records:
        clean = {k: v for k, v in sorted(record.items())
                 if k not in ("collected_at", "updated_at", "analyzed_at")}
        normalized.append(clean)

    canonical = json.dumps(normalized, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()
```

### Cache Invalidation Logic

```python
def get_cached_llm_response(cache_key: str, source_data_hash: str, db) -> str | None:
    """
    Returns cached response if valid, None if stale or absent.
    Two-condition invalidation:
    1. Cache entry has expired (expires_at < now())
    2. Source data has changed (source_data_hash mismatch)
    """
    entry = db.query(LLMCache).filter(
        LLMCache.cache_key == cache_key
    ).first()

    if entry is None:
        return None  # Cache miss

    if datetime.utcnow() > entry.expires_at:
        db.delete(entry)
        db.commit()
        return None  # Expired

    if entry.source_data_hash != source_data_hash:
        db.delete(entry)
        db.commit()
        return None  # Source data changed

    # Valid cache hit
    entry.cache_hits_count += 1
    db.commit()
    return entry.response_json
```

### What Triggers Invalidation

| LLM Task | Source Data Used | Invalidated When |
|---|---|---|
| Gig description quality | gigs.description_text, gigs.packages | Gig re-collected (new description or pricing) |
| Competitor synthesis | sellers + gigs + gig_quality_scores for a cluster | Any cluster seller re-collected |
| Keyword expansion | keywords seed list + niche context | Seed keywords changed in config.yaml |
| Score explanation | keyword_scores (all 11 scores) | Any score value changes by more than 0.5 |
| Recommendation titles | keyword_scores + competitor_analysis + gig_quality_scores | Score changes or new competitor data |
| Trend narrative | external_signals (google_trends) for cluster | Trends data re-collected |

---

## Freshness Score Calculation (for Confidence Modifier)

The `data_freshness_score` component of the Confidence Modifier measures how fresh the data underlying a keyword's scores is.

```python
def calculate_data_freshness_score(keyword_id: int, db) -> float:
    """
    Returns 0.0 (all data very stale) to 1.0 (all data fresh).
    """
    records = get_all_contributing_records(keyword_id, db)
    if not records:
        return 0.0

    freshness_scores = []
    for record in records:
        ratio = staleness_ratio(record.collected_at, record.ttl_hours)
        # 0.0 (just collected) to 1.0 (at TTL limit) to 1.0+ (past TTL)
        individual_freshness = max(0.0, 1.0 - ratio)
        freshness_scores.append(individual_freshness)

    return sum(freshness_scores) / len(freshness_scores)
```

**Freshness score deductions built into Confidence Modifier:**
| Data Age Relative to TTL | Freshness Score | Impact |
|---|---|---|
| < 25% of TTL (very fresh) | 1.0 | No deduction |
| 25–50% of TTL (fresh) | 0.85–1.0 | Minimal deduction |
| 50–75% of TTL (aging) | 0.65–0.85 | Moderate deduction |
| 75–100% of TTL (near-stale) | 0.40–0.65 | Significant deduction |
| > 100% of TTL (stale, past due) | < 0.40 | High deduction |
| > 200% of TTL (very stale) | 0.0 | Maximum deduction (−0.15 from confidence) |

---

## Freshness Dashboard Display

The Streamlit dashboard displays freshness information at three levels:

### Keyword-Level Freshness Indicator
On the Keywords page, each keyword card shows a freshness badge:
- 🟢 **FRESH** — all data within 50% of TTL
- 🟡 **AGING** — any data between 50–100% of TTL
- 🔴 **STALE** — any data past TTL (scheduled for refresh on next run)

### Niche-Level Freshness Summary
On the Opportunities page, each niche section shows:
- "Last collected: X hours ago"
- "Next refresh: Sunday 11:00 PM" (from APScheduler schedule)
- Count of stale keywords in this niche

### Alerts Panel
The dashboard header shows active freshness alerts:
```
⚠️ STALENESS ALERT: PRD niche — 8 keywords have stale search results (>72h old).
   Scheduled refresh: Sunday 11:00 PM. Run 'python run.py --mode collect-only' to refresh now.
```

### Data Age Field in Score Cards
Every keyword score card shows:
```
Score calculated: 2026-05-12 02:14 UTC
Data as of: 2026-05-11 23:00 UTC (newest) / 2026-05-09 14:22 UTC (oldest)
```

---

## Freshness Configuration in config.yaml

```yaml
freshness:
  ttl:
    keywords: 168              # hours — keyword expansion results
    search_results: 72         # hours — Fiverr search result pages
    gigs_top: 72               # hours — top 5 gigs per keyword
    gigs_mid: 120              # hours — gigs 6–20
    gigs_lower: 168            # hours — gigs 21+
    sellers: 168               # hours — seller profiles
    google_trends: 24          # hours — Google Trends signals
    reddit: 72                 # hours — Reddit demand signals
    youtube: 72                # hours — YouTube result counts

  stale_alert_threshold: 1.0   # ratio — alert when data_age / ttl_hours exceeds this
  # 1.0 = alert when data is past its TTL
  # 1.5 = alert when data is 50% past its TTL (more lenient)

  auto_requeue_on_run_start: true
  # If true, stale records are automatically added to the job queue at run start
  # If false, only records explicitly requested are refreshed
```
