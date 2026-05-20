"""Auth-focused unit tests for Fiverr session tooling."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import src.collection.session_manager as session_module
from src.collection.session_manager import SessionLoginError, SessionManager, validate_session_file


def _run(coro):
    return asyncio.run(coro)


def _config(session_path: Path) -> dict[str, object]:
    return {
        "fiverr": {
            "session_file": str(session_path),
            "login_url": "https://www.fiverr.com/login",
        },
        "collection": {"pacing": {}},
    }


def _mock_playwright_stack(monkeypatch: pytest.MonkeyPatch):
    page = MagicMock()
    page.goto = AsyncMock()
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    context.storage_state = AsyncMock()
    context.close = AsyncMock()
    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    browser.close = AsyncMock()
    chromium = MagicMock()
    chromium.launch = AsyncMock(return_value=browser)
    playwright_instance = MagicMock()
    playwright_instance.chromium = chromium
    starter = MagicMock()
    starter.start = AsyncMock(return_value=playwright_instance)
    monkeypatch.setattr(session_module, "async_playwright", lambda: starter)
    return page, context, browser, chromium


def test_headed_login_flow_saves_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(_config(session_path))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    chmod_mock = MagicMock()
    monkeypatch.setattr(session_module.os, "chmod", chmod_mock)
    _page, context, _browser, _chromium = _mock_playwright_stack(monkeypatch)
    sm._verify_session_on_page = AsyncMock(return_value=True)
    loaded_context = MagicMock()
    sm._load_session_headless = AsyncMock(return_value=loaded_context)

    result = _run(sm._headed_login_flow())

    assert result is loaded_context
    context.storage_state.assert_awaited_once_with(path=str(session_path))
    chmod_mock.assert_called_once_with(session_path, 0o600)


def test_headed_login_flow_retries_on_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(_config(session_path))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda _path, _mode: None)
    page, context, _browser, chromium = _mock_playwright_stack(monkeypatch)
    sm._verify_session_on_page = AsyncMock(side_effect=[False, False, True])
    sm._load_session_headless = AsyncMock(return_value=MagicMock())

    _run(sm._headed_login_flow())

    assert chromium.launch.await_count == 3
    assert page.close.await_count == 3
    assert context.close.await_count == 3
    context.storage_state.assert_awaited_once()


def test_headed_login_flow_raises_after_max_attempts(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(_config(session_path))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    _page, context, _browser, chromium = _mock_playwright_stack(monkeypatch)
    sm._verify_session_on_page = AsyncMock(return_value=False)

    with pytest.raises(SessionLoginError, match="Failed to verify Fiverr login"):
        _run(sm._headed_login_flow())

    assert chromium.launch.await_count == 3
    assert context.storage_state.await_count == 0


def test_force_relogin_calls_headed_login() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    relogin_context = MagicMock()
    sm.close = AsyncMock()
    sm._headed_login_flow = AsyncMock(return_value=relogin_context)

    _run(sm.force_relogin())

    sm.close.assert_awaited_once()
    sm._headed_login_flow.assert_awaited_once()
    assert sm._context is relogin_context


def test_is_session_valid_returns_true_when_verified() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    context = MagicMock()
    sm._get_context = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=True)

    assert _run(sm.is_session_valid()) is True


def test_is_session_valid_returns_false_when_exception() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._get_context = AsyncMock(side_effect=RuntimeError("boom"))

    assert _run(sm.is_session_valid()) is False


def test_load_or_login_uses_saved_session(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager(_config(session_path))
    context = MagicMock()
    sm._load_session_headless = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=True)
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())

    result = _run(sm._load_or_login())

    assert result is context
    sm._headed_login_flow.assert_not_awaited()


def test_load_or_login_triggers_login_when_session_expired(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager(_config(session_path))
    context = MagicMock()
    context.close = AsyncMock()
    sm._browser = MagicMock()
    sm._browser.close = AsyncMock()
    sm._load_session_headless = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=False)
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())

    _run(sm._load_or_login())

    context.close.assert_awaited_once()
    sm._headed_login_flow.assert_awaited_once()


def test_load_or_login_triggers_login_when_no_session_file(tmp_path: Path) -> None:
    session_path = tmp_path / "missing_session.json"
    sm = SessionManager(_config(session_path))
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())
    sm._load_session_headless = AsyncMock()

    _run(sm._load_or_login())

    sm._headed_login_flow.assert_awaited_once()
    sm._load_session_headless.assert_not_called()


def test_session_file_permissions_set(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(_config(session_path))
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    chmod_mock = MagicMock()
    monkeypatch.setattr(session_module.os, "chmod", chmod_mock)
    _page, _context, _browser, _chromium = _mock_playwright_stack(monkeypatch)
    sm._verify_session_on_page = AsyncMock(return_value=True)
    sm._load_session_headless = AsyncMock(return_value=MagicMock())

    _run(sm._headed_login_flow())

    chmod_mock.assert_called_once_with(session_path, 0o600)


def test_validate_session_file_missing(tmp_path: Path) -> None:
    result = validate_session_file(tmp_path / "missing_session.json")
    assert result == {
        "exists": False,
        "valid_json": False,
        "has_cookies": False,
        "has_origins": False,
        "path": str(tmp_path / "missing_session.json"),
    }


def test_validate_session_file_valid_json(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text('{"cookies":[{"name":"sid"}],"origins":[{"origin":"https://www.fiverr.com"}]}')
    result = validate_session_file(session_path)
    assert result["exists"] is True
    assert result["valid_json"] is True
    assert result["has_cookies"] is True
    assert result["has_origins"] is True


def test_validate_session_file_invalid_json(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{not-valid-json")
    result = validate_session_file(session_path)
    assert result["exists"] is True
    assert result["valid_json"] is False
    assert result["has_cookies"] is False
    assert result["has_origins"] is False
