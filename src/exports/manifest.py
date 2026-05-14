"""Export manifest contract for future artifact tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import PurePosixPath

from src.exports.formats import ALLOWED_EXPORT_ROOTS, ExportFormat, normalize_export_format

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
    allow_pending_checksum: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "format", normalize_export_format(self.format))

        if not self.artifact_type.strip():
            raise ValueError("artifact_type is required.")
        if not self.source_cycle.strip():
            raise ValueError("source_cycle is required.")
        if not self.path.strip():
            raise ValueError("path is required.")
        normalized_path = PurePosixPath(self.path.replace("\\", "/"))
        if normalized_path.is_absolute():
            raise ValueError("path must be relative to the repository artifact directories.")
        if ".." in normalized_path.parts:
            raise ValueError("path must not include parent directory traversal ('..').")
        root_dir = normalized_path.parts[0] if normalized_path.parts else ""
        if root_dir not in ALLOWED_EXPORT_ROOTS:
            allowed = ", ".join(ALLOWED_EXPORT_ROOTS)
            raise ValueError(f"path root must be one of: {allowed}.")

        if self.checksum == CHECKSUM_PLACEHOLDER and not self.allow_pending_checksum:
            raise ValueError("checksum is required when allow_pending_checksum is False.")
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
            "allow_pending_checksum": self.allow_pending_checksum,
            "included_sections": list(self.included_sections),
        }
