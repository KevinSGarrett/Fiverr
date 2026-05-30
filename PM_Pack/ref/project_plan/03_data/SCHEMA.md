# Data Schema
# Fiverr Research System — Wave 3

**Document Status:** Complete
**Wave:** 3 — Data Schema and Source Design
**Purpose:** Full SQLAlchemy 2.0 ORM class definitions for all 21 database tables with primary keys, foreign keys, indexes, constraints, relationships, and default values.

---

## Schema Design Principles

1. Every table uses an integer surrogate primary key (`id`) — no composite PKs
2. Every collected record has `collected_at` (datetime) and `ttl_hours` (integer) for freshness tracking
3. Every LLM-generated field has a corresponding `_model_used` field tracking which model produced it
4. JSON fields store structured data (lists, dicts) as TEXT in SQLite, JSONB in PostgreSQL
5. All foreign keys have cascade delete rules defined
6. Indexes are defined on every field used in WHERE, ORDER BY, JOIN, or GROUP BY clauses
7. Unique constraints prevent duplicate collection of the same resource within its TTL window
8. Alembic manages all migrations — schema changes never applied manually

---

## Base Model

```python
# src/models/base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Naming conventions for Alembic migrations
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=naming_convention)
```

---

## Table 1 — niche_configs

Runtime niche state. Stores live depth and gate status that can change between runs without editing config.yaml.

```python
# src/models/niche_config.py
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class NicheConfig(Base):
    __tablename__ = "niche_configs"

    id             = Column(Integer, primary_key=True)
    niche_id       = Column(String(64), nullable=False, unique=True, index=True)
    # Unique: one row per niche. niche_id matches config.yaml niches[*].id
    slot           = Column(Integer, nullable=False, index=True)
    name           = Column(String(256), nullable=False)
    tier           = Column(Integer, nullable=False)         # 1 or 2
    current_depth  = Column(String(32), nullable=False,
                        default="keyword_only")
    # Values: full | standard | keyword_only | feasibility
    # Initial value from config.yaml; auto-promotion evaluator may update this
    gate_passed    = Column(Boolean, nullable=False, default=False)
    run_count      = Column(Integer, nullable=False, default=0)
    last_run_at    = Column(DateTime, nullable=True)
    avg_final_score = Column(Float, nullable=True)
    # Rolling average of Final Recommendation Score across last 3 runs
    auto_promotion_eligible = Column(Boolean, nullable=False, default=False)
    depth_reason   = Column(Text, nullable=True)
    # Human-readable reason for current depth (e.g., "Auto-promoted after run 3")
    updated_at     = Column(DateTime, nullable=False, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    keywords       = relationship("Keyword", back_populates="niche", lazy="dynamic")
    runs           = relationship("RunLog", back_populates="niches", secondary="run_niches",
                        lazy="dynamic")
```

---

## Table 2 — run_logs

One record per pipeline run. Written at run start, updated throughout, finalized at Stage 15.

```python
# src/models/run_log.py
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Boolean
from .base import Base

class RunLog(Base):
    __tablename__ = "run_logs"

    id                     = Column(Integer, primary_key=True)
    run_id                 = Column(String(36), nullable=False, unique=True, index=True)
    # UUID4 generated at run start
    mode                   = Column(String(32), nullable=False)
    # full | collect-only | analyze-only | score-only | report-only | keyword-only | resume
    scoring_profile        = Column(String(64), nullable=True)
    # Active scoring profile name used in this run
    started_at             = Column(DateTime, nullable=False, index=True)
    completed_at           = Column(DateTime, nullable=True)
    duration_seconds       = Column(Float, nullable=True)
    status                 = Column(String(32), nullable=False, default="RUNNING")
    # RUNNING | COMPLETE | FAILED | PARTIAL

    # Collection stats
    niches_processed       = Column(JSON, nullable=True)
    # {"prd_ai_saas": "full", "python_automation": "standard", ...}
    keywords_expanded      = Column(Integer, nullable=False, default=0)
    gigs_collected         = Column(Integer, nullable=False, default=0)
    sellers_collected      = Column(Integer, nullable=False, default=0)

    # LLM stats
    llm_calls_total        = Column(Integer, nullable=False, default=0)
    llm_cache_hits         = Column(Integer, nullable=False, default=0)
    llm_cost_usd           = Column(Float, nullable=False, default=0.0)

    # Results
    new_strong_go_count    = Column(Integer, nullable=False, default=0)
    new_strong_go_keywords = Column(JSON, nullable=True)
    # [{"keyword_id": 123, "keyword_text": "...", "niche_id": "..."}]

    # Auto-promotion
    auto_promotion_ran     = Column(Boolean, nullable=False, default=False)
    auto_promotion_changes = Column(JSON, nullable=True)
    # [{"niche_id": "...", "old_depth": "standard", "new_depth": "full", "reason": "..."}]

    # Errors and summary
    errors                 = Column(JSON, nullable=True)
    # [{"job_id": "...", "job_type": "...", "niche_id": "...", "error": "...", "impact": "HIGH"}]
    errors_count           = Column(Integer, nullable=False, default=0)
    dead_letter_count      = Column(Integer, nullable=False, default=0)
    summary_text           = Column(Text, nullable=True)
    # LLM-generated natural language run summary (Stage 15)
    next_recommended_action = Column(Text, nullable=True)

    __table_args__ = (
        Index("ix_run_logs_started_at", "started_at"),
        Index("ix_run_logs_status", "status"),
    )
```

