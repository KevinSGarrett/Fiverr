"""Tests for side-effect-free Playwright availability checks."""

from __future__ import annotations

import importlib

from src.collection.playwright_check import check_playwright_chromium_available


def test_check_playwright_chromium_available_when_import_succeeds(
    monkeypatch,
) -> None:
    monkeypatch.setattr(importlib, "import_module", lambda _name: object())

    result = check_playwright_chromium_available()

    assert result["available"] is True
    assert result["needs_install"] is False


def test_check_playwright_chromium_available_when_import_fails(
    monkeypatch,
) -> None:
    def _raise(_name: str) -> object:
        raise ModuleNotFoundError("playwright")

    monkeypatch.setattr(importlib, "import_module", _raise)

    result = check_playwright_chromium_available()

    assert result["available"] is False
    assert result["needs_install"] is True
    assert "playwright install chromium" in str(result["command"])
