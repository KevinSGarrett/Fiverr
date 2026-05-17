"""Keyword expansion workflow — Stage 2 (Story 2.7)."""
from __future__ import annotations

from types import ModuleType
from typing import Any

from src.collection import keyword_expansion as _mod


class KeywordExpansionWorkflow:
    """Wraps keyword_expansion module; expands seed keywords via Fiverr autocomplete."""

    def run(self, *args: Any, **kwargs: Any) -> ModuleType:
        return _mod