---

## Table 3 — jobs

Job queue table. One record per pipeline job.

```python
# src/models/job.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from .base import Base

class Job(Base):
    __tablename__ = "jobs"

    id             = Column(Integer, primary_key=True)
    job_id         = Column(String(36), nullable=False, unique=True, index=True)
    run_id         = Column(String(36), ForeignKey("run_logs.run_id", ondelete="CASCADE"),
                        nullable=False, index=True)
    job_type       = Column(String(64), nullable=False, index=True)
    # e.g., "GIG_DETAIL", "GIG_QUALITY_DESC", "RECOMMEND_TITLES"
    stage          = Column(Integer, nullable=False)
    niche_id       = Column(String(64), ForeignKey("niche_configs.niche_id"),
                        nullable=False, index=True)
    priority       = Column(String(16), nullable=False, index=True)
    # CRITICAL | HIGH | STANDARD | LOW | BACKGROUND
    status         = Column(String(16), nullable=False, default="QUEUED", index=True)
    # QUEUED | RUNNING | COMPLETE | FAILED | DEAD_LETTER | SKIPPED
    payload        = Column(JSON, nullable=True)
    # Job-specific input: {"keyword_id": 123, "gig_url": "..."}
    result_ref     = Column(String(128), nullable=True)
    # Pointer to output: "gigs:456" or "gig_quality_scores:789"
    retry_count    = Column(Integer, nullable=False, default=0)
    max_retries    = Column(Integer, nullable=False, default=3)
    error_log      = Column(JSON, nullable=True)
    # List of error messages from each failed attempt
    checkpoint_ref = Column(String(256), nullable=True)
    created_at     = Column(DateTime, nullable=False, index=True)
    started_at     = Column(DateTime, nullable=True)
    completed_at   = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_jobs_run_status", "run_id", "status"),
        Index("ix_jobs_priority_stage", "priority", "stage"),
    )
```

---

## Table 4 — keywords

One record per unique keyword per niche. The central table — most other tables FK back to this.

```python
# src/models/keyword.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Keyword(Base):
    __tablename__ = "keywords"

    id                   = Column(Integer, primary_key=True)
    keyword_text         = Column(String(512), nullable=False)
    niche_id             = Column(String(64), ForeignKey("niche_configs.niche_id"),
                              nullable=False, index=True)
    source               = Column(String(32), nullable=False)
    # fiverr_autocomplete | google_suggest | llm_expansion | seed
    autocomplete_position = Column(Integer, nullable=True)
    # Position in Fiverr autocomplete (1–10), null if not from autocomplete
    intent_class         = Column(String(32), nullable=True, index=True)
    # INFORMATIONAL | CONSIDERATION | HIGH_INTENT | TRANSACTIONAL
    intent_model_used    = Column(String(64), nullable=True)
    cluster_id           = Column(Integer, ForeignKey("keyword_clusters.cluster_id"),
                              nullable=True, index=True)
    embedding_vector     = Column(JSON, nullable=True)
    # 1536-dimension float array stored as JSON. In PostgreSQL v2, use pgvector column type.
    embedding_model_used = Column(String(64), nullable=True)
    is_active            = Column(Boolean, nullable=False, default=True)
    # Set to False for keywords removed from config seeds that still have historical data
    collected_at         = Column(DateTime, nullable=False, index=True)
    ttl_hours            = Column(Integer, nullable=False, default=168)
    # 168 = 7 days for keyword expansion results

    # Relationships
    niche          = relationship("NicheConfig", back_populates="keywords")
    search_results = relationship("SearchResult", back_populates="keyword",
                        cascade="all, delete-orphan")
    gigs           = relationship("Gig", back_populates="keyword",
                        cascade="all, delete-orphan")
    scores         = relationship("KeywordScore", back_populates="keyword",
                        cascade="all, delete-orphan", uselist=False)
    ranking        = relationship("OpportunityRanking", back_populates="keyword",
                        cascade="all, delete-orphan", uselist=False)
    recommendation = relationship("Recommendation", back_populates="keyword",
                        cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        Index("ix_keywords_niche_text", "niche_id", "keyword_text"),
        # Unique per niche — prevents duplicate expansion results
    )
```

---

## Table 5 — search_results

One record per keyword per search collection run. Stores what Fiverr returns in search result cards.

```python
# src/models/search_result.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class SearchResult(Base):
    __tablename__ = "search_results"

    id                   = Column(Integer, primary_key=True)
    keyword_id           = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                              nullable=False, index=True)
    niche_id             = Column(String(64), nullable=False, index=True)
    run_id               = Column(String(36), ForeignKey("run_logs.run_id"),
                              nullable=False, index=True)

    # Result-level data
    total_result_count   = Column(Integer, nullable=True)
    pagination_depth     = Column(Integer, nullable=True)
    # Number of result pages available
    collected_at         = Column(DateTime, nullable=False, index=True)
    ttl_hours            = Column(Integer, nullable=False, default=72)
    # 72 = 3 days for search results

    # Gig cards collected in this search — stored as JSON array
    gig_cards            = Column(JSON, nullable=True)
    # [{
    #   "gig_url": "...", "gig_title": "...", "seller_username": "...",
    #   "seller_level": "Level 2", "rating_visible": 4.9,
    #   "review_count_visible": 847, "review_count_abbreviated": false,
    #   "starting_price": 95.0, "delivery_time": "3 days",
    #   "tags_visible": ["PRD", "AI SaaS"], "sponsored_flag": false,
    #   "position": 1
    # }]
    # Note: review_count_visible may be null if Fiverr only shows abbreviated count.
    # review_count_abbreviated=true when Fiverr shows "1k+" instead of exact count.
    # OQ-002 resolution: schema handles both cases. Exact count collected in gigs table.

    keyword             = relationship("Keyword", back_populates="search_results")

    __table_args__ = (
        Index("ix_search_results_keyword_run", "keyword_id", "run_id"),
    )
```

