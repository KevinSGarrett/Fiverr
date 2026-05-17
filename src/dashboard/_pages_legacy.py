"""Dashboard page payload registry integration for product pages."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.dashboard.keywords import build_keywords_payload
from src.dashboard.opportunities import build_opportunities_payload
from src.dashboard.run_history import build_run_history_payload

PagePayloadBuilder = Callable[..., dict[str, Any]]


def get_dashboard_page_payload_builders() -> dict[str, PagePayloadBuilder]:
    """Return payload builders for product dashboard pages."""
    return {
        "opportunities": build_opportunities_payload,
        "keywords": build_keywords_payload,
        "run_history": build_run_history_payload,
    }


def build_registered_page_payloads(
    *,
    opportunities_records: list[dict[str, Any]] | None = None,
    keywords_records: list[dict[str, Any]] | None = None,
    run_history_records: list[dict[str, Any]] | None = None,
    opportunities_filters: dict[str, Any] | None = None,
    keywords_filters: dict[str, Any] | None = None,
    run_history_filters: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build payloads for all registered product pages using deterministic defaults."""
    builders = get_dashboard_page_payload_builders()
    payloads = {
        "opportunities": builders["opportunities"](
            records=opportunities_records,
            filters=opportunities_filters,
        ),
        "keywords": builders["keywords"](
            records=keywords_records,
            filters=keywords_filters,
        ),
        "run_history": builders["run_history"](
            records=run_history_records,
            filters=run_history_filters,
        ),
    }
    for page_id, payload in payloads.items():
        payload["payload_support"] = {
            "implemented": True,
            "query_contract": page_id,
            "ui_runtime_ready": False,
            "ui_gap": "Payload contracts are implemented; Streamlit page rendering remains pending.",
        }
    return payloads

