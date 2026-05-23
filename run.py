"""Project CLI entrypoint."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import click
from src.collection.session_manager import SessionManager, validate_session_file
from src.config import ConfigLoader
from src.models import Recommendation
from src.models.database import (
    create_session_factory,
    get_session,
    initialize_database,
    normalize_database_url,
)
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
from src.recommendations.export import (
    export_all_recommendations,
    export_recommendation_by_keyword,
    export_recommendation_json_by_keyword,
)


@click.group()
def cli() -> None:
    """Fiverr research system CLI."""


def _load_recommendation_config(config_path: str = "config.yaml") -> dict[str, Any]:
    config = ConfigLoader(normalize_cli_config_path(config_path)).load()
    if hasattr(config, "model_dump"):
        payload = config.model_dump()
        if isinstance(payload, dict):
            return payload
    return {}


def _recommendation_db_session(database_url: str | None = None) -> Any:
    normalized_url = normalize_database_url(database_url)
    engine = initialize_database(database_url=normalized_url)
    session_factory = create_session_factory(engine)
    return get_session(session_factory)


def _resolve_latest_recommendation_run_id(db: Any) -> str | None:
    query_fn = getattr(db, "query", None)
    if query_fn is None:
        return None

    try:
        row = (
            query_fn(Recommendation)
            .filter(Recommendation.generation_complete.is_(True))
            .order_by(Recommendation.created_at.desc())
            .first()
        )
    except Exception:
        return None
    if row is None:
        return None

    run_id_text = getattr(row, "run_id_text", None)
    if isinstance(run_id_text, str) and run_id_text.strip():
        return run_id_text.strip()

    run_id = getattr(row, "run_id", None)
    if run_id is not None:
        return str(run_id)
    return None


def _safe_export_filename(keyword_text: str) -> str:
    filtered = [
        character.lower()
        if character.isalnum()
        else "_"
        for character in keyword_text.strip()
    ]
    safe_name = "".join(filtered).strip("_")
    while "__" in safe_name:
        safe_name = safe_name.replace("__", "_")
    return safe_name or "keyword"


def _recommendation_summary_counts(db: Any) -> dict[str, int]:
    query = db.query(Recommendation)
    total = int(query.count())
    complete = int(query.filter(Recommendation.generation_complete.is_(True)).count())
    strong_go = int(query.filter(Recommendation.tag == "STRONG GO").count()) + int(
        query.filter(Recommendation.tag == "STRONG_GO").count()
    )
    conditional_go = int(query.filter(Recommendation.tag == "CONDITIONAL GO").count()) + int(
        query.filter(Recommendation.tag == "CONDITIONAL_GO").count()
    )
    return {
        "strong_go": strong_go,
        "conditional_go": conditional_go,
        "total": total,
        "complete": complete,
        "incomplete": max(total - complete, 0),
    }


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


@cli.command("export-recommendation")
@click.option("--keyword-id", type=int, required=True, help="Keyword ID to export.")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Export format.",
)
@click.option("--output", default=None, help="Output file path (default: stdout).")
def export_recommendation_command(keyword_id: int, fmt: str, output: str | None) -> None:
    """Export a recommendation as Markdown for a given keyword ID."""

    async def _run() -> int:
        format_name = fmt.strip().lower()
        with _recommendation_db_session() as db:
            if format_name == "markdown":
                content, error = await export_recommendation_by_keyword(
                    keyword_id=keyword_id,
                    niche_id="",
                    run_id="",
                    db=db,
                )
                if error is not None:
                    click.echo(f"ERROR: {error}", err=True)
                    return 1
                result = content
            else:
                payload, error = await export_recommendation_json_by_keyword(
                    keyword_id=keyword_id,
                    niche_id="",
                    run_id="",
                    db=db,
                )
                if error is not None:
                    click.echo(f"ERROR: {error}", err=True)
                    return 1
                result = json.dumps(payload, indent=2)

        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result, encoding="utf-8")
            click.echo(f"Exported to {output_path}")
            return 0

        click.echo(result)
        return 0

    raise SystemExit(asyncio.run(_run()))


@cli.command("export-all-recommendations")
@click.option("--run-id", required=False, default=None, help="Run ID to export (defaults to latest recommendation run).")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Export format.",
)
@click.option("--output-dir", default="data/exports", show_default=True, help="Directory for output files.")
def export_all_recommendations_command(run_id: str | None, fmt: str, output_dir: str) -> None:
    """Export all complete recommendations for one run."""

    async def _run() -> int:
        config_payload = _load_recommendation_config()
        format_name = fmt.strip().lower()
        with _recommendation_db_session() as db:
            resolved_run_id = run_id.strip() if isinstance(run_id, str) and run_id.strip() else None
            if resolved_run_id is None:
                resolved_run_id = _resolve_latest_recommendation_run_id(db)
            if resolved_run_id is None:
                click.echo("ERROR: no completed recommendation run found.", err=True)
                return 1

            exported = await export_all_recommendations(
                run_id=resolved_run_id,
                fmt=format_name,
                db=db,
                config=config_payload,
            )

        export_dir = Path(output_dir)
        export_dir.mkdir(parents=True, exist_ok=True)
        extension = ".md" if format_name == "markdown" else ".json"
        written_count = 0
        for keyword_text, payload in exported.items():
            filename = f"{_safe_export_filename(keyword_text)}{extension}"
            target_path = export_dir / filename
            if format_name == "markdown":
                content = str(payload)
            else:
                content = json.dumps(payload, indent=2)
            target_path.write_text(content, encoding="utf-8")
            written_count += 1

        click.echo(f"Exported {written_count} recommendation(s) to {export_dir}")
        return 0

    raise SystemExit(asyncio.run(_run()))


@cli.command("recommendations-summary")
def recommendations_summary_command() -> None:
    """Report recommendation totals and completion counts."""

    with _recommendation_db_session() as db:
        counts = _recommendation_summary_counts(db)

    click.echo(
        "STRONG GO: {strong_go}, CONDITIONAL GO: {conditional_go}, total: {total}, complete: {complete}, "
        "incomplete: {incomplete}".format(**counts)
    )


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


@cli.command("collect-only")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def collect_only_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 1-5 dry-run collection orchestration only."""
    raise SystemExit(
        run_pipeline(
            mode="collect-only",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("cluster-only")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def cluster_only_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 9 keyword clustering for all niches."""
    raise SystemExit(
        run_pipeline(
            mode="cluster-only",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("profile-only")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def profile_only_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 10 competitor profiling for all niches."""
    raise SystemExit(
        run_pipeline(
            mode="profile-only",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("quality-analysis")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def quality_analysis_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 11 gig quality rubric analysis for all niches."""
    raise SystemExit(
        run_pipeline(
            mode="quality-analysis",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("review-analysis")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def review_analysis_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 12 review signal analysis for all niches."""
    raise SystemExit(
        run_pipeline(
            mode="review-analysis",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


@cli.command("saturation-analysis")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def saturation_analysis_command(config_path: str, database_url: str | None) -> None:
    """Run Stage 13 saturation model analysis for all niches."""
    raise SystemExit(
        run_pipeline(
            mode="saturation-analysis",
            config_path=normalize_cli_config_path(config_path),
            database_url=database_url,
        )
    )


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


@cli.command("relogin")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
def relogin_command(config_path: str) -> None:
    """Trigger a headed Fiverr login and save session to data/sessions/fiverr_session.json."""

    async def _run() -> None:
        config = ConfigLoader(normalize_cli_config_path(config_path)).load()
        session_manager = SessionManager(config)
        try:
            await session_manager.force_relogin()
        finally:
            await session_manager.close()

    asyncio.run(_run())
    click.echo("Session saved successfully.")


@cli.command("session-check")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
def session_check_command(config_path: str) -> None:
    """Check if the saved Fiverr session is valid without running collection."""

    async def _run() -> int:
        config = ConfigLoader(normalize_cli_config_path(config_path)).load()
        session_file = Path(config.fiverr.session_file)
        validation = validate_session_file(session_file)
        click.echo(f"Session file: {validation['path']}")
        click.echo(
            "Session file health: "
            f"exists={validation['exists']}, "
            f"valid_json={validation['valid_json']}, "
            f"has_cookies={validation['has_cookies']}, "
            f"has_origins={validation['has_origins']}"
        )

        exists = bool(validation["exists"])
        valid_json = bool(validation["valid_json"])
        has_cookies = bool(validation["has_cookies"])
        has_origins = bool(validation["has_origins"])

        if not exists:
            click.echo("ERROR: Session file not found. Run: python run.py relogin")
            return 1
        if not valid_json:
            click.echo("ERROR: Session file is invalid JSON. Run: python run.py relogin")
            return 1
        if not (has_cookies or has_origins):
            click.echo("ERROR: Session file has no auth payload. Run: python run.py relogin")
            return 1

        session_manager = SessionManager(config)
        try:
            valid = await session_manager.is_session_valid()
        finally:
            await session_manager.close()

        if valid:
            click.echo("Session is VALID. Ready for collection.")
            return 0

        click.echo("Session is EXPIRED. Run: python run.py relogin")
        return 1

    raise SystemExit(asyncio.run(_run()))


if __name__ == "__main__":
    cli()
