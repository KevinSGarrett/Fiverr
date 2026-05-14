"""Project CLI entrypoint."""

from __future__ import annotations

import click
from src.orchestrator import (
    AVAILABLE_MODES,
    normalize_cli_config_path,
    run_config_check,
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
