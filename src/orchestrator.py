"""CLI orchestration helpers for foundation-stage commands."""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from src.config import ConfigLoader
from src.models.database import initialize_database, normalize_database_url
from src.scripts.foundation_gate import run_foundation_gate
from src.scripts.init_db import main as init_db_script_main
from src.utils.logging import configure_logging

AVAILABLE_MODES = (
    "full",
    "collect-only",
    "score-only",
    "analyze-only",
    "recommendations-only",
    "discovery-only",
    "resume",
)

STAGE_AVAILABILITY = {
    "full": "Foundation CLI is active. Full pipeline orchestration is not wired yet.",
    "collect-only": "Collection module contracts exist; full collection orchestration is pending.",
    "score-only": "Scoring persistence foundation exists; scoring runner is not wired yet.",
    "analyze-only": "Analysis persistence foundation exists; analysis runner is not wired yet.",
    "recommendations-only": "Recommendation storage exists; recommendation engine is not wired yet.",
    "discovery-only": "Discovery storage exists; discovery orchestration is not wired yet.",
    "resume": "Resume mode placeholder is active; checkpoint resume flow is pending.",
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
    print(
        f"Dashboard command accepted in '{normalized}' mode. "
        "Interactive dashboard runtime is scheduled for Epic 09."
    )
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


def _resolve_collection_max_candidates(
    *,
    sample_size: int,
    selected_seeds: list[str],
    niche_metadata: Any,
) -> int:
    if sample_size > 0:
        return sample_size

    modifier_count = 0
    if isinstance(niche_metadata, dict):
        modifiers = niche_metadata.get("modifiers", [])
        if isinstance(modifiers, list):
            modifier_count = len([modifier for modifier in modifiers if isinstance(modifier, str) and modifier.strip()])

    # Keep uncapped dry-run stable by ensuring a positive candidate ceiling that
    # scales with fixture inputs while retaining deterministic behavior.
    estimated_candidates = len(selected_seeds) * max(1, (modifier_count * 2) + 1)
    return max(50, estimated_candidates)


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
    max_candidates = _resolve_collection_max_candidates(
        sample_size=sample_size,
        selected_seeds=selected_seeds,
        niche_metadata=payload.get("niche_metadata"),
    )
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

    status = str(result.status).lower()
    if status.endswith("failed"):
        print(f"Analysis dry-run failed. Output written to {output}")
        return 1

    print(f"Analysis dry-run OK: status={result.status}, stages={len(result.stages)}, output={output}")
    return 0


def run_phase2_smoke(config_path: str = "config.yaml") -> int:
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


def run_pipeline(mode: str, config_path: str = "config.yaml", database_url: str | None = None) -> int:
    if mode not in AVAILABLE_MODES:
        raise ValueError(f"Unsupported mode '{mode}'.")

    configure_logging()
    ConfigLoader(config_path).load()
    normalized_url = normalize_database_url(database_url)
    initialize_database(database_url=normalized_url)

    print(f"Mode: {mode}")
    print(f"Database: {normalized_url}")
    print(STAGE_AVAILABILITY[mode])
    return 0


def normalize_cli_config_path(config_path: str) -> str:
    return str(Path(config_path))
