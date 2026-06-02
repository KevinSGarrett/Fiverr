"""Dashboard package exports."""

from src.dashboard.alert_generator import ALERT_TYPES, generate_relevance_alerts_for_run
from src.dashboard.app import (
    build_app_entry_query_diagnostics,
    build_page_title,
    get_available_pages,
    get_cycle003_status_state,
    main,
)
from src.dashboard.badge_renderer import BADGE_TYPES, render_keyword_integrity_badge
from src.dashboard.navigation import DashboardPage
from src.dashboard.query_layer import DashboardQueryLayer, get_dashboard_query_layer
from src.dashboard.relevance_dashboard import (
    build_data_integrity_block,
    calculate_niche_relevance_quality_score,
    get_opportunities_for_display,
    run_summary_relevance_block,
)
from src.dashboard.schemas import (
    OpportunityCardSchema,
    PriceLadderDisplayStep,
    PricingDisplaySchema,
    ScoreBreakdown,
)
from src.dashboard.state import DashboardState, build_cycle003_status_state

__all__ = [
    "DashboardPage",
    "DashboardQueryLayer",
    "DashboardState",
    "ALERT_TYPES",
    "BADGE_TYPES",
    "OpportunityCardSchema",
    "PriceLadderDisplayStep",
    "PricingDisplaySchema",
    "ScoreBreakdown",
    "build_app_entry_query_diagnostics",
    "build_cycle003_status_state",
    "build_data_integrity_block",
    "build_page_title",
    "calculate_niche_relevance_quality_score",
    "generate_relevance_alerts_for_run",
    "get_dashboard_query_layer",
    "get_opportunities_for_display",
    "get_available_pages",
    "get_cycle003_status_state",
    "main",
    "render_keyword_integrity_badge",
    "run_summary_relevance_block",
]

