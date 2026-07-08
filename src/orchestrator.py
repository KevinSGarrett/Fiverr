"""CLI orchestration helpers for foundation-stage commands."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
from typing import Any

from sqlalchemy.exc import SQLAlchemyError

from src.config import ConfigLoader
from src.models.database import (
    create_session_factory,
    get_session,
    initialize_database,
    normalize_database_url,
)
from src.models.gig import Gig
from src.models.search_result import SearchResult
from src.scripts.foundation_gate import run_foundation_gate
from src.scripts.init_db import main as init_db_script_main
from src.utils.datetime import timestamp_stamp
from src.utils.logging import configure_logging

AVAILABLE_MODES = (
    "full",
    "collect-only",
    "cluster-only",
    "profile-only",
    "quality-analysis",
    "review-analysis",
    "saturation-analysis",
    "score-only",
    "analyze-only",
    "price-analysis",
    "recommendations-only",
    "discovery-only",
    "discovery-collect",
    "resume",
)

STAGE_AVAILABILITY = {
    "full": (
        "Full mode chains collection (Stage 1-13), scoring, pricing, recommendations, "
        "playbook generation, and exports in one run. Live collection auto-detects a "
        "valid saved Fiverr session; ScrapFly spend is further gated by "
        "collection.scrapfly.enabled in config."
    ),
    "collect-only": "Runs Stage 1-13 collection plus its built-in analysis stages only.",
    "cluster-only": "Cluster-only mode runs Stage 9 keyword clustering for active niches.",
    "profile-only": "Profile-only mode runs Stage 10 competitor profiling for active niches.",
    "quality-analysis": "Quality-analysis mode runs Stage 11 gig quality rubric analysis.",
    "review-analysis": "Review-analysis mode runs Stage 12 review signal analysis.",
    "saturation-analysis": "Saturation-analysis mode runs Stage 13 saturation model analysis.",
    "score-only": "Scoring persistence foundation exists; scoring runner is not wired yet.",
    "analyze-only": "Analysis persistence foundation exists; analysis runner is not wired yet.",
    "price-analysis": "Run Stage 10.5 pricing analysis and recommendation calculations.",
    "recommendations-only": "Re-run Stage 13 for all eligible keywords using existing scores.",
    "discovery-only": "Discovery-only mode runs Stage 16 discovery cycle orchestration.",
    "discovery-collect": "Discovery-collect mode: runs collection then discovery stage. Pending full wiring.",
    "resume": "Resume mode placeholder is active; checkpoint resume flow is pending.",
}

PHASE2_EXPECTED_GATES = (
    "CI / Lint, Typecheck, Tests, and Gates",
    "codecov/project",
    "codecov/patch",
)


def _resolve_existing_run_id(db_session: Any) -> str | None:
    """Resolve the most recent collection run_id available in local DB."""
    if not hasattr(db_session, "query"):
        return None

    try:
        latest_search_run = (
            db_session.query(SearchResult.run_id).order_by(SearchResult.collected_at.desc()).limit(1).scalar()
        )
    except SQLAlchemyError:
        latest_search_run = None
    if isinstance(latest_search_run, str) and latest_search_run.strip():
        return latest_search_run.strip()

    try:
        latest_gig_run = (
            db_session.query(Gig.run_id)
            .filter(Gig.run_id.isnot(None))
            .order_by(Gig.created_at.desc())
            .limit(1)
            .scalar()
        )
    except SQLAlchemyError:
        latest_gig_run = None
    if isinstance(latest_gig_run, str) and latest_gig_run.strip():
        return latest_gig_run.strip()

    return None


def _run_collection_stage(
    run_id: str,
    db_session: Any,
    config: Any,
    config_payload: dict[str, Any],
) -> dict[str, Any]:
    """Runs Stage 1-13 collection plus its built-in analysis stages.

    Live vs. dry-run is auto-detected from saved Fiverr session validity, so a
    routine `full`/`collect-only` invocation never spends ScrapFly credits
    unless an operator has already completed `relogin` AND left
    `collection.scrapfly.enabled: true` in their config (that flag defaults to
    false in git, matching the existing live_pilot safety convention).
    Previously `full`/`collect-only` passed a fake `db={}` and hardcoded
    `dry_run=True` unconditionally, so this stage never ran for real and never
    persisted anything even when credentials were configured (SCRUM-1147).

    The session-validity check and the pipeline run share a single event loop
    (one `asyncio.run` call) because Playwright's Browser/BrowserContext
    objects are event-loop-bound: `is_session_valid()` initializes and caches
    a real context on the SessionManager, and running the pipeline afterward
    on a second, separate `asyncio.run` loop would hand that same manager a
    context tied to an already-closed loop, breaking every live fetch (Codex
    review, PR #172).
    """
    from src.collection.orchestrator import run_collection_pipeline

    async def _run() -> dict[str, Any]:
        session_manager: Any = None
        session_valid = False
        try:
            session_manager = _construct_session_manager(config)
            session_valid = await session_manager.is_session_valid()
        except Exception:  # noqa: BLE001
            pass

        try:
            return await run_collection_pipeline(
                run_id=run_id,
                db=db_session,
                config=config_payload,
                session_manager=session_manager,
                dry_run=not session_valid,
            )
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}
        finally:
            if session_manager is not None:
                try:
                    await session_manager.close()
                except Exception:  # noqa: BLE001
                    pass

    return asyncio.run(_run())


def _construct_session_manager(config: Any) -> Any:
    """Constructs the real Playwright-backed SessionManager.

    Kept as a standalone indirection point (rather than importing SessionManager
    directly inline) so tests can monkeypatch this one function instead of
    triggering a real Playwright import via the underlying module.
    """
    from src.collection.session_manager import SessionManager

    return SessionManager(config)


def _build_llm_client_safely(config_payload: dict[str, Any]) -> Any:
    """Builds a real LLM client when OPENAI_API_KEY is configured, else None."""
    try:
        from src.llm.client import build_llm_client

        return build_llm_client(config_payload)
    except Exception:  # noqa: BLE001
        return None


def _extract_active_niche_ids(config_payload: dict[str, Any]) -> list[str]:
    """Extracts active niche_id strings from config, mirroring each analysis
    module's own `_extract_niche_ids` convention."""
    niches = config_payload.get("niches", []) if isinstance(config_payload, dict) else []
    if not isinstance(niches, list):
        return []
    resolved: list[str] = []
    for niche in niches:
        if not isinstance(niche, dict):
            continue
        if niche.get("is_active", True) is False:
            continue
        niche_id = niche.get("niche_id")
        if isinstance(niche_id, str) and niche_id.strip():
            resolved.append(niche_id.strip())
    return resolved


def _resolve_full_mode_niche_pks(config_payload: dict[str, Any]) -> list[int]:
    """Resolves config niche_id entries to integer Keyword.niche_id PKs, when
    the config already uses numeric niche identifiers."""
    niche_ids: list[int] = []
    niches_payload = config_payload.get("niches", []) if isinstance(config_payload, dict) else []
    if isinstance(niches_payload, dict):
        return [int(niche_id) for niche_id in niches_payload.keys() if str(niche_id).isdigit()]
    if isinstance(niches_payload, list):
        for niche in niches_payload:
            if not isinstance(niche, dict):
                continue
            niche_id = niche.get("niche_id")
            if niche_id is not None and str(niche_id).isdigit():
                niche_ids.append(int(niche_id))
    return niche_ids


def _generate_full_run_reports(
    db_session: Any,
    run_id: str,
    duration_seconds: float,
    collection_result: dict[str, Any],
    scored_count: int,
    recommendations_result: dict[str, Any],
) -> dict[str, str]:
    """Auto-generates the run_summary and opportunity PDF reports at the end
    of every full run (PM_Pack/ref/project_plan/07_reporting/REPORT_TEMPLATES.md).

    Tolerates a missing WeasyPrint native install (Pango/Cairo/GObject) the
    same way src/playbook/generator.py does -- report generation failing
    never fails the pipeline run itself.
    """
    from src.reports.context import build_opportunity_report_context, build_run_summary_context
    from src.reports.generator import generate_report

    results: dict[str, str] = {}
    out_dir = "data/exports/reports"

    try:
        run_summary_context = build_run_summary_context(
            run_id=run_id,
            duration_seconds=duration_seconds,
            collection_result=collection_result,
            scored_count=scored_count,
            recommendations_result=recommendations_result,
            db=db_session,
        )
        results["run_summary"] = generate_report(
            "run_summary", run_summary_context, f"{out_dir}/run_summary_{run_id}.pdf", run_id=run_id
        )
    except Exception as exc:  # noqa: BLE001
        results["run_summary"] = f"error: {exc}"

    try:
        opportunity_context = build_opportunity_report_context(db_session)
        results["opportunity"] = generate_report(
            "opportunity", opportunity_context, f"{out_dir}/opportunity_{run_id}.pdf", run_id=run_id
        )
    except Exception as exc:  # noqa: BLE001
        results["opportunity"] = f"error: {exc}"

    return results


def build_dashboard_readiness_handoff(
    app_entry_smoke: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return dashboard readiness handoff contract for orchestration/reporting."""
    smoke_state = dict(app_entry_smoke or {})
    startup = dict(smoke_state.get("startup", {}))
    readiness = dict(smoke_state.get("readiness", {}))
    registration = dict(smoke_state.get("page_registration", {}))
    blocked_pages = list(readiness.get("blocked_pages", []))
    if not blocked_pages:
        blocked_pages = list(registration.get("missing_pages", []))
    warning_count = int(startup.get("warning_count", 0))
    next_actions = list(readiness.get("next_actions", []))
    if not next_actions:
        next_actions.append("Run dashboard smoke checks and publish readiness evidence.")
    stage_status = str(readiness.get("severity", smoke_state.get("status", "warning")))
    return {
        "phase": "dashboard-readiness",
        "stage_status": stage_status,
        "startup_status": startup.get("status", "warning"),
        "warning_count": warning_count,
        "blocked_pages": blocked_pages,
        "registration_status": registration.get("status", "blocked"),
        "next_actions": next_actions,
    }


def build_first_run_readiness_handoff(
    app_entry_smoke: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return first-run readiness handoff contract from app-entry diagnostics."""
    smoke_state = dict(app_entry_smoke or {})
    startup = dict(smoke_state.get("startup", {}))
    first_run = dict(startup.get("first_run_readiness", {}))
    known_blockers = list(first_run.get("known_blockers", []))
    prerequisites = dict(first_run.get("prerequisites", {}))
    stage_status = str(first_run.get("status", "warning")).strip().lower() or "warning"
    return {
        "phase": "first-run-readiness",
        "stage_status": stage_status,
        "expected_stages": list(first_run.get("expected_stages", [])),
        "fixture_paths": list(first_run.get("fixture_paths", [])),
        "required_outputs": list(first_run.get("required_outputs", [])),
        "missing_outputs": list(first_run.get("missing_outputs", [])),
        "known_blockers": known_blockers,
        "prerequisites": prerequisites,
    }


def run_init_db(database_url: str | None = None) -> int:
    return init_db_script_main(database_url=database_url)


def run_config_check(config_path: str = "config.yaml") -> int:
    loader = ConfigLoader(config_path)
    config = loader.load()
    profile_names = ", ".join(sorted(config.scoring.profiles.keys()))
    print(
        "Config OK:"
        f" niches={len(config.niches)}"
        f", active_profile={config.scoring.active_profile}"
        f", profiles=[{profile_names}]"
    )
    return 0


def run_smoke_checks(config_path: str = "config.yaml") -> int:
    checks: list[tuple[str, str]] = [
        ("config loader", "src.config.loader"),
        ("models package", "src.models"),
        ("collection contracts", "src.collection.contracts"),
        ("llm client", "src.llm.client"),
        ("dashboard placeholder", "src.dashboard"),
        ("exports placeholder", "src.exports"),
    ]
    for label, module_name in checks:
        importlib.import_module(module_name)
        print(f"Smoke OK: {label}")
    ConfigLoader(config_path).load()
    return 0


def run_foundation_release_gate(config_path: str = "config.yaml", database_url: str | None = None) -> int:
    return run_foundation_gate(config_path=config_path, database_url=database_url)


def run_export_stub(export_format: str, input_path: str) -> int:
    supported = {"csv", "excel", "pdf", "markdown"}
    if export_format not in supported:
        print(f"Unsupported export format '{export_format}'. Supported: {', '.join(sorted(supported))}")
        return 2
    if not input_path.strip():
        print("Missing required --input-path.")
        return 2
    print(
        "Export CLI surface is available. "
        "Full export generation is scheduled for Epic 09."
    )
    return 0


def run_dashboard_stub(mode: str) -> int:
    normalized = mode.strip().lower() or "local"
    dashboard_module = importlib.import_module("src.dashboard.app")
    app_entry_smoke = dashboard_module.build_app_entry_smoke_state()
    registration = app_entry_smoke["page_registration"]
    startup = app_entry_smoke["startup"]
    handoff = build_dashboard_readiness_handoff(app_entry_smoke)
    first_run_handoff = build_first_run_readiness_handoff(app_entry_smoke)
    print(
        f"Dashboard command accepted in '{normalized}' mode. "
        "Interactive dashboard runtime is scheduled for Epic 09."
    )
    print(f"Dashboard app-entry module: {app_entry_smoke['entry']['entry_module']}")
    print(f"Dashboard registration status: {registration['status']}")
    print(f"Dashboard startup status: {startup['status']}")
    print(f"Dashboard readiness stage status: {handoff['stage_status']}")
    print(f"First-run readiness stage status: {first_run_handoff['stage_status']}")
    if registration["missing_pages"]:
        missing = ", ".join(registration["missing_pages"])
        print(f"Dashboard app-entry missing registered pages: {missing}")
        return 1
    if startup["safe_empty_state"]:
        print("Dashboard app-entry running in safe empty-state mode.")
    return 0


def _load_fixture_payload(fixture_path: str) -> dict[str, Any] | None:
    fixture = Path(fixture_path)
    if not fixture.exists() or not fixture.is_file():
        print(f"Fixture file not found: {fixture}")
        return None
    try:
        payload = json.loads(fixture.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unable to read fixture file '{fixture}': {exc}")
        return None
    if not isinstance(payload, dict):
        print(f"Fixture payload must be a JSON object: {fixture}")
        return None
    return payload


def run_collection_dry_run(
    fixture_path: str,
    output_path: str,
    sample_size: int,
) -> int:
    payload = _load_fixture_payload(fixture_path)
    if payload is None:
        return 2

    seeds = payload.get("seed_keywords", payload.get("keywords", []))
    if not isinstance(seeds, list) or not all(isinstance(item, str) for item in seeds):
        print("Fixture must contain 'seed_keywords' or 'keywords' as a list of strings.")
        return 2

    trimmed_seeds = [item.strip() for item in seeds if item.strip()]
    if not trimmed_seeds:
        print("Fixture does not contain usable seed keywords.")
        return 2

    selected_seeds = trimmed_seeds[:sample_size] if sample_size > 0 else trimmed_seeds
    max_candidates = sample_size if sample_size > 0 else max(1, len(selected_seeds))
    collection_module = importlib.import_module("src.collection.orchestrator")
    result = collection_module.run_collection_dry_run(
        selected_seeds,
        niche_metadata=payload.get("niche_metadata"),
        max_candidates=max_candidates,
        max_pages=payload.get("max_pages", 1),
        checkpoint_path=Path(output_path),
        region=payload.get("region"),
        language=payload.get("language"),
        sort=payload.get("sort"),
    )
    status = str(result.status).lower()
    if status.endswith("success"):
        print(
            "Collection dry-run OK:"
            f" records_seen={result.records_seen}, records_written={result.records_written},"
            f" checkpoint={result.checkpoint_path}"
        )
        return 0

    print("Collection dry-run failed.")
    for error in result.errors:
        print(f"- {error.code}: {error.message}")
    return 1


def run_analysis_dry_run(
    fixture_path: str,
    output_path: str,
    sample_size: int,
    database_url: str | None = None,
) -> int:
    payload = _load_fixture_payload(fixture_path)
    if payload is None:
        return 2

    if isinstance(payload.get("keywords"), list) and sample_size > 0:
        payload["keywords"] = payload["keywords"][:sample_size]
    if isinstance(payload.get("competitors"), list) and sample_size > 0:
        payload["competitors"] = payload["competitors"][:sample_size]

    analysis_module = importlib.import_module("src.analysis.orchestrator")
    result = analysis_module.run_analysis_dry_run(payload)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    persistence_details: dict[str, Any] | None = None
    if database_url:
        persistence_module = importlib.import_module("src.analysis.persistence")
        persistence_details = persistence_module.persist_analysis_run_summary(
            result,
            database_url=database_url,
            mode="analysis-dry-run",
        )

    status = str(result.status).lower()
    if status.endswith("failed"):
        print(f"Analysis dry-run failed. Output written to {output}")
        return 1

    persisted_suffix = ""
    if persistence_details is not None:
        persisted_suffix = (
            f", persisted_run_id={persistence_details['run_table_id']},"
            f" persisted_stage_count={persistence_details['persisted_stage_count']}"
        )
    print(
        f"Analysis dry-run OK: status={result.status}, stages={len(result.stages)}, output={output}"
        f"{persisted_suffix}"
    )
    return 0


def run_phase2_smoke(config_path: str = "config.yaml") -> int:
    metadata = build_phase2_smoke_metadata()
    print(f"Phase2 smoke metadata: {json.dumps(metadata, sort_keys=True)}")

    checks: list[tuple[str, str]] = [
        ("collection package", "src.collection"),
        ("analysis package", "src.analysis"),
        ("phase2 config models", "src.config.models"),
    ]
    failures: list[str] = []
    for label, module_name in checks:
        try:
            importlib.import_module(module_name)
            print(f"Phase2 smoke OK: {label}")
        except Exception as exc:  # pragma: no cover - exercised in CLI tests via monkeypatch
            failures.append(f"{label}: {exc}")

    ConfigLoader(config_path).load()
    if failures:
        print("Phase2 smoke failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1
    return 0


def build_phase2_smoke_metadata() -> dict[str, Any]:
    """Return a deterministic governance contract for integration handoff."""
    return {
        "phase": "phase2-smoke",
        "expected_gates": list(PHASE2_EXPECTED_GATES),
        "jira_mapping_required": True,
        "codex_disposition_required": True,
        "dashboard_handoff_required": True,
        "dashboard_handoff_fields": [
            "stage_status",
            "startup_status",
            "warning_count",
            "blocked_pages",
            "next_actions",
        ],
    }


def run_pipeline(
    mode: str,
    config_path: str = "config.yaml",
    database_url: str | None = None,
    skip_collection: bool = False,
) -> int:
    if mode not in AVAILABLE_MODES:
        raise ValueError(f"Unsupported mode '{mode}'.")

    configure_logging()
    config = ConfigLoader(config_path).load()
    config_payload = config.model_dump() if hasattr(config, "model_dump") else {}
    normalized_url = normalize_database_url(database_url)
    engine = initialize_database(database_url=normalized_url)

    if mode == "recommendations-only":
        from src.recommendations.pipeline import run_recommendations_pipeline

        run_id = timestamp_stamp()
        try:
            session_factory = create_session_factory(engine)
            with get_session(session_factory) as db_session:
                result = asyncio.run(
                    run_recommendations_pipeline(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload,
                        llm_client=None,
                        cache=None,
                        dry_run=True,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Recommendations stage failed: {exc}")
            return 1
        print(f"Recommendations stage complete: {result}")
        return 0

    if mode == "price-analysis":
        from src.models import Keyword
        from src.pricing.orchestrator import run_pricing_stage

        run_id = timestamp_stamp()
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db_session:
            keyword_ids = [int(keyword_id) for (keyword_id,) in db_session.query(Keyword.id).all()]
            result = run_pricing_stage(
                run_id=run_id,
                keyword_ids=keyword_ids,
                db=db_session,
                config=config_payload,
            )
        print(f"Price analysis complete: {result}")
        return 0

    if mode == "collect-only":
        import uuid

        run_id = str(uuid.uuid4())
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db_session:
            result = _run_collection_stage(
                run_id=run_id,
                db_session=db_session,
                config=config,
                config_payload=config_payload if isinstance(config_payload, dict) else {},
            )
        if "error" in result:
            print(f"Collection dry run failed: {result['error']}")
            return 1
        print(f"Collection dry run complete: {result}")
        return 0

    if mode == "discovery-only":
        from src.discovery.stage16 import run_discovery_cycle

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                cycle_log = run_discovery_cycle(
                    db=db_session,
                    config=config_payload if isinstance(config_payload, dict) else {},
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Discovery cycle failed: {exc}")
            return 1
        print(f"Discovery complete: {cycle_log.hypotheses_accepted} keywords inserted")
        return 0

    if mode == "cluster-only":
        import uuid

        from src.analysis.keyword_clusterer import run_clustering_for_all_niches

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                run_id = _resolve_existing_run_id(db_session) or str(uuid.uuid4())
                result = asyncio.run(
                    run_clustering_for_all_niches(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload if isinstance(config_payload, dict) else {},
                        llm_client=None,
                        cache=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Cluster-only run failed: {exc}")
            return 1
        print(f"Cluster-only run complete: {result}")
        return 0

    if mode == "profile-only":
        import uuid

        from src.analysis.competitor_profiler import run_competitor_profiling_for_all_niches

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                run_id = _resolve_existing_run_id(db_session) or str(uuid.uuid4())
                result = asyncio.run(
                    run_competitor_profiling_for_all_niches(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload if isinstance(config_payload, dict) else {},
                        llm_client=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Profile-only run failed: {exc}")
            return 1
        print(f"Profile-only run complete: {result}")
        return 0

    if mode == "quality-analysis":
        import uuid

        from src.analysis.gig_quality_rubric import run_gig_quality_analysis_for_all_niches

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                run_id = _resolve_existing_run_id(db_session) or str(uuid.uuid4())
                result = asyncio.run(
                    run_gig_quality_analysis_for_all_niches(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload if isinstance(config_payload, dict) else {},
                        llm_client=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Quality-analysis run failed: {exc}")
            return 1
        print(f"Quality-analysis run complete: {result}")
        return 0

    if mode == "review-analysis":
        import uuid

        from src.analysis.review_analyzer import run_review_analysis_for_all_niches

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                run_id = _resolve_existing_run_id(db_session) or str(uuid.uuid4())
                result = asyncio.run(
                    run_review_analysis_for_all_niches(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload if isinstance(config_payload, dict) else {},
                        llm_client=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Review-analysis run failed: {exc}")
            return 1
        print(f"Review-analysis run complete: {result}")
        return 0

    if mode == "saturation-analysis":
        import uuid

        from src.analysis.saturation_model import run_saturation_analysis_for_all_niches

        session_factory = create_session_factory(engine)
        try:
            with get_session(session_factory) as db_session:
                run_id = _resolve_existing_run_id(db_session) or str(uuid.uuid4())
                result = asyncio.run(
                    run_saturation_analysis_for_all_niches(
                        run_id=run_id,
                        db=db_session,
                        config=config_payload if isinstance(config_payload, dict) else {},
                        llm_client=None,
                    )
                )
        except Exception as exc:  # noqa: BLE001
            print(f"Saturation-analysis run failed: {exc}")
            return 1
        print(f"Saturation-analysis run complete: {result}")
        return 0

    if mode == "full":
        import time
        import uuid

        from src.models import Keyword
        from src.playbook.generator import export_playbook_markdown, generate_playbook
        from src.pricing.orchestrator import run_pricing_stage
        from src.pricing.pricing_export import export_all_pricing
        from src.recommendations.export import export_all_recommendations
        from src.recommendations.pipeline import run_recommendations_pipeline
        from src.scoring.pipeline import score_keyword_batch

        run_started_at = time.monotonic()
        run_id = str(uuid.uuid4())
        payload = config_payload if isinstance(config_payload, dict) else {}
        profile_name = (
            getattr(getattr(config, "scoring", None), "active_profile", None)
            or payload.get("scoring", {}).get("active_profile")
            or "default"
        )
        niche_ids = _resolve_full_mode_niche_pks(payload)
        llm_client = _build_llm_client_safely(payload)

        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db_session:
            if skip_collection:
                # Caller already collected (or deliberately skipped) live data
                # upstream - e.g. live_validate_command's own Stage 2 - so "full"
                # mode must not silently re-trigger a real collection pass here
                # (Codex-adjacent finding: --skip-collection did not previously
                # propagate past live_validate's Stage 2 into this call).
                collection_result: dict[str, Any] = {"skipped": True, "reason": "skip_collection=True"}
            else:
                collection_result = _run_collection_stage(
                    run_id=run_id,
                    db_session=db_session,
                    config=config,
                    config_payload=payload,
                )

            keyword_query = db_session.query(Keyword.id)
            if niche_ids:
                keyword_query = keyword_query.filter(Keyword.niche_id.in_(niche_ids))
            keyword_ids = [int(keyword_id) for (keyword_id,) in keyword_query.all()]

            try:
                scored_results = asyncio.run(
                    score_keyword_batch(
                        keyword_ids=keyword_ids,
                        profile_name=profile_name,
                        db=db_session,
                        llm_client=llm_client,
                        cache=None,
                        config=payload,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                scored_results = []
                print(f"Scoring stage failed: {exc}")

            try:
                pricing_result = run_pricing_stage(
                    run_id=run_id,
                    keyword_ids=keyword_ids,
                    db=db_session,
                    config=payload,
                )
            except Exception as exc:  # noqa: BLE001
                pricing_result = {"error": str(exc)}

            try:
                recommendations_result = asyncio.run(
                    run_recommendations_pipeline(
                        run_id=run_id,
                        db=db_session,
                        config=payload,
                        llm_client=llm_client,
                        cache=None,
                        dry_run=llm_client is None,
                    )
                )
            except Exception as exc:  # noqa: BLE001
                recommendations_result = {"error": str(exc)}

            try:
                recommendations_export = asyncio.run(
                    export_all_recommendations(run_id=run_id, fmt="markdown", db=db_session, config=payload)
                )
            except Exception as exc:  # noqa: BLE001
                recommendations_export = {"error": str(exc)}

            try:
                pricing_export = export_all_pricing(
                    keyword_ids=keyword_ids,
                    db=db_session,
                    output_dir="data/exports/pricing",
                )
            except Exception as exc:  # noqa: BLE001
                pricing_export = {"error": str(exc)}

            playbook_results: dict[str, str] = {}
            for niche_id_str in _extract_active_niche_ids(payload):
                try:
                    playbook = generate_playbook(niche_id_str, db_session, payload)
                    markdown = export_playbook_markdown(playbook)
                    out_dir = Path("data/exports/playbook")
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_path = out_dir / f"{niche_id_str}.md"
                    out_path.write_text(markdown, encoding="utf-8")
                    playbook_results[niche_id_str] = str(out_path)
                except Exception as exc:  # noqa: BLE001
                    playbook_results[niche_id_str] = f"error: {exc}"

            report_results = _generate_full_run_reports(
                db_session=db_session,
                run_id=run_id,
                duration_seconds=time.monotonic() - run_started_at,
                collection_result=collection_result,
                scored_count=len(scored_results),
                recommendations_result=recommendations_result,
            )

        print(f"Collection complete: {collection_result}")
        print(f"Scoring complete: {len(scored_results)} keywords scored")
        print(f"Stage 10.5 complete: {pricing_result}")
        print(f"Recommendations complete: {recommendations_result}")
        print(
            "Exports complete: "
            f"recommendations={len(recommendations_export) if isinstance(recommendations_export, dict) else 0} "
            f"pricing={len(pricing_export) if isinstance(pricing_export, dict) else 0}"
        )
        print(f"Playbooks complete: {playbook_results}")
        print(f"Reports complete: {report_results}")
        return 0

    print(f"Mode: {mode}")
    print(f"Database: {normalized_url}")
    print(STAGE_AVAILABILITY[mode])
    return 0


def normalize_cli_config_path(config_path: str) -> str:
    return str(Path(config_path))
