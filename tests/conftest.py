"""Global pytest fixtures for unit tests."""

from __future__ import annotations

import builtins
import importlib.util
import os
import pathlib
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Subdirectories created under every isolated runner root.
_RUNNER_SUBDIRS = (
    "state",
    "logs",
    "runs",
    "reports",
    "config",
    "secrets",
    "locks",
    "status",
    "tmp",
)


def _real_runner_root() -> Path:
    """Resolved production runner root (C:/AI_Runner) for write-guard comparison."""
    from automation import runner_paths

    return runner_paths.real_runner_root()


def _is_under(path: Path, root: Path) -> bool:
    """True when ``path`` resolves to somewhere under ``root`` (both resolved)."""
    try:
        resolved = path.resolve()
    except (OSError, ValueError, RuntimeError):
        # Unresolvable paths (e.g. bad chars) are never under the live root.
        return False
    try:
        return resolved == root or resolved.is_relative_to(root)
    except (ValueError, OSError):
        return False


# ---------------------------------------------------------------------------
# Session-scoped isolation: one tmp runner root for the entire test session.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _session_runner_root(tmp_path_factory: pytest.TempPathFactory):
    """Create one per-session tmp runner root and point the env var at it.

    Guarantees that any code resolving paths via ``automation.runner_paths`` (or
    the legacy ``C:/AI_Runner`` constants re-pointed below) writes under tmp for
    the whole session.
    """
    runner_root = tmp_path_factory.mktemp("AI_Runner_session")
    for subdir in _RUNNER_SUBDIRS:
        (runner_root / subdir).mkdir(parents=True, exist_ok=True)
    os.environ["AUTOPILOT_RUNNER_ROOT"] = str(runner_root)
    return runner_root


# ---------------------------------------------------------------------------
# 0.3 test-seam migration.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def _test_harness_optin():
    """Item 0.3 (B5/C7): mark the whole session as the sanctioned test harness.

    The fail-closed ENTRY GUARD in ai_cycle_controller refuses to run tick /
    run-cycle when ``PYTEST_CURRENT_TEST`` is set without ``AUTOPILOT_TEST_HARNESS``.
    pytest itself sets ``PYTEST_CURRENT_TEST`` for every test, so without this the
    guard would refuse every controller invocation. Setting the opt-in here lets
    the suite exercise tick/run-cycle while a leaked var in production (no harness)
    still fails closed.
    """
    prev = os.environ.get("AUTOPILOT_TEST_HARNESS")
    os.environ["AUTOPILOT_TEST_HARNESS"] = "1"
    yield
    if prev is None:
        os.environ.pop("AUTOPILOT_TEST_HARNESS", None)
    else:
        os.environ["AUTOPILOT_TEST_HARNESS"] = prev


@pytest.fixture(autouse=True)
def _fake_run_and_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    """Item 0.3 (C8): never spawn a real agent subprocess during tests.

    The production ``_run_and_stream`` PYTEST short-circuit was removed (a leaked
    env var must not turn a live dispatch into a silent no-op). This autouse
    fixture replaces that seam for the suite: it monkeypatches the controller's
    ``_run_and_stream`` to a fake returning ``(0, "ok")`` WITHOUT a subprocess.

    Tests that need the REAL implementation (e.g. proving the short-circuit is
    gone) restore it explicitly via ``monkeypatch`` in the test body.
    """
    try:
        import automation.ai_cycle_controller as ctrl
    except Exception:
        return
    monkeypatch.setattr(
        ctrl, "_run_and_stream",
        lambda args, label="": (0, "ok"), raising=False,
    )


@pytest.fixture(autouse=True)
def _fake_open_cycle_pr(monkeypatch: pytest.MonkeyPatch) -> None:
    """Item 3.1: never push / open a real GitHub PR during tests.

    ``cmd_run_cycle`` now calls ``pr_builder.open_cycle_pr`` after the work-proof
    gate whenever a cycle committed real work. Without this seam, every existing
    run-cycle test that seeds committed work (e.g. the 2.1 work-proof tests) would
    try a real ``git push`` + ``gh pr create``. This autouse fixture replaces it
    with a deterministic fake success (created+verified) WITHOUT any subprocess.

    The dedicated 3.1 tests that exercise the REAL ``open_cycle_pr`` capture the
    real implementation at import time and call it directly, bypassing this seam.
    """
    try:
        from automation import pr_builder
    except Exception:
        return
    monkeypatch.setattr(
        pr_builder, "open_cycle_pr",
        lambda cycle, *a, **k: {
            "created": True, "existing": False,
            "pr_number": 9000 + int(cycle), "url": f"https://example.test/pr/{cycle}",
            "verified": True, "error": "",
        },
        raising=False,
    )


def _repoint_module_path_constants(
    monkeypatch: pytest.MonkeyPatch, tmp_root: Path, real_root: Path
) -> None:
    """Re-point already-imported ``automation.*`` Path constants at tmp_root.

    Generic: for every loaded module under the ``automation`` package, inspect
    module-level attributes that are ``pathlib.Path`` instances resolving under
    the real runner root, and monkeypatch them to the tmp-root equivalent
    (recomputing the sub-path after the root swap).
    """
    for mod_name, module in list(sys.modules.items()):
        if module is None:
            continue
        if not (mod_name == "automation" or mod_name.startswith("automation.")):
            continue
        module_dict = getattr(module, "__dict__", None)
        if module_dict is None:
            continue
        for attr_name, value in list(module_dict.items()):
            if not isinstance(value, Path):
                continue
            if not _is_under(value, real_root):
                continue
            try:
                rel = value.resolve().relative_to(real_root)
            except (ValueError, OSError):
                continue
            monkeypatch.setattr(module, attr_name, tmp_root / rel, raising=False)


