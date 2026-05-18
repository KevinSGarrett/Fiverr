"""Project CLI entrypoint."""

from __future__ import annotations

import click
from src.orchestrator import (
    AVAILABLE_MODES,
    normalize_cli_config_path,
    run_analysis_dry_run,
    run_collection_dry_run,
    run_config_check,
    run_dashboard_stub,
    run_export_stub,
    run_foundation_release_gate,
    run_init_db,
    run_phase2_smoke,
    run_pipeline,
    run_smoke_checks,
)


@click.group()
def cli() -> None:
    """Fiverr research system CLI."""


@cli.command("init-db")
@click.option("--database-url", default=None, help="Database URL (defaults to sqlite:///data/fiverr_research.db).")
def init_db_command(database_url: str | None) -> None:
    """Initialize the database schema."""
    raise SystemExit(run_init_db(database_url=database_url))


@cli.command("config-check")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
def config_check_command(config_path: str) -> None:
    """Validate the config file and print key summary fields."""
    raise SystemExit(run_config_check(config_path=normalize_cli_config_path(config_path)))


@cli.command("smoke")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
def smoke_command(config_path: str) -> None:
    """Run local import/config smoke checks."""
    raise SystemExit(run_smoke_checks(config_path=normalize_cli_config_path(config_path)))


@cli.command("foundation-gate")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option(
    "--database-url",
    default="sqlite:///data/foundation_gate.db",
    show_default=True,
    help="Database URL used for release-gate table checks.",
)
def foundation_gate_command(config_path: str, database_url: str) -> None:
    """Run deterministic local Foundation release gate checks."""
    raise SystemExit(
        run_foundation_release_gate(
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("export")
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["csv", "excel", "pdf", "markdown"], case_sensitive=False),
    required=True,
    help="Requested export format.",
)
@click.option("--input-path", required=True, help="Path to the local data input payload.")
def export_command(export_format: str, input_path: str) -> None:
    """Validate export command surface for future Epic 09 implementation."""
    raise SystemExit(run_export_stub(export_format=export_format.lower(), input_path=input_path))


@cli.command("dashboard")
@click.option(
    "--mode",
    type=click.Choice(["local", "preview"], case_sensitive=False),
    default="local",
    show_default=True,
    help="Dashboard mode placeholder.",
)
def dashboard_command(mode: str) -> None:
    """Validate dashboard CLI surface without starting Streamlit."""
    raise SystemExit(run_dashboard_stub(mode=mode))


@cli.command("run")
@click.option(
    "--mode",
    type=click.Choice(AVAILABLE_MODES, case_sensitive=False),
    default="full",
    show_default=True,
    help="Execution mode.",
)
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def run_command(mode: str, config_path: str, database_url: str | None) -> None:
    """Run foundation-stage orchestrator entrypoint with mode routing."""
    raise SystemExit(
        run_pipeline(
            mode=mode,
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("collection-dry-run")
@click.option("--fixture-path", required=True, help="JSON fixture path for collection dry-run inputs.")
@click.option(
    "--output-path",
    default="artifacts/collection/queue_checkpoint.json",
    show_default=True,
    help="Output checkpoint path.",
)
@click.option("--sample-size", default=25, show_default=True, type=int, help="Max fixture records to use.")
def collection_dry_run_command(fixture_path: str, output_path: str, sample_size: int) -> None:
    """Run local collection dry-run from fixture payload."""
    raise SystemExit(
        run_collection_dry_run(
            fixture_path=normalize_cli_config_path(fixture_path),
            output_path=normalize_cli_config_path(output_path),
            sample_size=sample_size,
        )
    )


@cli.command("analysis-dry-run")
@click.option("--fixture-path", required=True, help="JSON fixture path for analysis dry-run inputs.")
@click.option(
    "--output-path",
    default="artifacts/analysis/analysis_dry_run_output.json",
    show_default=True,
    help="Output summary JSON path.",
)
@click.option("--sample-size", default=25, show_default=True, type=int, help="Max fixture records to use.")
@click.option(
    "--database-url",
    default=None,
    help="Optional database URL to persist analysis run and stage outputs.",
)
def analysis_dry_run_command(
    fixture_path: str,
    output_path: str,
    sample_size: int,
    database_url: str | None,
) -> None:
    """Run local analysis dry-run from fixture payload."""
    raise SystemExit(
        run_analysis_dry_run(
            fixture_path=normalize_cli_config_path(fixture_path),
            output_path=normalize_cli_config_path(output_path),
            sample_size=sample_size,
            database_url=database_url,
        )
    )


@cli.command("phase2-smoke")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
def phase2_smoke_command(config_path: str) -> None:
    """Run import/config smoke checks for Phase 2 collection+analysis surfaces."""
    raise SystemExit(run_phase2_smoke(config_path=normalize_cli_config_path(config_path)))


@cli.command("recommendations-only")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def recommendations_only_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 13 recommendation orchestration only."""
    raise SystemExit(
        run_pipeline(
            mode="recommendations-only",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("price-analysis")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def price_analysis_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 10.5 pricing orchestration only."""
    raise SystemExit(
        run_pipeline(
            mode="price-analysis",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


if __name__ == "__main__":
    cli()
