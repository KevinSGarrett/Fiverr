"""Project CLI entrypoint."""

from __future__ import annotations

import asyncio
import json
import math
import os
import sqlite3
from pathlib import Path
from typing import Any

import click
from sqlalchemy import select
from src.collection.session_manager import SessionManager, validate_session_file
from src.config import ConfigLoader
from src.models import Recommendation
from src.models.database import (
    create_session_factory,
    get_session,
    initialize_database,
    normalize_database_url,
)
from src.models.price_analysis import PriceAnalysis
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
from src.pricing.pricing_export import export_all_pricing
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


def _parse_relevance_toggle(config_overrides: tuple[str, ...]) -> bool | None:
    """Return explicit relevance.enable_stage_3_5 override, if present."""
    target_key = "relevance.enable_stage_3_5"
    selected: bool | None = None
    for override in config_overrides:
        if "=" not in override:
            continue
        key, raw_value = override.split("=", 1)
        if key.strip() != target_key:
            continue
        value = raw_value.strip().lower()
        if value in {"true", "1", "yes", "on"}:
            selected = True
        elif value in {"false", "0", "no", "off"}:
            selected = False
    return selected


def _load_latest_keyword_scores(db_path: Path) -> dict[int, dict[str, Any]]:
    """Load latest keyword score row per keyword_id from sqlite db."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        column_rows = conn.execute("PRAGMA table_info(keyword_scores)").fetchall()
        columns = {str(row[1]) for row in column_rows}
        tag_column = "recommendation_tag" if "recommendation_tag" in columns else "tag"
        rows = conn.execute(
            f"""
            SELECT ks.keyword_id,
                   ks.final_score,
                   ks.confidence_modifier,
                   ks.{tag_column} AS recommendation_tag
            FROM keyword_scores ks
            INNER JOIN (
                SELECT keyword_id, MAX(id) AS max_id
                FROM keyword_scores
                GROUP BY keyword_id
            ) latest ON latest.keyword_id = ks.keyword_id AND latest.max_id = ks.id
            """
        ).fetchall()
    return {
        int(row["keyword_id"]): {
            "final_score": float(row["final_score"]) if row["final_score"] is not None else None,
            "confidence_modifier": float(row["confidence_modifier"]) if row["confidence_modifier"] is not None else None,
            "tag": str(row["recommendation_tag"]) if row["recommendation_tag"] is not None else "",
        }
        for row in rows
    }


def _assert_anchor_present(scores: dict[int, dict[str, Any]], keyword_id: int) -> dict[str, Any]:
    payload = scores.get(keyword_id)
    if payload is None:
        raise click.ClickException(f"Missing anchor keyword_id={keyword_id} in score dataset")
    return payload


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


@cli.command("seed-niches")
@click.option("--database-url", default=None, help="Target database URL (or use DATABASE_URL env var).")
def seed_niches_command(database_url: str | None) -> None:
    """Seed niche rows from config.yaml into the target database."""
    from src.models.niche import Niche

    resolved_database_url = database_url or os.environ.get("DATABASE_URL")
    if not resolved_database_url:
        raise click.ClickException("Missing --database-url and DATABASE_URL env var.")

    config_payload = _load_recommendation_config()
    raw_niches = config_payload.get("niches", [])
    if not isinstance(raw_niches, list):
        raise click.ClickException("Config niches payload must be a list.")

    normalized_url = normalize_database_url(resolved_database_url)
    engine = initialize_database(database_url=normalized_url)
    session_factory = create_session_factory(engine)

    added = 0
    with get_session(session_factory) as db:
        for niche_item in raw_niches:
            if not isinstance(niche_item, dict):
                continue
            niche_slug = str(niche_item.get("niche_id", "")).strip()
            if not niche_slug:
                continue
            existing = db.query(Niche).filter(Niche.slug == niche_slug).first()
            if existing is not None:
                continue
            db.add(
                Niche(
                    slug=niche_slug,
                    name=str(niche_item.get("name", niche_slug.replace("_", " ").title())),
                    category_path=str(niche_item.get("category_path", "uncategorized")),
                    is_active=bool(niche_item.get("is_active", True)),
                    description=None,
                )
            )
            added += 1
        db.commit()
        total = int(db.query(Niche).count())

    click.echo(f"niches seeded: {total} ({added} new)")


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


@cli.command("pricing-export")
@click.option("--output-dir", default="exports/pricing", show_default=True, help="Output directory for pricing exports.")
@click.option("--database-url", default=None, help="Database URL override.")
def pricing_export_command(output_dir: str, database_url: str | None) -> None:
    """Export pricing snapshots for all keyword ids with pricing analyses."""
    with _recommendation_db_session(database_url) as db:
        keyword_ids = [row[0] for row in db.execute(select(PriceAnalysis.keyword_id).distinct()).fetchall()]
        if not keyword_ids:
            click.echo("No pricing rows found; nothing exported.")
            raise SystemExit(0)
        results = export_all_pricing(keyword_ids, db, output_dir)
    click.echo(f"Exported {len(results)} files to {output_dir}")


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
    """Export a recommendation as Markdown or JSON for a given keyword ID."""

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


@cli.command("discover")
@click.option("--run-id", default=None, help="Discovery run ID (generated if not provided).")
@click.option("--config-path", default="config.yaml", show_default=True, help="Config file path.")
@click.option("--database-url", default=None, help="Database URL override.")
def discover_command(run_id: str | None, config_path: str, database_url: str | None) -> None:
    """Run Stage 16 discovery cycle orchestration."""
    dry_run_sentinel = os.getenv("DRY_RUN_SENTINEL")
    if dry_run_sentinel:
        click.echo(f"DRY_RUN_SENTINEL set ({dry_run_sentinel}); skipping discovery writes.")
        raise SystemExit(0)

    from src.discovery.stage16 import run_discovery_cycle

    config_payload = _load_recommendation_config(config_path=config_path)
    with _recommendation_db_session(database_url) as db:
        cycle_log = run_discovery_cycle(
            db=db,
            run_id=run_id,
            config=config_payload,
        )
    click.echo(f"Discovery complete: {cycle_log.hypotheses_accepted} keywords inserted")


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


@cli.command("score")
@click.option("--golden", is_flag=True, default=False, help="Run golden parity check helper.")
@click.option(
    "--config-override",
    "config_overrides",
    multiple=True,
    help="Config override key=value pair (supports relevance.enable_stage_3_5).",
)
def score_command(golden: bool, config_overrides: tuple[str, ...]) -> None:
    """Run score parity helper for Cycle 053 gate replay."""
    if not golden:
        raise click.ClickException("Only --golden mode is supported for this command")

    toggle = _parse_relevance_toggle(config_overrides)
    if toggle is None:
        raise click.ClickException(
            "Missing relevance.enable_stage_3_5 override. "
            "Example: --config-override relevance.enable_stage_3_5=false"
        )

    workspace_root = Path(__file__).resolve().parent
    baseline_db = workspace_root / "data" / "cycle037_live.db"
    target_db = workspace_root / "data" / ("parity_on.db" if toggle else "parity_off.db")

    if not baseline_db.exists():
        raise click.ClickException(f"Baseline DB not found: {baseline_db}")
    if not target_db.exists():
        raise click.ClickException(f"Target parity DB not found: {target_db}")

    baseline_scores = _load_latest_keyword_scores(baseline_db)
    target_scores = _load_latest_keyword_scores(target_db)
    if not baseline_scores:
        raise click.ClickException("Baseline DB contains no keyword_scores rows")
    if not target_scores:
        raise click.ClickException("Target parity DB contains no keyword_scores rows")

    anchors = [110, 96, 3]
    baseline_anchor_rows = {kw: _assert_anchor_present(baseline_scores, kw) for kw in anchors}
    target_anchor_rows = {kw: _assert_anchor_present(target_scores, kw) for kw in anchors}

    if not toggle:
        shared_keywords = sorted(set(baseline_scores).intersection(target_scores))
        mismatches: list[int] = []
        for keyword_id in shared_keywords:
            baseline_row = baseline_scores[keyword_id]
            target_row = target_scores[keyword_id]
            if (
                baseline_row["final_score"] != target_row["final_score"]
                or baseline_row["confidence_modifier"] != target_row["confidence_modifier"]
                or baseline_row["tag"] != target_row["tag"]
            ):
                mismatches.append(keyword_id)
        if mismatches:
            preview = ", ".join(str(k) for k in mismatches[:10])
            raise click.ClickException(
                f"Golden parity OFF mismatch vs baseline for {len(mismatches)} keyword(s): {preview}"
            )

    kw110 = target_anchor_rows[110]
    if toggle:
        kw110_score = kw110["final_score"]
        kw110_cm = kw110["confidence_modifier"]
        kw110_tag = str(kw110["tag"]).upper().replace(" ", "_")
        if kw110_score is None or kw110_score < 60.0:
            raise click.ClickException(f"kw=110 final score gate failed: {kw110_score}")
        if kw110_cm is None or not math.isclose(kw110_cm, 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise click.ClickException(f"kw=110 confidence modifier gate failed: {kw110_cm}")
        if kw110_tag != "CONDITIONAL_GO":
            raise click.ClickException(f"kw=110 tag gate failed: {kw110['tag']}")

        for keyword_id in anchors:
            base_score = baseline_anchor_rows[keyword_id]["final_score"]
            tgt_score = target_anchor_rows[keyword_id]["final_score"]
            if base_score is None or tgt_score is None:
                raise click.ClickException(f"Missing score for anchor kw={keyword_id}")
            drift = abs(tgt_score - base_score)
            if drift > 2.0:
                raise click.ClickException(f"Anchor drift >2 for kw={keyword_id}: {drift:.2f}")

    click.echo(
        json.dumps(
            {
                "mode": "golden",
                "enable_stage_3_5": toggle,
                "baseline_db": str(baseline_db),
                "target_db": str(target_db),
                "anchor_rows": {str(k): target_anchor_rows[k] for k in anchors},
                "status": "PASS",
            },
            indent=2,
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


@cli.command("collect-live")
@click.option(
    "--niche",
    "niche_id",
    required=True,
    help="Niche ID for live collection. ONE niche only (TierD-2 condition A).",
)
@click.option(
    "--budget",
    "budget_credits",
    default=500,
    show_default=True,
    type=int,
    help="ScrapFly credit ceiling. Pilot stops automatically when reached.",
)
@click.option("--database-url", default=None, help="Pilot DB URL. Default: sqlite:///data/live_pilot_{niche}.db")
@click.option("--config-path", default="config.yaml", show_default=True)
@click.option(
    "--log-path",
    default="data/live_pilot_log.jsonl",
    show_default=True,
    help="JSONL file for per-request ScrapFly logging (TierD-2 condition C).",
)
@click.option("--evidence-path", default="data/live_validation_evidence.json", show_default=True)
def collect_live_command(
    niche_id: str,
    budget_credits: int,
    database_url: str | None,
    config_path: str,
    log_path: str,
    evidence_path: str,
) -> None:
    """
    Run CONTROLLED live collection for ONE niche using ScrapFly.

    TierD-2 conditions:
    - one niche only
    - hard credit ceiling
    - per-request JSONL logging
    - evidence bundle written on success/failure
    """
    from src.collection.live_pilot import run_live_collection_pilot

    click.echo(f"Starting live collection pilot: niche={niche_id} budget={budget_credits} credits")
    click.echo("Prerequisites: SCRAPFLY_API_KEY set + valid session (run relogin if needed)")
    result = asyncio.run(
        run_live_collection_pilot(
            niche_id=niche_id,
            budget_credits=budget_credits,
            database_url=database_url,
            config_path=normalize_cli_config_path(config_path),
            log_path=log_path,
            evidence_path=evidence_path,
        )
    )
    if result.get("stop_reason"):
        click.echo(f"Pilot stopped: {result['stop_reason']}", err=True)
    click.echo(
        f"success={result['success']} "
        f"credits={result['credits_used']}/{budget_credits} "
        f"gigs={result['gigs_collected']} "
        f"searches={result['search_results']}"
    )
    if result.get("errors"):
        for err in result["errors"][:3]:
            click.echo(f"  error: {err}", err=True)
    click.echo(f"Evidence: {result.get('evidence_path', evidence_path)}")
    raise SystemExit(0 if result["success"] else 1)


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
@click.option(
    "--live",
    "live_mode",
    is_flag=True,
    default=False,
    help=(
        "Pass dry_run=False for real LLM recommendations. "
        "Requires OPENAI_API_KEY. Falls back to dry_run=True if key missing."
    ),
)
def recommendations_only_command(config_path: str, database_url: str | None, live_mode: bool) -> None:
    """Run recommendation pipeline. Use --live for real LLM recommendations."""
    from src.recommendations.pipeline import run_recommendations_pipeline
    from src.utils.datetime import timestamp_stamp

    config_payload = _load_recommendation_config(config_path)
    run_id = timestamp_stamp()
    llm_client = None
    actual_live = live_mode
    if live_mode:
        try:
            from src.llm.client import build_llm_client

            llm_client = build_llm_client(config_payload)
            if llm_client is None:
                actual_live = False
                click.echo("Note: OPENAI_API_KEY not set, running dry_run=True", err=True)
        except (ImportError, Exception) as exc:  # noqa: BLE001
            actual_live = False
            click.echo(f"Note: LLM client unavailable ({exc}), running dry_run=True", err=True)

    with _recommendation_db_session(database_url) as db:
        result = asyncio.run(
            run_recommendations_pipeline(
                run_id=run_id,
                db=db,
                config=config_payload,
                llm_client=llm_client,
                cache=None,
                dry_run=(not actual_live),
            )
        )
    mode_label = "live" if actual_live else "dry-run"
    click.echo(f"Recommendations ({mode_label}): {result}")
    raise SystemExit(0)


@cli.command("live-validate")
@click.option("--niche", "niche_id", default="python_automation", show_default=True)
@click.option("--budget", "budget_credits", default=500, type=int)
@click.option("--database-url", default=None)
@click.option("--config-path", default="config.yaml", show_default=True)
@click.option(
    "--skip-collection",
    is_flag=True,
    default=False,
    help="Skip collection if already run for this niche and DB exists.",
)
@click.option("--evidence-path", default="data/live_validation_evidence.json", show_default=True)
def live_validate_command(
    niche_id: str,
    budget_credits: int,
    database_url: str | None,
    config_path: str,
    skip_collection: bool,
    evidence_path: str,
) -> None:
    """
    Full end-to-end live validation pipeline (TierD-2 controlled pilot).

    Stages:
      1) preflight 2) collection 3) db validation 4) scoring
      5) recommendations 6) export 7) playbook 8) evidence
    """
    resolved_db = database_url or f"sqlite:///data/live_pilot_{niche_id}.db"
    evidence: dict[str, Any] = {
        "niche_id": niche_id,
        "db_url": resolved_db,
        "stages": {},
        "success": False,
    }

    # Stage 1: Pre-flight
    scrapfly_key = os.getenv("SCRAPFLY_API_KEY")
    evidence["stages"]["preflight"] = {"scrapfly_key_present": bool(scrapfly_key)}
    if not scrapfly_key and not skip_collection:
        click.echo("ERROR: SCRAPFLY_API_KEY not set. Cannot collect live data.", err=True)
        raise SystemExit(1)

    # Stage 2: Collection
    if not skip_collection:
        click.echo(f"Stage 2: Live collection (niche={niche_id} budget={budget_credits})")
        from src.collection.live_pilot import run_live_collection_pilot

        collect_result = asyncio.run(
            run_live_collection_pilot(
                niche_id=niche_id,
                budget_credits=budget_credits,
                database_url=resolved_db,
                config_path=normalize_cli_config_path(config_path),
            )
        )
        evidence["stages"]["collection"] = collect_result
        click.echo(
            f"  Collected: gigs={collect_result.get('gigs_collected', 0)} "
            f"credits={collect_result.get('credits_used', 0)}"
        )
        if not collect_result.get("success", False):
            click.echo(f"  Collection failed: {collect_result.get('stop_reason')}", err=True)
    else:
        click.echo("Stage 2: Skipped (--skip-collection)")

    # Stage 3: DB validation
    click.echo("Stage 3: DB persistence validation")
    db_validation = _validate_pilot_db_state(resolved_db)
    evidence["stages"]["db_validation"] = db_validation
    click.echo(
        f"  gigs={db_validation.get('gigs', 0)} "
        f"keywords={db_validation.get('keywords', 0)} "
        f"search_results={db_validation.get('search_results', 0)}"
    )

    # Stage 4: Scoring
    click.echo("Stage 4: Scoring live keywords")
    try:
        run_pipeline(
            mode="full",
            config_path=normalize_cli_config_path(config_path),
            database_url=resolved_db,
        )
        evidence["stages"]["scoring"] = {"success": True}
    except Exception as exc:  # noqa: BLE001
        evidence["stages"]["scoring"] = {"success": False, "error": str(exc)}
        click.echo(f"  Scoring error: {exc}", err=True)

    # Stage 5: Recommendations
    click.echo("Stage 5: Live recommendations")
    recs = _run_live_recommendations(normalize_cli_config_path(config_path), resolved_db)
    evidence["stages"]["recommendations"] = recs
    click.echo(f"  dry_run={recs.get('dry_run', True)}")

    # Stage 6: Export
    export_dir = Path("data/exports/live_pilot")
    export_dir.mkdir(parents=True, exist_ok=True)
    evidence["stages"]["export"] = {"dir": str(export_dir), "files": len(list(export_dir.glob("*")))}

    # Stage 7: Playbook
    click.echo("Stage 7: Playbook from live recommendation")
    playbook_result = _generate_playbook_from_live_data(niche_id, resolved_db)
    evidence["stages"]["playbook"] = playbook_result
    click.echo(
        f"  has_full_data={playbook_result.get('has_full_data')} "
        f"sections={playbook_result.get('sections_count')}"
    )

    # Stage 8: Evidence
    evidence["success"] = (
        evidence["stages"].get("db_validation", {}).get("gigs", 0) > 0
        and evidence["stages"].get("scoring", {}).get("success", False)
    )
    evidence_file = Path(evidence_path)
    evidence_file.parent.mkdir(parents=True, exist_ok=True)
    evidence_file.write_text(json.dumps(evidence, indent=2, default=str), encoding="utf-8")
    click.echo(f"Evidence bundle: {evidence_path}")
    click.echo(f"Validation {'PASSED' if evidence['success'] else 'PARTIAL'}: {evidence['success']}")
    raise SystemExit(0)


def _validate_pilot_db_state(db_url: str) -> dict[str, Any]:
    """Count persisted entities from pilot DB without raising."""
    from src.models.gig import Gig
    from src.models.market import Keyword
    from src.models.search_result import SearchResult

    try:
        engine = initialize_database(database_url=normalize_database_url(db_url))
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db:
            return {
                "gigs": int(db.query(Gig).count()),
                "keywords": int(db.query(Keyword).count()),
                "search_results": int(db.query(SearchResult).count()),
            }
    except Exception as exc:  # noqa: BLE001
        return {"gigs": 0, "keywords": 0, "search_results": 0, "error": str(exc)}


def _run_live_recommendations(config_path: str, database_url: str) -> dict[str, Any]:
    """Run recommendation pipeline with live fallback logic."""
    from src.recommendations.pipeline import run_recommendations_pipeline
    from src.utils.datetime import timestamp_stamp

    config_payload = _load_recommendation_config(config_path)
    live_mode = bool(os.getenv("OPENAI_API_KEY"))
    try:
        llm_client = None
        if live_mode:
            try:
                from src.llm.client import build_llm_client

                llm_client = build_llm_client(config_payload)
                if llm_client is None:
                    live_mode = False
            except Exception:  # noqa: BLE001
                live_mode = False
        with _recommendation_db_session(database_url) as db:
            result = asyncio.run(
                run_recommendations_pipeline(
                    run_id=timestamp_stamp(),
                    db=db,
                    config=config_payload,
                    llm_client=llm_client,
                    cache=None,
                    dry_run=(not live_mode),
                )
            )
        count = int(result.get("generated", 0)) if isinstance(result, dict) else 0
        return {"success": True, "count": count, "dry_run": not live_mode, "result": str(result)}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc), "count": 0, "dry_run": True}


def _generate_playbook_from_live_data(niche_id: str, database_url: str) -> dict[str, Any]:
    """Generate playbook summary from best available live recommendation data."""
    try:
        from src.playbook.generator import export_playbook_markdown, generate_playbook

        engine = initialize_database(database_url=normalize_database_url(database_url))
        session_factory = create_session_factory(engine)
        config_payload = _load_recommendation_config()
        with get_session(session_factory) as db:
            playbook = generate_playbook(niche_id, db, config_payload)
        markdown = export_playbook_markdown(playbook)
        return {
            "success": True,
            "niche_id": niche_id,
            "has_full_data": playbook.get("has_full_data", False),
            "sections_count": len(playbook.get("sections", [])),
            "keyword_used": playbook.get("keyword_used"),
            "markdown_length": len(markdown),
        }
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "has_full_data": False, "sections_count": 0, "error": str(exc)}


@cli.command("playbook")
@click.argument("niche_id")
@click.option("--format", "fmt", type=click.Choice(["markdown", "pdf"]), default="markdown", show_default=True)
@click.option("--output", default=None, help="Output path (pdf only)")
@click.option("--database-url", default=None)
def playbook_command(niche_id: str, fmt: str, output: str | None, database_url: str | None) -> None:
    """Generate seller setup playbook for a niche."""
    from src.playbook.generator import export_playbook_markdown, export_playbook_pdf, generate_playbook

    config_payload = _load_recommendation_config()
    with _recommendation_db_session(database_url) as db:
        playbook = generate_playbook(niche_id, db, config_payload)
    if fmt == "pdf":
        out = output or f"data/exports/pdf/playbook_{niche_id}.pdf"
        export_playbook_pdf(playbook, out)
        click.echo(f"PDF: {out}")
    else:
        click.echo(export_playbook_markdown(playbook))
    raise SystemExit(0)


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
    """Check if the saved Fiverr session file exists and remains valid."""
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
        raise SystemExit(1)
    if not valid_json:
        click.echo("ERROR: Session file is invalid JSON. Run: python run.py relogin")
        raise SystemExit(1)
    if not (has_cookies or has_origins):
        click.echo("ERROR: Session file has no auth payload. Run: python run.py relogin")
        raise SystemExit(1)

    async def _verify_saved_session() -> bool:
        session_manager = SessionManager(config)
        try:
            return await session_manager.is_session_valid()
        finally:
            await session_manager.close()

    if asyncio.run(_verify_saved_session()):
        click.echo("Session is VALID. Ready for collection.")
        raise SystemExit(0)

    click.echo("Session is EXPIRED. Run: python run.py relogin")
    raise SystemExit(1)


if __name__ == "__main__":
    cli()
