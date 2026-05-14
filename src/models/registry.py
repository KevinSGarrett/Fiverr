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

# The source target is 28 tables; only tables declared as SQLAlchemy models are implemented.
# Pending names are explicit placeholders until SCHEMA/FIELD_CATALOG source docs are restored.
PENDING_SOURCE_TABLE_NAMES = (
    "pending_source_table_01",
    "pending_source_table_02",
    "pending_source_table_03",
    "pending_source_table_04",
    "pending_source_table_05",
    "pending_source_table_06",
    "pending_source_table_07",
)


def get_registered_model_classes() -> tuple[type[object], ...]:
    """Return currently implemented SQLAlchemy model classes."""
    return tuple(REGISTERED_MODEL_CLASSES)


def get_registered_table_names() -> list[str]:
    """Return unique, sorted table names from registered model classes."""
    table_names = [str(model.__tablename__) for model in REGISTERED_MODEL_CLASSES]
    return sorted(set(table_names))


def get_missing_source_tables() -> list[str]:
    """Return deterministic source tables that are still pending."""
    return list(PENDING_SOURCE_TABLE_NAMES)
