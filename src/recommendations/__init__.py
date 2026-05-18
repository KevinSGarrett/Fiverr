"""Recommendation engine — E05 scaffold.

Full implementation: SCRUM-178 through SCRUM-186.
"""

from src.recommendations.context import (
    RecommendationContext,
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
    RecommendationOutput,
    RedFlagsAssessment,
    TagSet,
    ThumbnailDirection,
    UpsellExtra,
    UpsellStructure,
    VisualRecommendations,
)
from src.recommendations.contracts import (
    RecommendationContext as RecommendationContractContext,
)
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.orchestrator import RecommendationOrchestrator
from src.recommendations.run import run_recommendations_stage
from src.recommendations.storage import write_recommendation
from src.recommendations.tasks import (
    RECOMMENDATION_FIELD_NAMES,
    generate_buyer_persona,
    generate_description_outline,
    generate_differentiation_angle,
    generate_faq_entries,
    generate_gig_titles,
    generate_niche_viability,
    generate_package_structure,
    generate_recommendation,
    generate_red_flags,
    generate_tag_sets,
    generate_thumbnail_direction,
    generate_upsell_structure,
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
    "run_recommendations_stage",
    "RecommendationOutput",
    "TagSet",
    "ThumbnailDirection",
    "UpsellExtra",
    "UpsellStructure",
    "VisualRecommendations",
    "RecommendationContractContext",
    "build_recommendation_context",
    "get_eligible_keywords",
    "passes_recommendation_gates",
    "should_regenerate_recommendation",
    "write_recommendation",
    "RECOMMENDATION_FIELD_NAMES",
    "generate_gig_titles",
    "generate_tag_sets",
    "generate_package_structure",
    "generate_description_outline",
    "generate_faq_entries",
    "generate_differentiation_angle",
    "generate_buyer_persona",
    "generate_thumbnail_direction",
    "generate_upsell_structure",
    "generate_red_flags",
    "generate_niche_viability",
    "generate_recommendation",
]
