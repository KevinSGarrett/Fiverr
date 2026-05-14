"""Collection package interfaces and safety helpers."""

from src.collection.checkpoint import CheckpointCorruptionError, CheckpointManager
from src.collection.contracts import (
    CollectionError,
    CollectionStageInput,
    CollectionStageResult,
    CollectionStageStatus,
)
from src.collection.orchestrator import CollectionOrchestrator, CollectionStage
from src.collection.pacing import PacingConfig, PacingManager
from src.collection.playwright_check import check_playwright_chromium_available
from src.collection.proxy import ProxyConfig, ProxyProvider
from src.collection.queue import CollectionJob, JobPriority, JobStatus, QueueProcessor, RetryPolicy
from src.collection.safety import (
    FORBIDDEN_COLLECTION_ACTIONS,
    SAFE_COLLECTION_MODES,
    validate_collection_action,
)
from src.collection.selectors import (
    SelectorEntry,
    explain_missing_required_selectors,
    get_selector_group,
    list_selector_groups,
    validate_selector_registry,
)
from src.collection.session import BrowserMode, PlaywrightSessionManager, SessionManagerConfig

__all__ = [
    "CollectionError",
    "CollectionStageInput",
    "CollectionStageResult",
    "CollectionStageStatus",
    "CollectionOrchestrator",
    "CollectionStage",
    "PacingConfig",
    "PacingManager",
    "CollectionJob",
    "JobPriority",
    "JobStatus",
    "RetryPolicy",
    "QueueProcessor",
    "SelectorEntry",
    "list_selector_groups",
    "get_selector_group",
    "validate_selector_registry",
    "explain_missing_required_selectors",
    "CheckpointManager",
    "CheckpointCorruptionError",
    "BrowserMode",
    "SessionManagerConfig",
    "PlaywrightSessionManager",
    "ProxyConfig",
    "ProxyProvider",
    "check_playwright_chromium_available",
    "FORBIDDEN_COLLECTION_ACTIONS",
    "SAFE_COLLECTION_MODES",
    "validate_collection_action",
]
