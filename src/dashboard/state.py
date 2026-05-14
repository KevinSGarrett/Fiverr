"""State container for dashboard shell interactions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class DashboardState:
    """Serializable state holder for dashboard shell defaults."""

    selected_page: str = "overview"
    filters: dict[str, Any] = field(default_factory=dict)
    active_run_id: str | None = None


def _build_metric_rows(
    metric_order: tuple[str, ...],
    provided_metrics: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    """Build metric rows where missing values are explicit pending placeholders."""
    provided_metrics = provided_metrics or {}
    rows: list[dict[str, Any]] = []
    for metric_name in metric_order:
        value = provided_metrics.get(metric_name)
        rows.append(
            {
                "name": metric_name,
                "value": value if value is not None else "pending",
                "status": "ready" if value is not None else "pending",
            }
        )
    return rows


def build_cycle003_status_state(
    foundation_metrics: Mapping[str, Any] | None = None,
    collection_metrics: Mapping[str, Any] | None = None,
    analysis_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return plain dashboard state sections for Cycle 003 status rendering."""
    sections = [
        {
            "section_id": "foundation",
            "label": "Foundation",
            "stage": "foundation",
            "metrics": _build_metric_rows(
                ("config_check", "init_db", "foundation_gate"),
                foundation_metrics,
            ),
        },
        {
            "section_id": "collection_dry_run",
            "label": "Collection Dry Run",
            "stage": "collection",
            "metrics": _build_metric_rows(
                ("query_set_ready", "sample_capture", "capture_validation"),
                collection_metrics,
            ),
        },
        {
            "section_id": "analysis_dry_run",
            "label": "Analysis Dry Run",
            "stage": "analysis",
            "metrics": _build_metric_rows(
                ("scoring_ready", "ranking_ready", "report_preview"),
                analysis_metrics,
            ),
        },
    ]
    return {"cycle": "003", "sections": sections}
