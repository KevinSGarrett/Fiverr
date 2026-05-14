"""Analysis package exports for Cycle 003 dry-run engines."""

from src.analysis.clustering import cluster_keywords
from src.analysis.competitors import profile_competitors
from src.analysis.contracts import (
    AnalysisError,
    AnalysisRunSummary,
    AnalysisStageSummary,
    AnalysisStatus,
    AnalysisTaskType,
    AnalysisWarning,
    ClusterEntry,
    CompetitorListingInput,
    CompetitorProfileInput,
    CompetitorProfileResult,
    GigQualityInput,
    GigQualityResult,
    KeywordClusterInput,
    KeywordClusterResult,
)
from src.analysis.gig_quality import score_gig_quality
from src.analysis.keyword_features import (
    KeywordFeatureError,
    build_keyword_feature_set,
    build_lexical_features,
    extract_tokens,
    normalize_keyword,
    vectorize_keywords,
)
from src.analysis.orchestrator import run_analysis_dry_run

__all__ = [
    "AnalysisError",
    "AnalysisRunSummary",
    "AnalysisStageSummary",
    "AnalysisStatus",
    "AnalysisTaskType",
    "AnalysisWarning",
    "ClusterEntry",
    "CompetitorListingInput",
    "CompetitorProfileInput",
    "CompetitorProfileResult",
    "GigQualityInput",
    "GigQualityResult",
    "KeywordClusterInput",
    "KeywordClusterResult",
    "KeywordFeatureError",
    "build_keyword_feature_set",
    "build_lexical_features",
    "cluster_keywords",
    "extract_tokens",
    "normalize_keyword",
    "profile_competitors",
    "run_analysis_dry_run",
    "score_gig_quality",
    "vectorize_keywords",
]
