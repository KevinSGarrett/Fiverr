"""SQLAlchemy model package exports."""

from src.models.analysis import (
    AnalysisResult,
    AnalysisRun,
    AnalysisSignalRecord,
    CompetitorSnapshot,
    DiscoveryHypothesis,
    PricingSnapshot,
)
from src.models.associations import KeywordGigAssociation
from src.models.auto_promotion import AutoPromotionLog
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
from src.models.discovery import DiscoveryCandidate
from src.models.discovery_cycle import DiscoveryCycleLog
from src.models.keyword_score import KeywordScore
from src.models.market import ExternalSignal, Gig, Keyword, Review, SearchResult, Seller
from src.models.niche import Niche, NicheConfigRecord
from src.models.order import Order
from src.models.pricing import PriceAnalysis
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
from src.models.visual import GigVisualAnalysis

__all__ = [
    "AlertEvent",
    "AnalysisResult",
    "AnalysisRun",
    "AnalysisSignalRecord",
    "AutoPromotionLog",
    "Base",
    "CompetitorSnapshot",
    "DiscoveryCandidate",
    "DiscoveryCycleLog",
    "DiscoveryHypothesis",
    "ExportArtifact",
    "ExternalSignal",
    "ExternalSourceMixin",
    "FinalScore",
    "Gig",
    "GigVisualAnalysis",
    "IntegerPrimaryKeyMixin",
    "JobStatus",
    "Keyword",
    "KeywordScore",
    "KeywordGigAssociation",
    "LLMCacheRecord",
    "LLMUsageLog",
    "MetadataJSONMixin",
    "Niche",
    "NicheConfigRecord",
    "Order",
    "PricingSnapshot",
    "PriceAnalysis",
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