@pytest.fixture(autouse=True)
def _isolate_runner_writes(
    monkeypatch: pytest.MonkeyPatch, _session_runner_root: Path
) -> None:
    """Autouse per-test isolation.

    1. Ensure the env var points at the session tmp root.
    2. Generically re-point already-imported ``automation.*`` Path constants.
    3. Explicitly re-point the well-known constants in state_writer,
       autopilot_logger and provider_health (mirroring isolated_runner_root).
    """
    tmp_root = _session_runner_root
    real_root = _real_runner_root()

    monkeypatch.setenv("AUTOPILOT_RUNNER_ROOT", str(tmp_root))

    # (2) Generic re-point of every loaded automation.* Path constant.
    _repoint_module_path_constants(monkeypatch, tmp_root, real_root)

    # (3) Explicit re-point of the well-known constants (in case a module is
    #     imported later or its attribute wasn't a Path under the real root).
    state_tmp = tmp_root / "state"
    runs_tmp = tmp_root / "runs"
    logs_tmp = tmp_root / "logs"

    if "automation.state_writer" in sys.modules:
        sw = sys.modules["automation.state_writer"]
        monkeypatch.setattr(sw, "RUNNER_STATE_DIR", state_tmp, raising=False)
        monkeypatch.setattr(sw, "RUNNER_RUNS_DIR", runs_tmp, raising=False)
        monkeypatch.setattr(
            sw, "CONTROLLER_STATE_PATH", state_tmp / "controller_state.json",
            raising=False,
        )
        monkeypatch.setattr(
            sw, "HEARTBEAT_PATH", state_tmp / "heartbeat.json", raising=False
        )

    if "automation.autopilot_logger" in sys.modules:
        al = sys.modules["automation.autopilot_logger"]
        monkeypatch.setattr(al, "LOG_DIR", logs_tmp, raising=False)
        monkeypatch.setattr(al, "RUNS_DIR", runs_tmp, raising=False)
        monkeypatch.setattr(al, "STATE_DIR", state_tmp, raising=False)
        monkeypatch.setattr(
            al, "_ACTIVITY_FILE", state_tmp / "current_activity.json", raising=False
        )

    if "automation.provider_health" in sys.modules:
        ph = sys.modules["automation.provider_health"]
        monkeypatch.setattr(
            ph, "DEFAULT_PROVIDER_HEALTH_PATH",
            state_tmp / "provider_health.json", raising=False,
        )
    monkeypatch.setenv("PROVIDER_HEALTH_PATH", str(state_tmp / "provider_health.json"))


# ---------------------------------------------------------------------------
# WRITE-GUARD: fail any test that writes under the real runner root.
# ---------------------------------------------------------------------------
def _mode_is_write(mode: str) -> bool:
    return any(ch in mode for ch in ("w", "a", "x", "+"))


@pytest.fixture(autouse=True)
def _write_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise if any code writes a file under the real C:/AI_Runner root.

    Wraps Path.mkdir / write_text / write_bytes / open and builtins.open. Allows
    every other path (tmp, repo, pytest internals, coverage) through unchanged.
    """
    real_root = _real_runner_root()

    orig_mkdir = pathlib.Path.mkdir
    orig_write_text = pathlib.Path.write_text
    orig_write_bytes = pathlib.Path.write_bytes
    orig_path_open = pathlib.Path.open
    orig_builtin_open = builtins.open

    def _violation(path: object) -> RuntimeError:
        return RuntimeError(
            f"TEST ISOLATION VIOLATION: write to live runner root: {path}"
        )

    def _guarded_mkdir(self: pathlib.Path, *args: object, **kwargs: object):
        if _is_under(self, real_root):
            raise _violation(self)
        return orig_mkdir(self, *args, **kwargs)  # type: ignore[arg-type]

    def _guarded_write_text(self: pathlib.Path, *args: object, **kwargs: object):
        if _is_under(self, real_root):
            raise _violation(self)
        return orig_write_text(self, *args, **kwargs)  # type: ignore[arg-type]

    def _guarded_write_bytes(self: pathlib.Path, *args: object, **kwargs: object):
        if _is_under(self, real_root):
            raise _violation(self)
        return orig_write_bytes(self, *args, **kwargs)  # type: ignore[arg-type]

    def _guarded_path_open(
        self: pathlib.Path, mode: str = "r", *args: object, **kwargs: object
    ):
        if _mode_is_write(mode) and _is_under(self, real_root):
            raise _violation(self)
        return orig_path_open(self, mode, *args, **kwargs)  # type: ignore[arg-type]

    def _guarded_builtin_open(
        file: object, mode: str = "r", *args: object, **kwargs: object
    ):
        if isinstance(file, str | os.PathLike) and _mode_is_write(mode):
            if _is_under(Path(os.fspath(file)), real_root):
                raise _violation(file)
        return orig_builtin_open(file, mode, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(pathlib.Path, "mkdir", _guarded_mkdir, raising=False)
    monkeypatch.setattr(pathlib.Path, "write_text", _guarded_write_text, raising=False)
    monkeypatch.setattr(pathlib.Path, "write_bytes", _guarded_write_bytes, raising=False)
    monkeypatch.setattr(pathlib.Path, "open", _guarded_path_open, raising=False)
    monkeypatch.setattr(builtins, "open", _guarded_builtin_open, raising=False)


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
