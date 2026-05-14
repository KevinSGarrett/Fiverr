"""Project CLI entrypoint."""

from __future__ import annotations

import click
from src.orchestrator import (
    AVAILABLE_MODES,
    normalize_cli_config_path,
    run_config_check,
    run_dashboard_stub,
    run_export_stub,
    run_foundation_release_gate,
    run_init_db,
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
    """Run foundation-stage orchestrator entrypoint."""
    raise SystemExit(
        run_pipeline(
            mode=mode,
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


if __name__ == "__main__":
    cli()
