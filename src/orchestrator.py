"""CLI orchestration helpers for foundation-stage commands."""

from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
from typing import Any

from src.config import ConfigLoader
from src.models.database import (
    create_session_factory,
    get_session,
    initialize_database,
    normalize_database_url,
)
from src.scripts.foundation_gate import run_foundation_gate
from src.scripts.init_db import main as init_db_script_main
from src.utils.datetime import timestamp_stamp
from src.utils.logging import configure_logging

AVAILABLE_MODES = (
    "full",
    "collect-only",
    "score-only",
    "analyze-only",
    "price-analysis",
    "recommendations-only",
    "discovery-only",
    "discovery-collect",
    "resume",
)

STAGE_AVAILABILITY = {
    "full": "Foundation CLI is active. Full pipeline orchestration is not wired yet.",
    "collect-only": "Collection module contracts exist; full collection orchestration is pending.",
    "score-only": "Scoring persistence foundation exists; scoring runner is not wired yet.",
    "analyze-only": "Analysis persistence foundation exists; analysis runner is not wired yet.",
    "price-analysis": "Run Stage 10.5 pricing analysis and recommendation calculations.",
    "recommendations-only": "Re-run Stage 13 for all eligible keywords using existing scores.",
    "discovery-only": "Discovery storage exists; discovery orchestration is not wired yet.",
    "discovery-collect": "Discovery-collect mode: runs collection then discovery stage. Pending full wiring.",
    "resume": "Resume mode placeholder is active; checkpoint resume flow is pending.",
}

PHASE2_EXPECTED_GATES = (
    "CI / Lint, Typecheck, Tests, and Gates",
    "codecov/project",
    "codecov/patch",
)


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


def run_pipeline(mode: str, config_path: str = "config.yaml", database_url: str | None = None) -> int:
    if mode not in AVAILABLE_MODES:
        raise ValueError(f"Unsupported mode '{mode}'.")

    configure_logging()
    config = ConfigLoader(config_path).load()
    config_payload = config.model_dump() if hasattr(config, "model_dump") else {}
    normalized_url = normalize_database_url(database_url)
    engine = initialize_database(database_url=normalized_url)

    if mode == "recommendations-only":
        from src.recommendations.run import run_recommendations_stage

        run_id = timestamp_stamp()
        try:
            session_factory = create_session_factory(engine)
            with get_session(session_factory) as db_session:
                result = asyncio.run(
                    run_recommendations_stage(
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

    if mode == "full":
        from src.models import Keyword
        from src.scoring.pipeline import score_keyword_batch

        profile_name = (
            getattr(getattr(config, "scoring", None), "active_profile", None)
            or config_payload.get("scoring", {}).get("active_profile")
            or "default"
        )
        niche_ids = [int(niche_id) for niche_id in config_payload.get("niches", {}).keys() if str(niche_id).isdigit()]
        session_factory = create_session_factory(engine)
        with get_session(session_factory) as db_session:
            keyword_query = db_session.query(Keyword.id)
            if niche_ids:
                keyword_query = keyword_query.filter(Keyword.niche_id.in_(niche_ids))
            keyword_ids = [int(keyword_id) for (keyword_id,) in keyword_query.all()]
            scored_results = asyncio.run(
                score_keyword_batch(
                    keyword_ids=keyword_ids,
                    profile_name=profile_name,
                    db=db_session,
                    llm_client=None,
                    cache=None,
                )
            )
        print(f"Scoring complete: {len(scored_results)} keywords scored")
        return 0

    print(f"Mode: {mode}")
    print(f"Database: {normalized_url}")
    print(STAGE_AVAILABILITY[mode])
    return 0


def normalize_cli_config_path(config_path: str) -> str:
    return str(Path(config_path))
