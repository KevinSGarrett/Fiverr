"""Collection package interfaces and safety helpers."""

from src.collection.autocomplete import (
    AutocompleteFixtureError,
    AutocompletePlan,
    AutocompleteSuggestion,
    load_autocomplete_fixture,
)
from src.collection.checkpoint import (
    QueueCheckpointError,
    checkpoint_queue_state,
    load_queue_checkpoint,
)
from src.collection.community_signals import CommunitySignal, load_community_signal_fixture
from src.collection.contracts import CollectionError, CollectionStageResult, CollectionStageStatus
from src.collection.external_signals import (
    ExternalSignal,
    LiveSignalConnectorDisabledError,
    SignalFreshness,
    SignalSource,
    fetch_external_signals_live,
    load_external_signal_fixture,
)
from src.collection.gig_detail import GigDetailParseResult, GigPackage, parse_gig_detail_from_html
from src.collection.keyword_expansion import (
    ExpandedKeyword,
    KeywordExpansionResult,
    expand_keywords,
)
from src.collection.orchestrator import run_collection_dry_run
from src.collection.pacing import PacingConfig, PacingManager
from src.collection.playwright_check import check_playwright_chromium_available
from src.collection.proxy import ProxyConfig, ProxyProvider
from src.collection.queue import CollectionQueue, QueueJob, QueueJobStatus, enqueue_search_plan
from src.collection.safety import (
    FORBIDDEN_COLLECTION_ACTIONS,
    SAFE_COLLECTION_MODES,
    validate_collection_action,
)
from src.collection.search_plan import SearchPlan, SearchPlanItem, build_search_plan
from src.collection.selectors import (
    ParsedSearchCard,
    get_selector,
    parse_search_result_cards_from_html,
    validate_selector_registry,
)
from src.collection.seller_profile import (
    SellerProfileParseResult,
    parse_seller_profile_from_html,
    redact_sensitive_text,
)
from src.collection.session import (
    BrowserSessionConfig,
    ManagedBrowserSession,
    build_browser_launch_options,
    validate_storage_state_path,
)

# Spec-name aliases (AC compliance for E02 class interface names)
SessionManager = ManagedBrowserSession  # Spec name: SessionManager
QueueProcessor = CollectionQueue  # Spec name: QueueProcessor

__all__ = [
    "CollectionError",
    "CollectionStageResult",
    "CollectionStageStatus",
    "AutocompleteFixtureError",
    "AutocompleteSuggestion",
    "AutocompletePlan",
    "load_autocomplete_fixture",
    "GigPackage",
    "GigDetailParseResult",
    "parse_gig_detail_from_html",
    "SellerProfileParseResult",
    "parse_seller_profile_from_html",
    "redact_sensitive_text",
    "ExternalSignal",
    "SignalSource",
    "SignalFreshness",
    "load_external_signal_fixture",
    "fetch_external_signals_live",
    "LiveSignalConnectorDisabledError",
    "CommunitySignal",
    "load_community_signal_fixture",
    "PacingConfig",
    "PacingManager",
    "QueueJob",
    "QueueJobStatus",
    "CollectionQueue",
    "enqueue_search_plan",
    "ParsedSearchCard",
    "get_selector",
    "validate_selector_registry",
    "parse_search_result_cards_from_html",
    "QueueCheckpointError",
    "checkpoint_queue_state",
    "load_queue_checkpoint",
    "BrowserSessionConfig",
    "build_browser_launch_options",
    "validate_storage_state_path",
    "ManagedBrowserSession",
    "ExpandedKeyword",
    "KeywordExpansionResult",
    "expand_keywords",
    "SearchPlanItem",
    "SearchPlan",
    "build_search_plan",
    "run_collection_dry_run",
    "ProxyConfig",
    "ProxyProvider",
    "check_playwright_chromium_available",
    "FORBIDDEN_COLLECTION_ACTIONS",
    "SAFE_COLLECTION_MODES",
    "validate_collection_action",
    # Spec-name aliases
    "SessionManager",
    "QueueProcessor",
]
