"""Export path and directory utilities — AC-1.6.6."""

from __future__ import annotations

from pathlib import Path

from src.utils.paths import project_root

# Sub-directories created under data/exports/
_EXPORT_SUBDIRS: tuple[str, ...] = (
    "reports",
    "csv",
    "json",
    "markdown",
    "pdf",
    "playbook",
)


def ensure_export_dirs(base_path: Path | str | None = None) -> Path:
    """Create all required export subdirectories and return the export root.

    Creates ``data/exports/`` and each standard sub-folder if they do not
    already exist.  Safe to call repeatedly (idempotent).

    Args:
        base_path: Override for the export root directory.  Defaults to
            ``<project_root>/data/exports``.

    Returns:
        The resolved export root :class:`~pathlib.Path`.
    """
    if base_path is None:
        export_root = project_root() / "data" / "exports"
    else:
        export_root = Path(base_path)

    export_root.mkdir(parents=True, exist_ok=True)
    for subdir in _EXPORT_SUBDIRS:
        (export_root / subdir).mkdir(parents=True, exist_ok=True)

    return export_root


def get_export_path(
    format: str,
    filename: str,
    base_path: Path | str | None = None,
) -> Path:
    """Return a full export file path for the given format and filename.

    Ensures the target directory exists before returning.

    Args:
        format: Export format string (``"csv"``, ``"json"``, ``"markdown"``,
            ``"pdf"``, ``"reports"``, ``"playbook"``).
        filename: Base filename (e.g. ``"opportunities_20240101.csv"``).
        base_path: Optional override for the export root.

    Returns:
        Resolved :class:`~pathlib.Path` for the export file.
    """
    export_root = ensure_export_dirs(base_path)
    subdir = export_root / format
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir / filename
