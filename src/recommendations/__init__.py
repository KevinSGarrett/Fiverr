"""Recommendation engine — E05 scaffold.

Full implementation: SCRUM-178 through SCRUM-186.
"""

from src.recommendations.context import (
    RecommendationContext as RecommendationEngineContext,
)
from src.recommendations.context import (
    build_recommendation_context,
)
from src.recommendations.contracts import (
    BuyerPersona,
    DescriptionOutline,
    DescriptionSection,
    DifferentiationAngle,
    FAQEntry,
    GigTitle,
    NicheViability,
    PackageStructure,
    PackageTier,
    PricingStrategy,
    ProfileOptimization,
    RecommendationContext,
    RecommendationOutput,
    RedFlagsAssessment,
    TagSet,
    ThumbnailDirection,
    UpsellExtra,
    UpsellStructure,
    VisualRecommendations,
)
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.orchestrator import RecommendationOrchestrator
from src.recommendations.tasks import (
    generate_differentiation_angle,
    generate_gig_titles,
    generate_red_flags,
    generate_tag_sets,
)

__all__ = [
    "BuyerPersona",
    "DescriptionOutline",
    "DescriptionSection",
    "DifferentiationAngle",
    "FAQEntry",
    "GigTitle",
    "NicheViability",
    "PackageStructure",
    "PackageTier",
    "PricingStrategy",
    "ProfileOptimization",
    "RedFlagsAssessment",
    "RecommendationContext",
    "RecommendationOrchestrator",
    "RecommendationOutput",
    "TagSet",
    "ThumbnailDirection",
    "UpsellExtra",
    "UpsellStructure",
    "VisualRecommendations",
    "RecommendationEngineContext",
    "build_recommendation_context",
    "get_eligible_keywords",
    "passes_recommendation_gates",
    "should_regenerate_recommendation",
    "generate_gig_titles",
    "generate_tag_sets",
    "generate_differentiation_angle",
    "generate_red_flags",
]
