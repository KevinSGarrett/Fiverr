"""Foundation release gate checks."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path

from src.config import ConfigLoader
from src.models.database import initialize_database, list_tables, normalize_database_url
from src.models.registry import get_missing_source_tables, get_registered_table_names
from src.scripts.repo_hygiene import find_hygiene_issues
from src.utils.paths import project_root

SMOKE_IMPORT_MODULES = (
    "src.config.loader",
    "src.models",
    "src.collection.contracts",
    "src.llm.client",
    "src.utils.paths",
)


@dataclass
class GateCheck:
    name: str
    passed: bool
    details: str


def _run_import_checks() -> GateCheck:
    for module_name in SMOKE_IMPORT_MODULES:
        importlib.import_module(module_name)
    return GateCheck(
        name="smoke_imports",
        passed=True,
        details=f"Imported {len(SMOKE_IMPORT_MODULES)} key modules.",
    )


def _run_table_checks(database_url: str) -> GateCheck:
    engine = initialize_database(database_url=database_url)
    existing_tables = set(list_tables(engine))
    registered_tables = set(get_registered_table_names())
    missing_registered = sorted(registered_tables - existing_tables)
    if missing_registered:
        return GateCheck(
            name="database_registry",
            passed=False,
            details=f"Missing registered tables: {', '.join(missing_registered)}",
        )
    missing_source = get_missing_source_tables()
    return GateCheck(
        name="database_registry",
        passed=True,
        details=(
            f"created={len(existing_tables)}"
            f", registered={len(registered_tables)}"
            f", source_missing={len(missing_source)}"
        ),
    )


def run_foundation_gate(
    *,
    config_path: str = "config.yaml",
    database_url: str | None = None,
    repo_root: Path | None = None,
) -> int:
    """Run deterministic local checks and print PASS/FAIL summary."""
    checks: list[GateCheck] = []
    failed = False

    try:
        ConfigLoader(config_path).load()
        checks.append(GateCheck(name="config_load", passed=True, details=f"Loaded {config_path}"))
    except Exception as exc:
        checks.append(GateCheck(name="config_load", passed=False, details=str(exc)))
        failed = True

    try:
        normalized_url = normalize_database_url(database_url)
        checks.append(_run_table_checks(normalized_url))
    except Exception as exc:
        checks.append(GateCheck(name="database_registry", passed=False, details=str(exc)))
        failed = True

    try:
        checks.append(_run_import_checks())
    except Exception as exc:
        checks.append(GateCheck(name="smoke_imports", passed=False, details=str(exc)))
        failed = True

    try:
        issues = find_hygiene_issues(repo_root=repo_root or project_root())
        if issues:
            details = ", ".join(f"{issue.issue_type}:{issue.path}" for issue in issues[:5])
            checks.append(GateCheck(name="repo_hygiene", passed=False, details=details))
            failed = True
        else:
            checks.append(GateCheck(name="repo_hygiene", passed=True, details="No hygiene issues detected."))
    except Exception as exc:
        checks.append(GateCheck(name="repo_hygiene", passed=False, details=str(exc)))
        failed = True

    for check in checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"[{status}] {check.name}: {check.details}")

    return 1 if failed or any(not check.passed for check in checks) else 0