---

## Table 6 — gigs

One record per unique gig URL. Updated when re-collected after TTL expiry.

```python
# src/models/gig.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base

class Gig(Base):
    __tablename__ = "gigs"

    id                     = Column(Integer, primary_key=True)
    gig_url                = Column(String(512), nullable=False, unique=True, index=True)
    keyword_id             = Column(Integer, ForeignKey("keywords.id", ondelete="SET NULL"),
                                nullable=True, index=True)
    # SET NULL: if keyword is deleted, gig record remains for historical analysis
    niche_id               = Column(String(64), nullable=False, index=True)
    seller_username        = Column(String(256), nullable=False, index=True)

    # Basic fields (also available in search result cards)
    gig_title              = Column(String(512), nullable=False)
    starting_price         = Column(Float, nullable=True)
    delivery_time          = Column(String(64), nullable=True)
    rating_exact           = Column(Float, nullable=True)
    review_count_exact     = Column(Integer, nullable=True, index=True)
    # Exact count from gig detail page — more reliable than search card value

    # Detail page fields (only available after Stage 4 collection)
    description_text       = Column(Text, nullable=True)
    packages               = Column(JSON, nullable=True)
    # [{"name": "Basic", "price": 95.0, "deliverables": [...], "delivery_days": 3, "revisions": 1}]
    gig_extras             = Column(JSON, nullable=True)
    # [{"name": "Extra revision", "price": 25.0}]
    tags                   = Column(JSON, nullable=True)
    # ["PRD", "AI SaaS", "MVP", "technical roadmap", "product requirements"]
    faq_text               = Column(Text, nullable=True)
    # Full FAQ text as collected
    faq_entries            = Column(JSON, nullable=True)
    # Parsed: [{"question": "...", "answer": "..."}]

    # Media signals
    video_present          = Column(Boolean, nullable=True)
    portfolio_count        = Column(Integer, nullable=True)
    thumbnail_url          = Column(String(512), nullable=True)

    # Review snippets (visible on detail page)
    review_snippets        = Column(JSON, nullable=True)
    # [{"reviewer": "...", "rating": 5, "snippet": "...", "date": "2026-03-15"}]

    # Orders in queue (OQ-003 resolution)
    orders_in_queue        = Column(Integer, nullable=True)
    # Null when field is not shown by Fiverr (common — field appears/disappears per UI tests)
    # When null, review_velocity (in gig_quality_scores) is used as the proxy metric

    # Freshness
    detail_collected       = Column(Boolean, nullable=False, default=False)
    # False = only search card data collected; True = full detail page collected
    collected_at           = Column(DateTime, nullable=False, index=True)
    ttl_hours              = Column(Integer, nullable=False, default=120)
    # 120 = 5 days for gig detail pages; lower for top-ranked gigs (configurable)

    # Relationships
    keyword        = relationship("Keyword", back_populates="gigs")
    quality_score  = relationship("GigQualityScore", back_populates="gig",
                        cascade="all, delete-orphan", uselist=False)

    __table_args__ = (
        Index("ix_gigs_niche_seller", "niche_id", "seller_username"),
        Index("ix_gigs_review_count", "review_count_exact"),
    )
```

---

## Table 7 — sellers

One record per unique seller username. Updated when re-collected after TTL expiry.

```python
# src/models/seller.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class Seller(Base):
    __tablename__ = "sellers"

    id                 = Column(Integer, primary_key=True)
    seller_username    = Column(String(256), nullable=False, unique=True, index=True)
    seller_level       = Column(String(32), nullable=True, index=True)
    # "No Level" | "Level 1" | "Level 2" | "Top Rated" | "Pro"
    member_since       = Column(String(32), nullable=True)
    # Stored as string ("Jan 2022") — Fiverr doesn't expose exact date
    response_time      = Column(String(64), nullable=True)
    # "1 hour" | "2 hours" | "1 day" etc.
    response_rate      = Column(Integer, nullable=True)
    # Percentage integer (e.g., 97 = 97%)
    languages          = Column(JSON, nullable=True)
    # [{"language": "English", "level": "Native"}]
    bio_text           = Column(Text, nullable=True)
    total_reviews      = Column(Integer, nullable=True, index=True)
    total_gigs         = Column(Integer, nullable=True)
    active_gig_titles  = Column(JSON, nullable=True)
    # List of all gig titles visible on seller's profile page
    portfolio_count    = Column(Integer, nullable=True)
    badges             = Column(JSON, nullable=True)
    # [{"badge": "Top Rated", "earned": "2025-06"}]
    profile_url        = Column(String(512), nullable=True)

    # Authority analysis (from Stage 8 LLM)
    authority_score    = Column(Float, nullable=True)
    # 0–10 score from gpt-4o-mini bio analysis
    authority_signals  = Column(JSON, nullable=True)
    authority_model    = Column(String(64), nullable=True)

    # Freshness
    collected_at       = Column(DateTime, nullable=False, index=True)
    ttl_hours          = Column(Integer, nullable=False, default=168)

    # Relationship
    score              = relationship("SellerScore", back_populates="seller",
                            cascade="all, delete-orphan", uselist=False)
```

