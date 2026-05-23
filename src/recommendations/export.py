"""Recommendation export stubs for Stage 13 outputs."""

from __future__ import annotations

from typing import Any


async def export_recommendation_markdown(recommendation_id: str, db: Any) -> str:
    """Exports recommendation as formatted Markdown. Stub returns empty string."""
    del recommendation_id, db
    return ""


async def export_recommendation_json(recommendation_id: str, db: Any) -> dict[str, Any]:
    """Exports recommendation as JSON dict. Stub returns {}."""
    del recommendation_id, db
    return {}


__all__ = ["export_recommendation_markdown", "export_recommendation_json"]
