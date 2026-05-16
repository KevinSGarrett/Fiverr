"""Public query-layer boundary for dashboard data access contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.dashboard import queries
from src.dashboard.contracts import (
    FilterDescriptor,
    FreshnessMetadata,
    QueryResult,
    SortDescriptor,
    SourceContext,
)


@dataclass(slots=True)
class DashboardQueryLayer:
    """Composable query layer used by dashboard pages and tests."""

    default_source: SourceContext = SourceContext(source_name="fixture", source_type="in_memory")

    def opportunities(
        self,
        *,
        records: list[dict[str, Any]] | None,
        filters: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
        limit: int = queries.DEFAULT_LIMIT,
        offset: int = 0,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query opportunities with deterministic sparse-data handling."""
        return queries.query_opportunities(
            records=records,
            filters=filters,
            sort=sort,
            limit=limit,
            offset=offset,
            source_context=self.default_source,
            freshness=freshness,
        )

    def keywords(
        self,
        *,
        records: list[dict[str, Any]] | None,
        filters: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
        limit: int = queries.DEFAULT_LIMIT,
        offset: int = 0,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query keyword clusters with reusable filter/sort contracts."""
        return queries.query_keywords(
            records=records,
            filters=filters,
            sort=sort,
            limit=limit,
            offset=offset,
            source_context=self.default_source,
            freshness=freshness,
        )

    def run_history(
        self,
        *,
        records: list[dict[str, Any]] | None,
        filters: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
        limit: int = queries.DEFAULT_LIMIT,
        offset: int = 0,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query run history records with pagination metadata."""
        return queries.query_run_history(
            records=records,
            filters=filters,
            sort=sort,
            limit=limit,
            offset=offset,
            source_context=self.default_source,
            freshness=freshness,
        )

    def app_readiness(
        self,
        *,
        page_registry: list[dict[str, Any]] | None,
        startup_diagnostics: dict[str, Any] | None,
        orchestrator_handoff: dict[str, Any] | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query dashboard app-readiness diagnostics for the entry page."""
        return queries.query_app_readiness(
            page_registry=page_registry,
            startup_diagnostics=startup_diagnostics,
            orchestrator_handoff=orchestrator_handoff,
            source_context=self.default_source,
        )

    def source_freshness_summary(
        self,
        *,
        source_contexts: list[SourceContext] | None,
        freshness_metadata: list[FreshnessMetadata] | None,
    ) -> QueryResult[dict[str, Any]]:
        """Query source/freshness summary rows for traceability UI."""
        return queries.query_source_freshness_summary(
            source_contexts=source_contexts,
            freshness_metadata=freshness_metadata,
        )

    def alert_summary(
        self,
        *,
        records: list[dict[str, Any]] | None,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query alert-summary diagnostics for dashboard startup and health pages."""
        return queries.query_alert_summary(
            records=records,
            source_context=self.default_source,
            freshness=freshness,
        )

    def export_summary(
        self,
        *,
        records: list[dict[str, Any]] | None,
        filters: dict[str, Any] | None = None,
        sort: dict[str, Any] | None = None,
        limit: int = queries.DEFAULT_LIMIT,
        offset: int = 0,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query export-manifest summaries for dashboard data consumers."""
        return queries.query_export_summary(
            records=records,
            filters=filters,
            sort=sort,
            limit=limit,
            offset=offset,
            source_context=self.default_source,
            freshness=freshness,
        )

    def integration_evidence(
        self,
        *,
        evidence: dict[str, Any] | None,
        freshness: FreshnessMetadata | None = None,
    ) -> QueryResult[dict[str, Any]]:
        """Query integration evidence rollups for app-entry and run-history pages."""
        return queries.query_integration_evidence(
            evidence=evidence,
            source_context=self.default_source,
            freshness=freshness,
        )

    def filter_descriptors(self) -> tuple[FilterDescriptor, ...]:
        """Return reusable filter descriptors for all query consumers."""
        return queries.get_filter_descriptors()

    def sort_descriptors(self) -> tuple[SortDescriptor, ...]:
        """Return reusable sort descriptors for all query consumers."""
        return queries.get_sort_descriptors()


def get_dashboard_query_layer() -> DashboardQueryLayer:
    """Return default dashboard query-layer instance."""
    return DashboardQueryLayer()