---

## Table 8 — external_signals

One record per signal type per keyword/niche per collection. Covers Google Trends, Reddit, YouTube.

```python
# src/models/external_signal.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text
from .base import Base

class ExternalSignal(Base):
    __tablename__ = "external_signals"

    id                       = Column(Integer, primary_key=True)
    keyword_id               = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                                   nullable=True, index=True)
    niche_id                 = Column(String(64), nullable=False, index=True)
    run_id                   = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)
    signal_type              = Column(String(32), nullable=False, index=True)
    # google_trends | reddit_demand | youtube_count

    # Google Trends fields (signal_type = google_trends)
    trends_12mo_score        = Column(Float, nullable=True)
    # 0–100 interest score over past 12 months
    trends_3mo_score         = Column(Float, nullable=True)
    trends_slope             = Column(String(16), nullable=True)
    # RISING | FLAT | DECLINING | STRONGLY_RISING | STRONGLY_DECLINING
    trends_related_queries   = Column(JSON, nullable=True)
    trends_related_topics    = Column(JSON, nullable=True)

    # Reddit fields (signal_type = reddit_demand)
    reddit_post_count_90d    = Column(Integer, nullable=True)
    reddit_top_snippets      = Column(JSON, nullable=True)
    # [{"subreddit": "...", "title": "...", "snippet": "...", "upvotes": 847}]
    reddit_demand_intent_score = Column(Float, nullable=True)
    # 0–10 LLM-scored buyer intent from Reddit post analysis
    reddit_intent_phrases    = Column(JSON, nullable=True)
    # ["I need someone to build...", "looking for a PRD writer..."]
    reddit_llm_model         = Column(String(64), nullable=True)

    # YouTube fields (signal_type = youtube_count)
    youtube_result_count     = Column(Integer, nullable=True)

    # General
    signal_details           = Column(JSON, nullable=True)
    # Catch-all for any additional signal data
    collected_at             = Column(DateTime, nullable=False, index=True)
    ttl_hours                = Column(Integer, nullable=False, default=24)
    # 24 hours for Google Trends; 72 hours for Reddit

    __table_args__ = (
        Index("ix_external_signals_niche_type", "niche_id", "signal_type"),
        Index("ix_external_signals_keyword_type", "keyword_id", "signal_type"),
    )
```

---

## Table 9 — gig_quality_scores

LLM-generated quality analysis for each gig. One record per gig.

```python
# src/models/gig_quality_score.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from .base import Base

class GigQualityScore(Base):
    __tablename__ = "gig_quality_scores"

    id                          = Column(Integer, primary_key=True)
    gig_id                      = Column(Integer, ForeignKey("gigs.id", ondelete="CASCADE"),
                                      nullable=False, unique=True, index=True)
    keyword_id                  = Column(Integer, ForeignKey("keywords.id"), nullable=True, index=True)
    niche_id                    = Column(String(64), nullable=False, index=True)
    run_id                      = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)

    # Title analysis (gpt-4o-mini)
    title_quality_score         = Column(Float, nullable=True)   # 0–100
    title_keyword_targeting     = Column(Float, nullable=True)   # 0–10
    title_clarity               = Column(Float, nullable=True)   # 0–10
    title_specificity           = Column(Float, nullable=True)   # 0–10
    title_model_used            = Column(String(64), nullable=True)

    # Description analysis (gpt-4o)
    description_quality_score   = Column(Float, nullable=True)   # 0–100
    desc_clarity                = Column(Float, nullable=True)   # 0–10
    desc_benefit_language       = Column(Float, nullable=True)   # 0–10
    desc_proof_elements         = Column(Float, nullable=True)   # 0–10
    desc_cta_strength           = Column(Float, nullable=True)   # 0–10
    desc_package_differentiation = Column(Float, nullable=True)  # 0–10
    desc_niche_specificity      = Column(Float, nullable=True)   # 0–10
    description_model_used      = Column(String(64), nullable=True)

    # Weakness detection (gpt-4o)
    weakness_list               = Column(JSON, nullable=True)
    # [{"weakness": "vague promises", "severity": "HIGH", "description": "..."}]
    weakness_count              = Column(Integer, nullable=True)
    weakness_model_used         = Column(String(64), nullable=True)

    # Thumbnail assessment (gpt-4o-mini)
    thumbnail_class             = Column(String(32), nullable=True)
    # PROFESSIONAL_PHOTO | GRAPHIC_DESIGN | TEXT_HEAVY | STOCK_IMAGE | LOW_QUALITY
    thumbnail_model_used        = Column(String(64), nullable=True)

    # FAQ analysis (gpt-4o-mini)
    faq_quality_score           = Column(Float, nullable=True)   # 0–100
    faq_completeness            = Column(Float, nullable=True)   # 0–10
    faq_buyer_relevance         = Column(Float, nullable=True)   # 0–10
    faq_model_used              = Column(String(64), nullable=True)

    # Collection-based signals (no LLM needed)
    video_absent                = Column(Boolean, nullable=True)
    portfolio_absent            = Column(Boolean, nullable=True)

    # Review velocity proxy (OQ-003 resolution: used when orders_in_queue is null)
    review_velocity_30d         = Column(Float, nullable=True)
    # Estimated reviews received in last 30 days (calculated from review date distribution)

    # Overall weakness score (composite — used in Gig Quality Weakness Score)
    overall_weakness_score      = Column(Float, nullable=True)   # 0–10 (higher = weaker)

    analyzed_at                 = Column(DateTime, nullable=False, index=True)
    analysis_complete           = Column(Boolean, nullable=False, default=False)
    # False if any LLM task failed for this gig

    gig = relationship("Gig", back_populates="quality_score")
```

