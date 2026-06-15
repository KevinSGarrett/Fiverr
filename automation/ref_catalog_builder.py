"""Build and verify lightweight reference catalogs for PM/automation docs."""
from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import click

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "PM_Pack/automation/ref_catalogs"


@dataclass(frozen=True)
class CatalogSpec:
    name: str
    relative_root: str
    patterns: tuple[str, ...]


SPECS: tuple[CatalogSpec, ...] = (
    CatalogSpec("pm_pack_ref", "PM_Pack/ref", ("*.md", "*.yml", "*.yaml", "*.json")),
    CatalogSpec("pm_pack_automation", "PM_Pack/automation", ("*.md", "*.yml", "*.yaml", "*.json")),
    CatalogSpec("docs_architecture", "docs/architecture", ("*.md",)),
    CatalogSpec("cycle_reports", "docs/cycle_reports", ("*.md",)),
)


def _iter_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    files: set[Path] = set()
    if not root.exists():
        return []
    for pattern in patterns:
        files.update(p for p in root.rglob(pattern) if p.is_file())
    return sorted(files)


def _build_catalog(spec: CatalogSpec) -> dict[str, object]:
    root = REPO_ROOT / spec.relative_root
    files = _iter_files(root, spec.patterns)
    rel_files = [str(p.relative_to(REPO_ROOT)).replace("\\", "/") for p in files]
    return {
        "catalog": spec.name,
        "generated_at": datetime.now(UTC).isoformat(),
        "root": spec.relative_root,
        "entry_count": len(rel_files),
        "entries": rel_files,
    }


def build_catalogs() -> list[dict[str, object]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payloads: list[dict[str, object]] = []
    for spec in SPECS:
        payload = _build_catalog(spec)
        out_path = OUT_DIR / f"{spec.name}.json"
        out_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        payloads.append(payload)
    return payloads


def verify_catalogs(strict: bool) -> tuple[bool, list[str]]:
    issues: list[str] = []
    for spec in SPECS:
        path = OUT_DIR / f"{spec.name}.json"
        if not path.exists():
            issues.append(f"Missing catalog file: {path}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
        if not isinstance(entries, list):
            issues.append(f"{spec.name}: entries must be a list")
            continue
        if strict and len(entries) == 0:
            issues.append(f"{spec.name}: strict mode requires non-empty entries")
    return (len(issues) == 0, issues)


@click.group()
def cli() -> None:
    """Reference catalog build/verify command group."""


@cli.command("build")
def cmd_build() -> None:
    """Build all reference catalogs."""
    payloads = build_catalogs()
    for payload in payloads:
        click.echo(f"{payload['catalog']}: {payload['entry_count']} entries")
    click.secho("REF CATALOG BUILD PASS", fg="green", bold=True)


@cli.command("verify")
@click.option("--strict", is_flag=True, default=False, help="Require non-empty catalogs.")
def cmd_verify(strict: bool) -> None:
    """Verify catalogs exist and are parseable."""
    ok, issues = verify_catalogs(strict=strict)
    if not ok:
        for issue in issues:
            click.secho(f"  ISSUE: {issue}", fg="red")
        click.secho("REF CATALOG VERIFY FAIL", fg="red", bold=True)
        raise SystemExit(1)

    for spec in SPECS:
        data = json.loads((OUT_DIR / f"{spec.name}.json").read_text(encoding="utf-8"))
        click.echo(f"{spec.name}: {data.get('entry_count', 0)} entries")
    click.secho("REF CATALOG VERIFY PASS", fg="green", bold=True)


if __name__ == "__main__":
    cli()
