"""Explicit SQLAlchemy model and table registry."""

from __future__ import annotations

from src.models.analysis import AnalysisResult, AnalysisRun, DiscoveryHypothesis, PricingSnapshot
from src.models.market import ExternalSignal, Gig, Keyword, Review, SearchResult, Seller
from src.models.niche import Niche, NicheConfigRecord
from src.models.runtime import (
    AlertEvent,
    ExportArtifact,
    JobStatus,
    LLMCacheRecord,
    LLMUsageLog,
    RunLog,
)
from src.models.scoring import FinalScore, Recommendation, ScoreComponent

REGISTERED_MODEL_CLASSES = (
    NicheConfigRecord,
    Niche,
    Keyword,
    SearchResult,
    Gig,
    Seller,
    Review,
    ExternalSignal,
    AnalysisRun,
    AnalysisResult,
    PricingSnapshot,
    DiscoveryHypothesis,
    ScoreComponent,
    FinalScore,
    Recommendation,
    RunLog,
    JobStatus,
    AlertEvent,
    ExportArtifact,
    LLMUsageLog,
    LLMCacheRecord,
)

# Source-required Foundation target table set (28 total):
# - 21 currently implemented SQLAlchemy tables.
# - 7 pending collection/report persistence tables declared in the Foundation backlog.
SOURCE_REQUIRED_TABLE_NAMES = (
    "alert_events",
    "analysis_results",
    "analysis_runs",
    "collection_checkpoints",
    "collection_proxy_events",
    "collection_queue_items",
    "collection_selector_audits",
    "collection_session_events",
    "discovery_hypotheses",
    "export_artifacts",
    "final_scores",
    "gigs",
    "job_statuses",
    "keywords",
    "llm_cache_records",
    "llm_usage_logs",
    "niche_configs",
    "niches",
    "pricing_snapshots",
    "recommendations",
    "report_runs",
    "report_sections",
    "reviews",
    "run_logs",
    "score_components",
    "search_results",
    "sellers",
    "external_signals",
)


def get_registered_model_classes() -> tuple[type[object], ...]:
    """Return currently implemented SQLAlchemy model classes."""
    return tuple(REGISTERED_MODEL_CLASSES)


def get_registered_table_names() -> list[str]:
    """Return unique, sorted table names from registered model classes."""
    table_names = [str(model.__tablename__) for model in REGISTERED_MODEL_CLASSES]
    return sorted(set(table_names))


def get_missing_source_tables() -> list[str]:
    """Return deterministic source-required table names still pending implementation."""
    registered = set(get_registered_table_names())
    source_required = set(SOURCE_REQUIRED_TABLE_NAMES)
    return sorted(source_required - registered)