---

## Table 10 — seller_scores

LLM-generated seller authority analysis. One record per seller.

```python
# src/models/seller_score.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class SellerScore(Base):
    __tablename__ = "seller_scores"

    id                  = Column(Integer, primary_key=True)
    seller_id           = Column(Integer, ForeignKey("sellers.id", ondelete="CASCADE"),
                              nullable=False, unique=True, index=True)
    niche_id            = Column(String(64), nullable=False, index=True)
    run_id              = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)
    authority_score     = Column(Float, nullable=True)    # 0–10
    authority_signals   = Column(JSON, nullable=True)
    # [{"signal": "10+ years experience", "weight": "HIGH"}]
    weakness_list       = Column(JSON, nullable=True)
    # [{"weakness": "generic bio", "severity": "MEDIUM"}]
    model_used          = Column(String(64), nullable=True)
    analyzed_at         = Column(DateTime, nullable=False, index=True)

    seller = relationship("Seller", back_populates="score")
```

---

## Table 11 — keyword_clusters

Maps keywords to clusters. One record per keyword (updated when clustering re-runs).

```python
# src/models/keyword_cluster.py
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from .base import Base

class KeywordCluster(Base):
    __tablename__ = "keyword_clusters"

    id           = Column(Integer, primary_key=True)
    cluster_id   = Column(Integer, nullable=False, index=True)
    # Cluster number within the niche (e.g., 0, 1, 2, 3 ...)
    niche_id     = Column(String(64), nullable=False, index=True)
    keyword_id   = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                       nullable=False, unique=True, index=True)
    # unique=True: each keyword belongs to exactly one cluster
    cluster_label = Column(String(256), nullable=True)
    # Human-readable label set by gpt-4o-mini (e.g., "PRD — MVP Scoping")
    distance_to_centroid = Column(Float, nullable=True)
    # sklearn cluster distance — lower = more representative of cluster
    assigned_at  = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_keyword_clusters_niche_cluster", "niche_id", "cluster_id"),
    )
```

---

## Table 12 — cluster_analysis

LLM-generated cluster-level analysis. One record per cluster per niche.

```python
# src/models/cluster_analysis.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text
from .base import Base

class ClusterAnalysis(Base):
    __tablename__ = "cluster_analysis"

    id                       = Column(Integer, primary_key=True)
    cluster_id               = Column(Integer, nullable=False, index=True)
    niche_id                 = Column(String(64), nullable=False, index=True)
    run_id                   = Column(String(36), nullable=False, index=True)
    cluster_label            = Column(String(256), nullable=True)
    keyword_count            = Column(Integer, nullable=False, default=0)
    representative_keywords  = Column(JSON, nullable=True)
    # Top 5 keywords closest to centroid

    # LLM outputs
    opportunity_narrative    = Column(Text, nullable=True)
    # gpt-4o paragraph: what this cluster represents and why it is/isn't a strong opportunity
    trend_narrative          = Column(Text, nullable=True)
    # gpt-4o-mini paragraph: trend interpretation for this cluster
    competitor_landscape_summary = Column(Text, nullable=True)
    # gpt-4o paragraph: competitor landscape summary for dashboard Competitors page
    entry_feasibility_rating = Column(Float, nullable=True)   # 0–10
    dominant_sellers         = Column(JSON, nullable=True)
    positioning_gaps         = Column(JSON, nullable=True)
    synthesis_model_used     = Column(String(64), nullable=True)
    label_model_used         = Column(String(64), nullable=True)
    analyzed_at              = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_cluster_analysis_niche_cluster", "niche_id", "cluster_id"),
    )
```

---

## Table 13 — keyword_scores

All 11 scores for each keyword. One record per keyword (updated each run).

```python
# src/models/keyword_score.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class KeywordScore(Base):
    __tablename__ = "keyword_scores"

    id                      = Column(Integer, primary_key=True)
    keyword_id              = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                                 nullable=False, unique=True, index=True)
    niche_id                = Column(String(64), nullable=False, index=True)
    run_id                  = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)
    scoring_profile         = Column(String(64), nullable=False)
    niche_tier              = Column(String(16), nullable=False)
    # tier1_full | tier1_gated | tier2_standard
    score_depth             = Column(String(16), nullable=False)
    # all_11 | scores_1_to_5 | scores_1_to_3

    # Individual scores (null when score_depth excludes them)
    demand_score            = Column(Float, nullable=True)
    competition_score       = Column(Float, nullable=True)
    opportunity_score       = Column(Float, nullable=True)
    feasibility_score       = Column(Float, nullable=True)
    profitability_score     = Column(Float, nullable=True)
    intent_score            = Column(Float, nullable=True)
    saturation_score        = Column(Float, nullable=True)
    weakness_score          = Column(Float, nullable=True)
    trend_score             = Column(Float, nullable=True)

    # Final scores
    weighted_composite      = Column(Float, nullable=True)
    confidence_modifier     = Column(Float, nullable=True)   # 0.0–1.0
    final_score             = Column(Float, nullable=True, index=True)
    # final_score = weighted_composite × confidence_modifier

    # Explainability
    score_components        = Column(JSON, nullable=True)
    # {"demand": {"value": 74.2, "components": {"fiverr_count": 0.38, ...}}, ...}
    confidence_breakdown    = Column(JSON, nullable=True)
    # {"data_completeness": 0.92, "data_freshness": 0.88, "source_diversity": 0.75, ...}
    confidence_reason       = Column(Text, nullable=True)
    explanation_text        = Column(Text, nullable=True)
    # gpt-4o generated 2–4 sentence explanation
    explanation_model_used  = Column(String(64), nullable=True)
    red_flags               = Column(JSON, nullable=True)
    # [{"flag_type": "declining_trend", "description": "...", "severity": "MEDIUM"}]
    missing_data_warnings   = Column(JSON, nullable=True)
    source_evidence         = Column(JSON, nullable=True)
    saturation_narrative    = Column(Text, nullable=True)

    # Freshness
    scored_at               = Column(DateTime, nullable=False, index=True)
    data_as_of              = Column(DateTime, nullable=True)
    # Timestamp of the oldest contributing data record

    keyword = relationship("Keyword", back_populates="scores")

    __table_args__ = (
        Index("ix_keyword_scores_final_score", "final_score"),
        Index("ix_keyword_scores_niche_score", "niche_id", "final_score"),
    )
```

