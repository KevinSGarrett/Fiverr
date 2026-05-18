"""Unit tests for legacy compatibility export modules."""

from __future__ import annotations

import importlib


def test_models_init_compat_exports() -> None:
    module = importlib.import_module("src.models.init")
    assert hasattr(module, "Base")
    assert hasattr(module, "Job")


def test_scheduler_init_compat_exports() -> None:
    module = importlib.import_module("src.scheduler.init")
    assert hasattr(module, "QueueProcessor")
    assert hasattr(module, "execute_with_retry")
