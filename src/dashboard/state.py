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


@dataclass(frozen=True, slots=True)
class FixtureCoverageState:
    """Coverage metrics for fixture-backed parser and dry-run surfaces."""

    gig_detail_parser: int | str = "pending"
    seller_profile_parser: int | str = "pending"
    collection_fixture_set: int | str = "pending"
    analysis_fixture_set: int | str = "pending"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "gig_detail_parser": self.gig_detail_parser,
            "seller_profile_parser": self.seller_profile_parser,
            "collection_fixture_set": self.collection_fixture_set,
            "analysis_fixture_set": self.analysis_fixture_set,
        }


@dataclass(frozen=True, slots=True)
class DryRunStatusState:
    """Status shape for one dry-run workflow."""

    status: str = "pending"
    run_id: str = "pending"
    sample_size: int | str = "pending"
    last_updated: str = "pending"

    def to_dict(self) -> dict[str, int | str]:
        return {
            "status": self.status,
            "run_id": self.run_id,
            "sample_size": self.sample_size,
            "last_updated": self.last_updated,
        }


@dataclass(frozen=True, slots=True)
class GateStatusState:
    """Foundation/Phase 2 gate readiness status."""

    foundation_gate: str = "pending"
    phase2_smoke: str = "pending"
    validation_bundle: str = "pending"

    def to_dict(self) -> dict[str, str]:
        return {
            "foundation_gate": self.foundation_gate,
            "phase2_smoke": self.phase2_smoke,
            "validation_bundle": self.validation_bundle,
        }


@dataclass(frozen=True, slots=True)
class Phase2ReadinessState:
    """Import-safe structured state for Cycle 004 readiness visibility."""

    cycle: str = "004"
    collection_dry_run: DryRunStatusState = field(default_factory=DryRunStatusState)
    analysis_dry_run: DryRunStatusState = field(default_factory=DryRunStatusState)
    fixture_coverage: FixtureCoverageState = field(default_factory=FixtureCoverageState)
    gate_status: GateStatusState = field(default_factory=GateStatusState)
    pending_blockers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "cycle": self.cycle,
            "collection_dry_run": self.collection_dry_run.to_dict(),
            "analysis_dry_run": self.analysis_dry_run.to_dict(),
            "fixture_coverage": self.fixture_coverage.to_dict(),
            "gate_status": self.gate_status.to_dict(),
            "pending_blockers": list(self.pending_blockers),
        }


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


def _normalize_metric(value: Any) -> Any:
    return value if value is not None else "pending"


def build_phase2_readiness_state(
    collection_metrics: Mapping[str, Any] | None = None,
    analysis_metrics: Mapping[str, Any] | None = None,
    fixture_coverage: Mapping[str, Any] | None = None,
    gate_status: Mapping[str, Any] | None = None,
    pending_blockers: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Build Cycle 004 readiness state with explicit placeholders for missing metrics."""
    collection_metrics = collection_metrics or {}
    analysis_metrics = analysis_metrics or {}
    fixture_coverage = fixture_coverage or {}
    gate_status = gate_status or {}

    readiness = Phase2ReadinessState(
        collection_dry_run=DryRunStatusState(
            status=str(_normalize_metric(collection_metrics.get("status"))),
            run_id=str(_normalize_metric(collection_metrics.get("run_id"))),
            sample_size=_normalize_metric(collection_metrics.get("sample_size")),
            last_updated=str(_normalize_metric(collection_metrics.get("last_updated"))),
        ),
        analysis_dry_run=DryRunStatusState(
            status=str(_normalize_metric(analysis_metrics.get("status"))),
            run_id=str(_normalize_metric(analysis_metrics.get("run_id"))),
            sample_size=_normalize_metric(analysis_metrics.get("sample_size")),
            last_updated=str(_normalize_metric(analysis_metrics.get("last_updated"))),
        ),
        fixture_coverage=FixtureCoverageState(
            gig_detail_parser=_normalize_metric(fixture_coverage.get("gig_detail_parser")),
            seller_profile_parser=_normalize_metric(fixture_coverage.get("seller_profile_parser")),
            collection_fixture_set=_normalize_metric(fixture_coverage.get("collection_fixture_set")),
            analysis_fixture_set=_normalize_metric(fixture_coverage.get("analysis_fixture_set")),
        ),
        gate_status=GateStatusState(
            foundation_gate=str(_normalize_metric(gate_status.get("foundation_gate"))),
            phase2_smoke=str(_normalize_metric(gate_status.get("phase2_smoke"))),
            validation_bundle=str(_normalize_metric(gate_status.get("validation_bundle"))),
        ),
        pending_blockers=pending_blockers,
    )
    return readiness.to_dict()
