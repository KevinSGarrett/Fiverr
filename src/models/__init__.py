"""SQLAlchemy model package exports."""

from src.models.analysis import AnalysisResult, AnalysisRun, DiscoveryHypothesis, PricingSnapshot
from src.models.base import (
    Base,
    ExternalSourceMixin,
    IntegerPrimaryKeyMixin,
    MetadataJSONMixin,
    SoftStatusMixin,
    TimestampMixin,
    naming_convention,
    safe_json_default,
    utc_now,
)
from src.models.market import ExternalSignal, Gig, Keyword, Review, SearchResult, Seller
from src.models.niche import Niche, NicheConfigRecord
from src.models.registry import (
    get_missing_source_tables,
    get_registered_model_classes,
    get_registered_table_names,
)
from src.models.runtime import (
    AlertEvent,
    ExportArtifact,
    JobStatus,
    LLMCacheRecord,
    LLMUsageLog,
    RunLog,
)
from src.models.scoring import FinalScore, Recommendation, ScoreComponent

__all__ = [
    "AlertEvent",
    "AnalysisResult",
    "AnalysisRun",
    "Base",
    "DiscoveryHypothesis",
    "ExportArtifact",
    "ExternalSignal",
    "ExternalSourceMixin",
    "FinalScore",
    "Gig",
    "IntegerPrimaryKeyMixin",
    "JobStatus",
    "Keyword",
    "LLMCacheRecord",
    "LLMUsageLog",
    "MetadataJSONMixin",
    "Niche",
    "NicheConfigRecord",
    "PricingSnapshot",
    "Recommendation",
    "Review",
    "RunLog",
    "ScoreComponent",
    "SearchResult",
    "Seller",
    "SoftStatusMixin",
    "TimestampMixin",
    "get_missing_source_tables",
    "get_registered_model_classes",
    "get_registered_table_names",
    "naming_convention",
    "safe_json_default",
    "utc_now",
]
