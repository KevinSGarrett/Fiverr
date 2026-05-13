"""Collection package interfaces and safety helpers."""

from src.collection.contracts import (
    CollectionError,
    CollectionStageInput,
    CollectionStageResult,
    CollectionStageStatus,
)
from src.collection.playwright_check import check_playwright_chromium_available
from src.collection.safety import (
    FORBIDDEN_COLLECTION_ACTIONS,
    SAFE_COLLECTION_MODES,
    validate_collection_action,
)

__all__ = [
    "CollectionError",
    "CollectionStageInput",
    "CollectionStageResult",
    "CollectionStageStatus",
    "check_playwright_chromium_available",
    "FORBIDDEN_COLLECTION_ACTIONS",
    "SAFE_COLLECTION_MODES",
    "validate_collection_action",
]