---

## Table 14 — opportunity_rankings

GO/PASS tags and rank order per keyword per run.

```python
# src/models/opportunity_ranking.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base

class OpportunityRanking(Base):
    __tablename__ = "opportunity_rankings"

    id           = Column(Integer, primary_key=True)
    keyword_id   = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                       nullable=False, index=True)
    niche_id     = Column(String(64), nullable=False, index=True)
    run_id       = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False, index=True)
    final_score  = Column(Float, nullable=False, index=True)
    tag          = Column(String(32), nullable=False, index=True)
    # STRONG GO | CONDITIONAL GO | MONITOR | CAUTION | PASS
    rank         = Column(Integer, nullable=False)
    # Rank within niche (1 = highest scoring)
    rank_global  = Column(Integer, nullable=True)
    # Rank across all niches in this run
    ranked_at    = Column(DateTime, nullable=False, index=True)

    keyword = relationship("Keyword", back_populates="ranking")

    __table_args__ = (
        Index("ix_rankings_run_niche_tag", "run_id", "niche_id", "tag"),
        Index("ix_rankings_run_global", "run_id", "rank_global"),
    )
```

---

## Table 15 — recommendations

Full LLM-generated gig recommendation package. One record per keyword (GO-tier only).

```python
# src/models/recommendation.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base

class Recommendation(Base):
    __tablename__ = "recommendations"

    id                       = Column(Integer, primary_key=True)
    keyword_id               = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"),
                                   nullable=False, unique=True, index=True)
    niche_id                 = Column(String(64), nullable=False, index=True)
    run_id                   = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)
    tag                      = Column(String(32), nullable=False, index=True)
    final_score              = Column(Float, nullable=False)

    # LLM-generated components
    gig_titles               = Column(JSON, nullable=True)
    # ["title 1", "title 2", "title 3", "title 4", "title 5"]
    tag_sets                 = Column(JSON, nullable=True)
    # [["tag1","tag2","tag3","tag4","tag5"], ...]  — 5 sets
    package_structure        = Column(JSON, nullable=True)
    # {"basic": {"name":"..","price":95,"deliverables":[..],"delivery_days":3,"revisions":1}, ...}
    description_outline      = Column(JSON, nullable=True)
    # {"sections": [{"heading":"..","copy_direction":"..","proof_elements":[..]}]}
    faq_entries              = Column(JSON, nullable=True)
    # [{"question":"..","answer":".."}]
    differentiation_angle    = Column(Text, nullable=True)
    buyer_persona            = Column(JSON, nullable=True)
    # {"name":"..","role":"..","pain_points":[..],"budget":"..","decision_trigger":".."}
    thumbnail_direction      = Column(Text, nullable=True)
    upsell_structure         = Column(JSON, nullable=True)
    # [{"extra_name":"..","price":25,"description":".."}]
    red_flags                = Column(JSON, nullable=True)
    niche_viability_assessment = Column(Text, nullable=True)

    # LLM metadata
    titles_model             = Column(String(64), nullable=True)
    packages_model           = Column(String(64), nullable=True)
    description_model        = Column(String(64), nullable=True)
    differentiation_model    = Column(String(64), nullable=True)
    viability_model          = Column(String(64), nullable=True)
    llm_cost_usd             = Column(Float, nullable=True)
    # Total LLM cost for all 11 recommendation tasks for this keyword
    generation_complete      = Column(Boolean, nullable=False, default=False)

    generated_at             = Column(DateTime, nullable=False, index=True)

    keyword = relationship("Keyword", back_populates="recommendation")
```

---

## Table 16 — llm_cache

LLM response cache. Cache key = SHA-256(model + temperature + prompt_text).

