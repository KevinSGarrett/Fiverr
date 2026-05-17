"""Reddit signals workflow — Stage 6b (Story 2.12)."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import community_signals as _mod


class RedditSignalWorkflow:
    """Collects Reddit demand signals for each keyword via subreddit search."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
