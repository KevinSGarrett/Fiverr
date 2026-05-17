"""Recommendation engine — E05 scaffold.

Full implementation: SCRUM-178 through SCRUM-186.
"""

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
from src.recommendations.orchestrator import RecommendationOrchestrator

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
]
