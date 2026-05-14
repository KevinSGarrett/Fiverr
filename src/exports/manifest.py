"""Export manifest contract for future artifact tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.exports.formats import ExportFormat


@dataclass(frozen=True, slots=True)
class ExportManifest:
    """Serializable metadata for a generated export artifact."""

    artifact_path: str
    format: ExportFormat
    row_count: int | None = None
    created_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    source_run_id: str | None = None
    checksum: str | None = None

    def to_dict(self) -> dict[str, str | int | None]:
        """Return a plain-structure dictionary for serialization."""
        return {
            "artifact_path": self.artifact_path,
            "format": self.format.value,
            "row_count": self.row_count,
            "created_at": self.created_at,
            "source_run_id": self.source_run_id,
            "checksum": self.checksum,
        }
