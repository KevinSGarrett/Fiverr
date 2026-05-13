"""Unit tests for dashboard presentation scaffolding."""

from __future__ import annotations

import builtins
import importlib


def test_dashboard_import_does_not_import_streamlit(monkeypatch) -> None:
    original_import = builtins.__import__

    def guarded_import(name: str, *args, **kwargs):
        if name == "streamlit":
            raise AssertionError("streamlit should not be imported during module import")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    module = importlib.import_module("src.dashboard.app")
    assert module.create_app_title() == "Fiverr Research System Dashboard (Cycle 001 Scaffold)"


def test_dashboard_package_exports_are_importable() -> None:
    module = importlib.import_module("src.dashboard")
    assert module.create_app_title() == "Fiverr Research System Dashboard (Cycle 001 Scaffold)"
    assert callable(module.main)

