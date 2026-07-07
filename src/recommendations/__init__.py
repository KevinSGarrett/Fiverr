"""Recommendation engine — E05.

This package contains TWO parallel recommendation-generation stacks with different
production entrypoints (SCRUM-1112). Know which one you are editing:

Stack A — CLI batch path:
    pipeline.py (run_recommendations_pipeline) -> context_builder.py
    (build_recommendation_context) -> executor.py (generate_recommendation)
    -> llm_tasks.py (task_*) -> storage.py (save_recommendation)
    Invoked by: src/orchestrator.py mode="recommendations-only" and run.py.
    Its context has NO pricing fields.

Stack B — score-triggered auto path:
    context.py (RecommendationContext / build_recommendation_context, the
    pricing-aware builder) -> tasks.py (generate_*) -> storage.py
    (write_recommendation)
    Invoked by: src/scoring/pipeline.py's _maybe_auto_generate_recommendation
    after STRONG_GO/CONDITIONAL_GO scores.

run.py's run_recommendations_stage and orchestrator.py's RecommendationOrchestrator
have NO production callers (tests only). A bug fix applied to one stack does not
automatically fix the other — check both before closing a defect. Consolidating the
stacks is tracked separately; do not add new callers to the unwired entrypoints.
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
from src.recommendations.contracts import (
    RecommendationOutput as ContractRecommendationOutput,
)
from src.recommendations.eligibility import (
    get_eligible_keywords,
    passes_recommendation_gates,
    should_regenerate_recommendation,
)
from src.recommendations.executor import generate_recommendation
from src.recommendations.export import (
    export_recommendation_json,
    export_recommendation_markdown,
)
from src.recommendations.llm_tasks import (
    task_buyer_persona,
    task_description_outline,
    task_differentiation_angle,
    task_faq_entries,
    task_gig_titles,
    task_niche_viability,
    task_package_structure,
    task_red_flags,
    task_tag_sets,
    task_thumbnail_direction,
    task_upsell_structure,
)
from src.recommendations.orchestrator import RecommendationOrchestrator
from src.recommendations.pipeline import run_recommendations_pipeline
from src.recommendations.run import run_recommendations_stage
from src.recommendations.schemas import (
    BuyerPersonaOutput,
    DescriptionOutlineOutput,
    DifferentiationAngleOutput,
    FaqEntriesOutput,
    GigTitlesOutput,
    NicheViabilityOutput,
    PackageStructureOutput,
    RecommendationOutput,
    RedFlagsOutput,
    TagSetsOutput,
    ThumbnailDirectionOutput,
    UpsellStructureOutput,
)
from src.recommendations.storage import (
    get_recommendation,
    run_save_recommendations,
    save_recommendation,
    write_recommendation,
)
from src.recommendations.tasks import (
    RECOMMENDATION_FIELD_NAMES,
    generate_buyer_persona,
    generate_description_outline,
    generate_differentiation_angle,
    generate_faq_entries,
    generate_gig_titles,
    generate_niche_viability,
    generate_package_structure,
    generate_red_flags,
    generate_tag_sets,
    generate_thumbnail_direction,
    generate_upsell_structure,
)
from src.recommendations.tasks import (
    generate_recommendation as generate_recommendation_legacy,
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
    "run_recommendations_pipeline",
    "ContractRecommendationOutput",
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
    "save_recommendation",
    "get_recommendation",
    "run_save_recommendations",
    "export_recommendation_markdown",
    "export_recommendation_json",
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
    "generate_recommendation_legacy",
    "GigTitlesOutput",
    "TagSetsOutput",
    "PackageStructureOutput",
    "DescriptionOutlineOutput",
    "FaqEntriesOutput",
    "DifferentiationAngleOutput",
    "BuyerPersonaOutput",
    "ThumbnailDirectionOutput",
    "UpsellStructureOutput",
    "RedFlagsOutput",
    "NicheViabilityOutput",
    "task_gig_titles",
    "task_tag_sets",
    "task_package_structure",
    "task_description_outline",
    "task_faq_entries",
    "task_differentiation_angle",
    "task_buyer_persona",
    "task_thumbnail_direction",
    "task_upsell_structure",
    "task_red_flags",
    "task_niche_viability",
]
