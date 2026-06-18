"""Global pytest fixtures for unit tests."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def smoke_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create an isolated data directory and default test database URL."""
    data_dir = tmp_path / "data"
    (data_dir / "checkpoints").mkdir(parents=True, exist_ok=True)
    (data_dir / "screenshots").mkdir(parents=True, exist_ok=True)
    (data_dir / "exports").mkdir(parents=True, exist_ok=True)
    db_path = data_dir / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    return data_dir


@pytest.fixture
def load_module_from_path() -> Callable[[str, str], ModuleType]:
    """Load a Python module directly from disk by relative path."""

    loaded: list[str] = []
    created_packages: list[str] = []

    def _ensure_parent_packages(module_name: str) -> None:
        parts = module_name.split(".")
        for index in range(1, len(parts)):
            package_name = ".".join(parts[:index])
            if package_name in sys.modules:
                continue
            package = ModuleType(package_name)
            package.__path__ = []  # type: ignore[attr-defined]
            sys.modules[package_name] = package
            created_packages.append(package_name)

    def _load(relative_path: str, module_name: str) -> ModuleType:
        _ensure_parent_packages(module_name)
        module_path = PROJECT_ROOT / relative_path
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"Unable to load module spec for {module_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        loaded.append(module_name)
        spec.loader.exec_module(module)
        parent_name, _, attr_name = module_name.rpartition(".")
        if parent_name and parent_name in sys.modules:
            setattr(sys.modules[parent_name], attr_name, module)
        return module

    try:
        yield _load
    finally:
        for module_name in reversed(loaded):
            sys.modules.pop(module_name, None)
        for package_name in reversed(created_packages):
            sys.modules.pop(package_name, None)

@pytest.fixture(autouse=False)
def isolated_runner_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """M-TEST-1 FIX: Redirect C:/AI_Runner to a temp directory for test isolation.

    Without this, tests that exercise state_writer, provider_health, or ai_cycle_controller
    write real files into C:/AI_Runner/state/ -- polluting the live runner state.
    Apply this fixture explicitly on tests that exercise these paths.

    Usage:
        def test_something(isolated_runner_root):
            # All writes to C:/AI_Runner go to tmp_path instead
    """
    runner_root = tmp_path / "AI_Runner"
    for subdir in ("state", "logs", "status", "locks", "tmp", "reports"):
        (runner_root / subdir).mkdir(parents=True, exist_ok=True)

    # Redirect RUNNER_ROOT in every module that imports it
    import automation.state_writer as _sw
    import automation.provider_health as _ph
    monkeypatch.setattr(_sw, "RUNNER_STATE_DIR", runner_root / "state")
    monkeypatch.setattr(_sw, "CONTROLLER_STATE_PATH", runner_root / "state" / "controller_state.json")
    monkeypatch.setattr(_sw, "HEARTBEAT_PATH", runner_root / "state" / "heartbeat.json")
    monkeypatch.setattr(_ph, "DEFAULT_PROVIDER_HEALTH_PATH",
                        runner_root / "state" / "provider_health.json")
    monkeypatch.setenv("PROVIDER_HEALTH_PATH",
                       str(runner_root / "state" / "provider_health.json"))

    return runner_root
