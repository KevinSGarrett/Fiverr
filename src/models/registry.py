"""Explicit SQLAlchemy model and table registry."""

from __future__ import annotations

from src.models.analysis import (
    AnalysisResult,
    AnalysisRun,
    AnalysisSignalRecord,
    CompetitorSnapshot,
    DiscoveryHypothesis,
    PricingSnapshot,
)
from src.models.collection_runtime import (
    CollectionCheckpoint,
    CollectionProxyEvent,
    CollectionQueueItem,
    CollectionSelectorAudit,
    CollectionSessionEvent,
)
from src.models.external_signal import ExternalSignal
from src.models.gig import Gig
from src.models.job import Job
from src.models.market import AutocompleteSuggestion, ClusterAssignment, ClusterLabel, Keyword, Review
from src.models.niche import Niche, NicheConfigRecord
from src.models.runtime import (
    AlertEvent,
    ExportArtifact,
    JobStatus,
    LLMCacheRecord,
    LLMUsageLog,
    ReportRun,
    ReportSection,
    RunLog,
)
from src.models.scoring import FinalScore, Recommendation, ScoreComponent
from src.models.search_result import SearchResult
from src.models.seller import Seller

REGISTERED_MODEL_CLASSES = (
    NicheConfigRecord,
    Niche,
    Keyword,
    AutocompleteSuggestion,
    ClusterAssignment,
    ClusterLabel,
    SearchResult,
    Gig,
    Seller,
    Review,
    ExternalSignal,
    AnalysisRun,
    AnalysisResult,
    PricingSnapshot,
    DiscoveryHypothesis,
    CompetitorSnapshot,
    AnalysisSignalRecord,
    ScoreComponent,
    FinalScore,
    Recommendation,
    Job,
    RunLog,
    JobStatus,
    AlertEvent,
    ExportArtifact,
    LLMUsageLog,
    LLMCacheRecord,
    CollectionCheckpoint,
    CollectionProxyEvent,
    CollectionQueueItem,
    CollectionSelectorAudit,
    CollectionSessionEvent,
    ReportRun,
    ReportSection,
)

# Source-required Foundation target table set (28 total — all implemented):
SOURCE_REQUIRED_TABLE_NAMES = (
    "alert_events",
    "analysis_results",
    "analysis_runs",
    "analysis_signal_records",
    "competitor_snapshots",
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

PHASE2_REQUIRED_TABLE_NAMES = (
    "analysis_runs",
    "analysis_results",
    "analysis_signal_records",
    "competitor_snapshots",
    "external_signals",
    "gigs",
    "keywords",
    "search_results",
    "sellers",
)

TABLE_DOMAIN_MAP = {
    "collection": {
        "keywords",
        "search_results",
        "gigs",
        "sellers",
        "reviews",
        "autocomplete_suggestions",
        "external_signals",
    },
    "analysis": {
        "analysis_runs",
        "analysis_results",
        "pricing_snapshots",
        "discovery_hypotheses",
        "competitor_snapshots",
        "analysis_signal_records",
        "cluster_assignments",
        "cluster_labels",
    },
    "scoring": {"score_components", "final_scores", "recommendations"},
    "runtime": {"run_logs", "jobs", "job_statuses", "alert_events", "export_artifacts", "llm_usage_logs", "llm_cache_records"},
    "niche": {"niche_configs", "niches"},
}


def get_registered_model_classes() -> tuple[type[object], ...]:
    """Return currently implemented SQLAlchemy model classes."""
    return tuple(REGISTERED_MODEL_CLASSES)


def get_registered_table_names() -> list[str]:
    """Return unique, sorted table names from registered model classes."""
    table_names = [str(model.__tablename__) for model in REGISTERED_MODEL_CLASSES]
    return sorted(set(table_names))


def get_registered_tables_by_domain() -> dict[str, list[str]]:
    """Return deterministic table grouping for collection/analysis/runtime domains."""
    registered = set(get_registered_table_names())
    classified: dict[str, list[str]] = {}
    for domain in sorted(TABLE_DOMAIN_MAP):
        domain_tables = sorted(registered.intersection(TABLE_DOMAIN_MAP[domain]))
        classified[domain] = domain_tables
    return classified


def verify_required_phase2_tables(table_names: list[str] | None = None) -> list[str]:
    """Return deterministic list of missing Phase 2 support tables."""
    available = set(table_names if table_names is not None else get_registered_table_names())
    required = set(PHASE2_REQUIRED_TABLE_NAMES)
    return sorted(required - available)


def get_missing_source_tables() -> list[str]:
    """Return deterministic source-required table names still pending implementation."""
    registered = set(get_registered_table_names())
    source_required = set(SOURCE_REQUIRED_TABLE_NAMES)
    return sorted(source_required - registered)
