"""Playwright session abstractions without browser execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class BrowserMode(StrEnum):
    UNAUTHENTICATED_READ_ONLY = "unauthenticated_read_only"
    AUTHENTICATED_READ_ONLY = "authenticated_read_only"


@dataclass(frozen=True, slots=True)
class SessionState:
    mode: BrowserMode
    session_path: Path | None
    valid: bool
    message: str


@dataclass(frozen=True, slots=True)
class SessionManagerConfig:
    mode: BrowserMode = BrowserMode.UNAUTHENTICATED_READ_ONLY
    headless: bool = True
    browser_channel: str | None = None
    session_file_path: Path | None = None
    repo_root: Path | None = None
    allowed_repo_session_dirs: tuple[str, ...] = field(default_factory=lambda: (".gitignored",))


class PlaywrightSessionManager:
    """Validates session file requirements and launch options."""

    def __init__(self, config: SessionManagerConfig) -> None:
        self.config = config
        self._repo_root = (config.repo_root or Path.cwd()).resolve()

    def describe_required_manual_setup(self) -> str:
        if self.config.mode == BrowserMode.AUTHENTICATED_READ_ONLY:
            return (
                "Authenticated read-only mode requires manual login outside automation and an "
                "external Playwright storage state file path."
            )
        return "Unauthenticated read-only mode does not require a session state file."

    def session_state_path(self) -> Path | None:
        return self.config.session_file_path

    def validate_session_state_file(self) -> SessionState:
        session_path = self.session_state_path()
        mode = self.config.mode
        if mode == BrowserMode.UNAUTHENTICATED_READ_ONLY and session_path is None:
            return SessionState(
                mode=mode,
                session_path=None,
                valid=True,
                message="No session file required for unauthenticated read-only mode.",
            )

        if mode == BrowserMode.AUTHENTICATED_READ_ONLY and session_path is None:
            return SessionState(
                mode=mode,
                session_path=None,
                valid=False,
                message="Authenticated mode requires session_file_path.",
            )

        assert session_path is not None
        if not self._is_session_path_safe(session_path):
            return SessionState(
                mode=mode,
                session_path=session_path,
                valid=False,
                message="Session file path under repository is not allowed unless explicitly safe.",
            )

        if not session_path.exists():
            return SessionState(
                mode=mode,
                session_path=session_path,
                valid=False,
                message="Session state file does not exist. Complete manual login first.",
            )

        return SessionState(mode=mode, session_path=session_path, valid=True, message="Session valid.")

    def build_launch_options(self) -> dict[str, object]:
        validation = self.validate_session_state_file()
        options: dict[str, object] = {"headless": self.config.headless}
        if self.config.browser_channel:
            options["channel"] = self.config.browser_channel

        if (
            self.config.mode == BrowserMode.AUTHENTICATED_READ_ONLY
            and validation.valid
            and validation.session_path is not None
        ):
            options["storage_state"] = str(validation.session_path)
        return options

    def _is_session_path_safe(self, path: Path) -> bool:
        try:
            resolved_path = path.resolve()
        except OSError:
            return False

        try:
            relative = resolved_path.relative_to(self._repo_root)
        except ValueError:
            return True

        relative_parts = set(relative.parts)
        return any(part in relative_parts for part in self.config.allowed_repo_session_dirs)
