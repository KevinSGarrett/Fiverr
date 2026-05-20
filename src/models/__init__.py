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
from src.models.external_signal import (
    ExternalSignal,
    get_all_signals,
    get_signal,
    write_external_signal,
)
from src.models.gig import Gig, get_gigs_for_keyword, write_gig_card
from src.models.gig_quality_score import (
    GigQualityScore,
    get_analysis_complete_count,
    get_gig_quality_scores,
    write_gig_quality_score,
)
from src.models.job import Job
from src.models.keyword_score import KeywordScore
from src.models.market import (
    AutocompleteSuggestion,
    Keyword,
    Review,
    write_autocomplete_suggestion,
)
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
from src.models.search_result import SearchResult, get_latest_search_result, write_search_result
from src.models.seller import Seller, get_seller, write_seller_profile
from src.models.visual import GigVisualAnalysis

__all__ = [
    "AlertEvent",
    "AnalysisResult",
    "AnalysisRun",
    "AnalysisSignalRecord",
    "AutocompleteSuggestion",
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
    "GigQualityScore",
    "GigVisualAnalysis",
    "get_gigs_for_keyword",
    "IntegerPrimaryKeyMixin",
    "Job",
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
    "get_all_signals",
    "get_analysis_complete_count",
    "get_gig_quality_scores",
    "get_signal",
    "get_registered_model_classes",
    "get_registered_table_names",
    "naming_convention",
    "safe_json_default",
    "write_gig_card",
    "write_gig_quality_score",
    "write_autocomplete_suggestion",
    "write_search_result",
    "write_external_signal",
    "write_seller_profile",
    "get_seller",
    "get_latest_search_result",
    "utc_now",
]