```python
# src/models/llm_cache.py
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from .base import Base

class LLMCache(Base):
    __tablename__ = "llm_cache"

    id             = Column(Integer, primary_key=True)
    cache_key      = Column(String(64), nullable=False, unique=True, index=True)
    # SHA-256 hex digest of (model + str(temperature) + prompt_text)
    model          = Column(String(64), nullable=False, index=True)
    temperature    = Column(Float, nullable=False)
    prompt_hash    = Column(String(64), nullable=False)
    # SHA-256 of prompt_text alone — useful for finding related prompts
    response_json  = Column(Text, nullable=False)
    # Full API response as JSON string
    prompt_tokens  = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    created_at     = Column(DateTime, nullable=False, index=True)
    expires_at     = Column(DateTime, nullable=False, index=True)
    # expires_at = created_at + ttl_hours from config.llm.cache_ttl_hours
    cache_hits_count = Column(Integer, nullable=False, default=0)
    # Incremented each time this cache entry is served
    source_data_hash = Column(String(64), nullable=True)
    # Hash of the source data records that contributed to this prompt
    # Used for invalidation: when source data is refreshed, this hash changes

    __table_args__ = (
        Index("ix_llm_cache_expires", "expires_at"),
    )
```

---

## Table 17 — llm_usage_logs

One record per LLM API call (including cache hits logged separately).

```python
# src/models/llm_usage_log.py
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, ForeignKey
from .base import Base

class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id               = Column(Integer, primary_key=True)
    run_id           = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False, index=True)
    niche_id         = Column(String(64), nullable=True, index=True)
    stage            = Column(Integer, nullable=True, index=True)
    task             = Column(String(64), nullable=True)
    # e.g., "gig_description_quality", "recommendation_titles"
    model            = Column(String(64), nullable=False, index=True)
    prompt_tokens    = Column(Integer, nullable=False, default=0)
    completion_tokens = Column(Integer, nullable=False, default=0)
    total_tokens     = Column(Integer, nullable=False, default=0)
    cost_usd         = Column(Float, nullable=False, default=0.0)
    cache_hit        = Column(Boolean, nullable=False, default=False)
    success          = Column(Boolean, nullable=False, default=True)
    error_type       = Column(String(64), nullable=True)
    # e.g., "ValidationError", "RateLimitError", "Timeout"
    called_at        = Column(DateTime, nullable=False, index=True)
    duration_ms      = Column(Integer, nullable=True)

    __table_args__ = (
        Index("ix_llm_usage_run_model", "run_id", "model"),
        Index("ix_llm_usage_stage_task", "stage", "task"),
    )
```

---

## Table 18 — competitor_analysis

LLM-generated competitor cluster synthesis. One record per cluster per niche per run.

```python
# src/models/competitor_analysis.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Float, Text, ForeignKey
from .base import Base

class CompetitorAnalysis(Base):
    __tablename__ = "competitor_analysis"

    id                        = Column(Integer, primary_key=True)
    cluster_id                = Column(Integer, nullable=False, index=True)
    niche_id                  = Column(String(64), nullable=False, index=True)
    run_id                    = Column(String(36), ForeignKey("run_logs.run_id"), nullable=False)
    synthesis_narrative       = Column(Text, nullable=True)
    entry_feasibility_rating  = Column(Float, nullable=True)   # 0–10
    dominant_sellers          = Column(JSON, nullable=True)
    # [{"username":"..","level":"..","reviews":847,"why_winning":".."}]
    positioning_gaps          = Column(JSON, nullable=True)
    # [{"gap":"..","evidence":"..","exploitability":"HIGH"}]
    per_seller_weaknesses     = Column(JSON, nullable=True)
    # [{"username":"..","weaknesses":[{"weakness":"..","severity":"HIGH"}]}]
    synthesis_model_used      = Column(String(64), nullable=True)
    analyzed_at               = Column(DateTime, nullable=False, index=True)

    __table_args__ = (
        Index("ix_competitor_analysis_niche_cluster", "niche_id", "cluster_id"),
    )
```

---

## Table 19 — orders

Manual order entry for revenue gate tracking. User adds orders through dashboard.

```python
# src/models/order.py
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from .base import Base

class Order(Base):
    __tablename__ = "orders"

    id                = Column(Integer, primary_key=True)
    order_id          = Column(String(36), nullable=False, unique=True, index=True)
    # UUID4 generated at entry
    niche_id          = Column(String(64), ForeignKey("niche_configs.niche_id"),
                            nullable=False, index=True)
    order_date        = Column(DateTime, nullable=False, index=True)
    gross_usd         = Column(Float, nullable=False)
    net_usd           = Column(Float, nullable=False)
    # net_usd = gross_usd × (1 - fiverr_share)
    keyword_text      = Column(String(512), nullable=True)
    # Optional: which keyword/gig this order came from
    trust_stage       = Column(String(32), nullable=True)
    # "0_reviews" | "1_4_orders" | "5_plus_orders" | "level_1" | "10_plus_reviews"
    notes             = Column(Text, nullable=True)
    entered_at        = Column(DateTime, nullable=False)
    # When user entered this order into the system
```

---

## Table 20 — alerts

System alerts for staleness, new opportunities, LLM cost threshold, and run failures.

```python
# src/models/alert.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from .base import Base

class Alert(Base):
    __tablename__ = "alerts"

    id           = Column(Integer, primary_key=True)
    run_id       = Column(String(36), ForeignKey("run_logs.run_id"), nullable=True, index=True)
    alert_type   = Column(String(64), nullable=False, index=True)
    # STALE_DATA | NEW_STRONG_GO | LLM_COST_THRESHOLD | JOB_DEAD_LETTER_HIGH | AUTO_PROMOTION
    severity     = Column(String(16), nullable=False, index=True)
    # INFO | WARNING | ERROR
    niche_id     = Column(String(64), nullable=True, index=True)
    message      = Column(Text, nullable=False)
    detail       = Column(Text, nullable=True)
    resolved     = Column(Boolean, nullable=False, default=False, index=True)
    resolved_at  = Column(DateTime, nullable=True)
    created_at   = Column(DateTime, nullable=False, index=True)
```

