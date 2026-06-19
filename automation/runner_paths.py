"""runner_paths.py -- Single source of truth for the runner root directory.

All runner-side state (logs, runs, state, reports, etc.) lives under a single
root directory. In production this is ``C:/AI_Runner``. Tests redirect it by
setting the ``AUTOPILOT_RUNNER_ROOT`` environment variable so that a full test
run never touches the live operator root.

The root is read LAZILY on every call so that fixtures setting the env var after
import are still honoured. Dependency-free (only ``os`` + ``pathlib``).
"""
from __future__ import annotations

import os
from pathlib import Path

# The production default. Never changes -- production must keep using this when
# the env var is unset. The write-guard compares against the resolved form.
DEFAULT_RUNNER_ROOT = "C:/AI_Runner"


def get_runner_root() -> Path:
    """Return the active runner root, honouring ``AUTOPILOT_RUNNER_ROOT`` lazily."""
    return Path(os.environ.get("AUTOPILOT_RUNNER_ROOT", DEFAULT_RUNNER_ROOT))


def real_runner_root() -> Path:
    """Return the DEFAULT runner root resolved (for the test write-guard)."""
    return Path(DEFAULT_RUNNER_ROOT).resolve()


def state_dir() -> Path:
    return get_runner_root() / "state"


def logs_dir() -> Path:
    return get_runner_root() / "logs"


def runs_dir() -> Path:
    return get_runner_root() / "runs"


def reports_dir() -> Path:
    return get_runner_root() / "reports"


def config_dir() -> Path:
    return get_runner_root() / "config"


def secrets_dir() -> Path:
    return get_runner_root() / "secrets"


def locks_dir() -> Path:
    return get_runner_root() / "locks"


def status_dir() -> Path:
    return get_runner_root() / "status"


def tmp_dir() -> Path:
    return get_runner_root() / "tmp"
