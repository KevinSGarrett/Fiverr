"""CLI orchestration helpers for foundation-stage commands."""

from __future__ import annotations

import importlib
from pathlib import Path

from src.config import ConfigLoader
from src.models.database import initialize_database, normalize_database_url
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
