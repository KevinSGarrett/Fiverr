"""Build machine-readable catalogs from PM_Pack/ref."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parent.parent
REF_DIR = REPO_ROOT / "PM_Pack" / "ref"
CATALOG_DIR = REPO_ROOT / "PM_Pack" / "automation"

PROJECT_PLAN_CATALOG_PATH = CATALOG_DIR / "project_plan_catalog.json"
DOD_CATALOG_PATH = CATALOG_DIR / "dod_catalog.json"
TODO_CATALOG_PATH = CATALOG_DIR / "todo_epic_catalog.json"
GITHUB_CATALOG_PATH = CATALOG_DIR / "github_governance_catalog.json"


def build_all_catalogs(ref_dir: Path = REF_DIR, catalog_dir: Path = CATALOG_DIR) -> dict[str, int]:
    """Build all catalogs and return entry counts."""
    catalog_dir.mkdir(parents=True, exist_ok=True)
    project_plan_catalog = build_project_plan_catalog(
        ref_dir=ref_dir, output_path=catalog_dir / "project_plan_catalog.json"
    )
    dod_catalog = build_dod_catalog(ref_dir=ref_dir, output_path=catalog_dir / "dod_catalog.json")
    todo_catalog = build_todo_catalog(ref_dir=ref_dir, output_path=catalog_dir / "todo_epic_catalog.json")
    github_catalog = build_github_catalog(
        ref_dir=ref_dir, output_path=catalog_dir / "github_governance_catalog.json"
    )
    return {
        "project_plan_catalog": len(project_plan_catalog["entries"]),
        "dod_catalog": len(dod_catalog["entries"]),
        "todo_epic_catalog": len(todo_catalog["entries"]),
        "github_governance_catalog": len(github_catalog["entries"]),
    }


def build_project_plan_catalog(ref_dir: Path = REF_DIR, output_path: Path | None = None) -> dict[str, Any]:
    """Build catalog for PM_Pack/ref/project_plan files."""
    project_plan_dir = ref_dir / "project_plan"
    entries: list[dict[str, Any]] = []
    if project_plan_dir.exists():
        for path in sorted(p for p in project_plan_dir.rglob("*") if p.is_file()):
            rel_path = _to_repo_relative(path)
            if path.suffix.lower() == ".zip":
                entries.append(
                    {
                        "source_path": rel_path,
                        "title": "archived-project-plan",
                        "type": "archive",
                        "wave": None,
                        "epic_ids": [],
                        "story_ids": [],
                        "jira_keys": [],
                        "files_or_modules": [],
                        "dod_refs": [],
                        "todo_refs": [],
                        "summary": "",
                    }
                )
                continue

            content = _read_text(path)
            title = _extract_title(content) or path.stem
            epic_ids = sorted(set(re.findall(r"EPIC_(\d{2})", content, flags=re.IGNORECASE)))
            epic_tokens = [f"EPIC_{value}" for value in epic_ids]
            story_ids = sorted(set(re.findall(r"\bS\d+\.\d+\b", content)))
            jira_keys = sorted(set(re.findall(r"\bSCRUM-\d+\b", content)))
            files_or_modules = sorted(set(re.findall(r"\bsrc/[A-Za-z0-9_./-]+\.py\b", content)))
            wave = _extract_wave(content)
            dod_refs = [f"PM_Pack/ref/dod/DOD_EPIC_{epic[-2:]}.md" for epic in epic_tokens]
            todo_refs = [f"PM_Pack/ref/todo/EPIC_{epic[-2:]}_*.md" for epic in epic_tokens]
            entries.append(
                {
                    "source_path": rel_path,
                    "title": title,
                    "type": "markdown",
                    "wave": wave,
                    "epic_ids": epic_tokens,
                    "story_ids": story_ids,
                    "jira_keys": jira_keys,
                    "files_or_modules": files_or_modules,
                    "dod_refs": dod_refs,
                    "todo_refs": todo_refs,
                    "summary": content[:300],
                }
            )

    catalog = {
        "generated_at": _now_iso(),
        "source_dir": _to_repo_relative(project_plan_dir),
        "entries": entries,
    }
    _write_json(output_path or PROJECT_PLAN_CATALOG_PATH, catalog)
    return catalog


def build_dod_catalog(ref_dir: Path = REF_DIR, output_path: Path | None = None) -> dict[str, Any]:
    """Build catalog for PM_Pack/ref/dod files."""
    dod_dir = ref_dir / "dod"
    entries: list[dict[str, Any]] = []
    if dod_dir.exists():
        for path in sorted(p for p in dod_dir.glob("DOD_EPIC_*.md") if p.is_file()):
            content = _read_text(path)
            epic_match = re.search(r"DOD_EPIC_(\d{2})\.md", path.name, flags=re.IGNORECASE)
            epic_id = f"EPIC_{epic_match.group(1)}" if epic_match else "EPIC_00"
            epic_name = _extract_title(content) or path.stem
            criteria = _extract_dod_criteria(content)
            validation_commands = _extract_validation_commands(content)
            entries.append(
                {
                    "source_path": _to_repo_relative(path),
                    "epic_id": epic_id,
                    "epic_name": epic_name,
                    "criteria": criteria,
                    "validation_commands": validation_commands,
                }
            )

    catalog = {"generated_at": _now_iso(), "source_dir": _to_repo_relative(dod_dir), "entries": entries}
    _write_json(output_path or DOD_CATALOG_PATH, catalog)
    return catalog


def build_todo_catalog(ref_dir: Path = REF_DIR, output_path: Path | None = None) -> dict[str, Any]:
    """Build catalog for PM_Pack/ref/todo files."""
    todo_dir = ref_dir / "todo"
    entries: list[dict[str, Any]] = []
    if todo_dir.exists():
        for path in sorted(p for p in todo_dir.glob("*.md") if p.is_file()):
            content = _read_text(path)
            epic_match = re.search(r"EPIC_(\d{2})", path.name, flags=re.IGNORECASE)
            epic_id = f"EPIC_{epic_match.group(1)}" if epic_match else "EPIC_00"
            open_stories = re.findall(r"^\s*-\s*\[\s\]\s*(.+)$", content, flags=re.MULTILINE)
            done_stories = re.findall(r"^\s*-\s*\[[xX]\]\s*(.+)$", content, flags=re.MULTILINE)
            total = len(open_stories) + len(done_stories)
            completion_pct = (len(done_stories) / total) if total else 0.0
            entries.append(
                {
                    "source_path": _to_repo_relative(path),
                    "epic_id": epic_id,
                    "open_stories": open_stories,
                    "done_stories": done_stories,
                    "completion_pct": completion_pct,
                }
            )

    catalog = {"generated_at": _now_iso(), "source_dir": _to_repo_relative(todo_dir), "entries": entries}
    _write_json(output_path or TODO_CATALOG_PATH, catalog)
    return catalog


def build_github_catalog(ref_dir: Path = REF_DIR, output_path: Path | None = None) -> dict[str, Any]:
    """Build catalog for PM_Pack/ref/github files."""
    github_dir = ref_dir / "github"
    entries: list[dict[str, Any]] = []
    if github_dir.exists():
        for path in sorted(p for p in github_dir.rglob("*") if p.is_file()):
            content = _read_text(path)
            entries.append(
                {
                    "source_path": _to_repo_relative(path),
                    "category": path.parent.name,
                    "title": _extract_title(content) or path.stem,
                    "summary": content[:300],
                }
            )

    catalog = {"generated_at": _now_iso(), "source_dir": _to_repo_relative(github_dir), "entries": entries}
    _write_json(output_path or GITHUB_CATALOG_PATH, catalog)
    return catalog


def verify(strict: bool = False, catalog_dir: Path = CATALOG_DIR) -> bool:
    """Verify catalog presence, freshness, and minimum entry counts."""
    max_age_hours = 24 if strict else 48
    checks = {
        "project_plan_catalog.json": 80,
        "dod_catalog.json": 10,
        "todo_epic_catalog.json": 10,
        "github_governance_catalog.json": 40,
    }
    for file_name, min_count in checks.items():
        path = catalog_dir / file_name
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except json.JSONDecodeError:
            return False
        generated_at = _parse_iso(payload.get("generated_at"))
        if generated_at is None:
            return False
        if datetime.now(UTC) - generated_at > timedelta(hours=max_age_hours):
            return False
        entries = payload.get("entries")
        if not isinstance(entries, list):
            return False
        if len(entries) < min_count:
            return False
    return True


def _extract_title(content: str) -> str:
    match = re.search(r"^\s*#\s+(.+?)\s*$", content, flags=re.MULTILINE)
    if match:
        return match.group(1).strip()
    return ""


def _extract_wave(content: str) -> str | None:
    match = re.search(r"\b(?:WAVE|Wave)\s*[:#-]?\s*(\d{1,2})\b", content)
    return match.group(1) if match else None


def _extract_dod_criteria(content: str) -> list[str]:
    patterns = [
        r"^\s*##+\s*Criteria\b",
        r"^\s*##+\s*Definition of Done\b",
    ]
    lines = content.splitlines()
    criteria: list[str] = []
    active = False
    for line in lines:
        if any(re.search(pattern, line, flags=re.IGNORECASE) for pattern in patterns):
            active = True
            continue
        if active and re.match(r"^\s*##+\s+", line):
            break
        if active:
            bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
            if bullet:
                criteria.append(bullet.group(1).strip())
    return criteria


def _extract_validation_commands(content: str) -> list[str]:
    commands: list[str] = []
    in_code = False
    for line in content.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            stripped = line.strip()
            if stripped.startswith("pytest") or stripped.startswith("python") or stripped.startswith("ruff"):
                commands.append(stripped)
    for snippet in re.findall(r"`([^`]+)`", content):
        stripped = snippet.strip()
        if stripped.startswith("pytest") or stripped.startswith("python") or stripped.startswith("ruff"):
            commands.append(stripped)
    commands = list(dict.fromkeys(commands))
    return commands


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    candidate = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _to_repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    import sys

    if "build" in sys.argv:
        results = build_all_catalogs()
        print(json.dumps(results, indent=2))
    elif "verify" in sys.argv:
        ok = verify(strict="--strict" in sys.argv)
        sys.exit(0 if ok else 1)
