"""Collection package interfaces and safety helpers."""

from src.collection.checkpoint import (
    QueueCheckpointError,
    checkpoint_queue_state,
    load_queue_checkpoint,
)
from src.collection.contracts import CollectionError, CollectionStageResult, CollectionStageStatus
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
from src.collection.session import (
    BrowserSessionConfig,
    ManagedBrowserSession,
    build_browser_launch_options,
    validate_storage_state_path,
)

__all__ = [
    "CollectionError",
    "CollectionStageResult",
    "CollectionStageStatus",
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
]
