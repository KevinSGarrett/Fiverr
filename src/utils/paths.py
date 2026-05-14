"""Shared path helpers."""

from __future__ import annotations

from pathlib import Path


def ensure_dir(path: Path | str) -> Path:
    """Create directory if needed and return normalized path."""
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def project_root() -> Path:
    """Return repository root based on this file location."""
    return Path(__file__).resolve().parents[2]


def resolve_data_path(relative_path: str = "fiverr_research.db") -> Path:
    """Resolve a path under the project data directory."""
    return project_root() / "data" / relative_path