---

## Table 21 — run_niches (Association Table)

Associates runs with the niches processed in that run.

```python
# src/models/run_niche.py
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from .base import Base

run_niches = Table(
    "run_niches",
    Base.metadata,
    Column("run_id", String(36), ForeignKey("run_logs.run_id", ondelete="CASCADE"),
        primary_key=True),
    Column("niche_id", String(64), ForeignKey("niche_configs.niche_id"),
        primary_key=True),
    Column("depth_used", String(32), nullable=False),
    Column("keywords_processed", Integer, nullable=False, default=0),
    Column("gigs_collected", Integer, nullable=False, default=0),
)
```

---

## Alembic Initial Migration (env.py setup note)

The initial migration creates all 21 tables with all indexes and constraints. Run sequence:

```bash
alembic init alembic           # Initialize Alembic
alembic revision --autogenerate -m "initial_schema"
alembic upgrade head           # Create all tables
```

SQLite does not support all ALTER TABLE operations — breaking schema changes in SQLite must use the `recreate` strategy in Alembic. PostgreSQL migration in v2 uses standard Alembic operations.


---

## SRDI ADDENDUM -- Schema Extensions and New Models
**Source:** WAVE_I; Epic R8 (SCRUM-583 to SCRUM-590)
**Migration scripts:** M1 through M6 plus M-ext (additive, idempotent)
**Backward compat rule:** NULL on any new column = unknown = include

### New Table: result_set_validations (M1)

Unique on (keyword_id, run_id). One row per keyword per run.

Columns: id PK, keyword_id FK, run_id, result_set_relevance_score REAL DEFAULT 1.0,
total_gigs_analyzed INT, relevant_gig_count INT, sponsored_gig_count INT,
organic_relevant_count INT, category_contamination_flag BOOL,
ghost_market_flag BOOL, used_fallback_strictness BOOL,
fallback_strictness_used VARCHAR(20), confidence_deduction REAL DEFAULT 0.0,
llm_validated BOOL DEFAULT FALSE, llm_relevant_count INT, llm_verdict VARCHAR(20),
contamination_explanation VARCHAR(500), dominant_competing_service VARCHAR(200),
per_gig_relevance JSON, validation_warnings JSON, validated_at DATETIME

Indexes: idx_rsv_keyword_id, idx_rsv_run_id, idx_rsv_keyword_run (compound),
idx_rsv_ghost (partial WHERE ghost_market_flag=TRUE),
idx_rsv_contamination (partial WHERE category_contamination_flag=TRUE)

### Additive Columns: gigs table (M2)

is_sponsored BOOL (idx partial)  -- from gig_cards; NULL = organic = include
is_zombie BOOL (idx partial)     -- from Stage 4.5; NULL = non-zombie = include
zombie_score REAL                -- 0.0-1.0; threshold 0.50
zombie_signals JSON              -- contributing signals dict
last_reviewed_at DATETIME        -- latest review date from snippets
relevance_flag BOOL (idx)        -- from Stage 3.5; NULL = include
relevance_score REAL             -- per-gig 0.0-1.0
category_path VARCHAR(200)       -- e.g. "Programming & Tech > Desktop Applications"
Compound index: idx_gigs_scoring_filter (is_sponsored, is_zombie, relevance_flag)

### Additive Columns: search_results table (M3)

search_strictness_used VARCHAR(20) NOT NULL DEFAULT 'NONE'
result_set_relevance_score REAL    -- denormalized from RSV
category_contamination_flag BOOL DEFAULT FALSE
ghost_market_flag BOOL DEFAULT FALSE
sponsored_gig_count INT DEFAULT 0
organic_gig_count INT
pages_collected INT DEFAULT 1
Indexes: idx_sr_strictness, idx_sr_ghost (partial), idx_sr_ghost_keyword

### Additive Columns: keyword_scores table (M4)

relevance_qualifier REAL DEFAULT 1.0  -- from RSV; 0.0-1.0
trc_reliability_score REAL            -- R4.1 single multiplier
qualified_trc REAL                    -- TRC * trc_reliability
sponsored_gigs_excluded INT DEFAULT 0
zombie_gigs_excluded INT DEFAULT 0
clean_gig_count INT

### Additive Columns: keywords table (M5)

discovery_needs_recollection BOOL DEFAULT FALSE
pre_validation_data JSON          -- Gate 2 dry-run evidence
specificity_confidence REAL       -- 0.0-1.0
Index: idx_kw_needs_recollection (partial WHERE TRUE)

### Additive Columns: discovery_outcomes table (M6)

is_invalid BOOL DEFAULT FALSE     -- ghost market = invalid, NOT a miss
is_contaminated BOOL DEFAULT FALSE
invalid_reason VARCHAR
relevance_score REAL              -- RSV at time of evaluation
pre_validation_passed BOOL
Indexes: idx_do_is_invalid (partial), idx_do_is_contaminated (partial)

### Additive Columns: external_signals table (M-ext)

fiverr_relevance_qualifier REAL   -- 0.20-0.95; written by R7
signal_quality_score REAL         -- sqrt(freshness x relevance)

### Migration Order (MUST follow)

M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M-ext

Each migration uses IF NOT EXISTS or column-exists guards. Safe to re-run.
Apply+rollback rehearsed on a DB copy before running on live DB.
See 03_data/RESULT_SET_VALIDATION.md for full DDL.
