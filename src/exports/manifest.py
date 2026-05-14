"""Export manifest contract for future artifact tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.exports.formats import ExportFormat, normalize_export_format

CHECKSUM_PLACEHOLDER = "pending:sha256"


@dataclass(frozen=True, slots=True)
class ExportManifest:
    """Serializable metadata for a generated export artifact."""

    artifact_type: str
    format: ExportFormat | str
    source_cycle: str
    path: str
    included_sections: tuple[str, ...] = ()
    generated_at: str = field(default_factory=lambda: datetime.now(tz=UTC).isoformat())
    checksum: str = CHECKSUM_PLACEHOLDER

    def __post_init__(self) -> None:
        object.__setattr__(self, "format", normalize_export_format(self.format))

        if not self.artifact_type.strip():
            raise ValueError("artifact_type is required.")
        if not self.source_cycle.strip():
            raise ValueError("source_cycle is required.")
        if not self.path.strip():
            raise ValueError("path is required.")
        if self.checksum != CHECKSUM_PLACEHOLDER and not self.checksum.startswith("sha256:"):
            raise ValueError("checksum must be 'pending:sha256' or prefixed with 'sha256:'.")
        if self.checksum.startswith("sha256:") and len(self.checksum) <= len("sha256:"):
            raise ValueError("checksum digest is missing after 'sha256:'.")

    def to_dict(self) -> dict[str, object]:
        """Return a plain-structure dictionary for serialization."""
        return {
            "artifact_type": self.artifact_type,
            "format": normalize_export_format(self.format).value,
            "source_cycle": self.source_cycle,
            "generated_at": self.generated_at,
            "path": self.path,
            "checksum": self.checksum,
            "included_sections": list(self.included_sections),
        }
