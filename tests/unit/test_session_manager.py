"""Unit tests for collection session manager and selector constants."""

from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import src.collection.session_manager as session_module
from src.collection.fiverr_selectors import (
    GIG_CARD_TITLE,
    GIG_DETAIL_TITLE,
    LOGGED_IN_INDICATOR,
    SEARCH_RESULT_COUNT,
    SELLER_LEVEL_BADGE,
)
from src.collection.human_events import attach_human_events, random_user_agent, random_viewport
from src.collection.session_manager import SessionLoginError, SessionManager


def _run(coro):
    return asyncio.run(coro)


def test_session_manager_init(tmp_path: Path) -> None:
    config = {
        "fiverr": {"session_file": str(tmp_path / "session.json"), "login_url": "https://www.fiverr.com/login"},
        "collection": {"pacing": {}},
    }
    sm = SessionManager(config)
    assert sm.config is config
    assert sm.session_file == tmp_path / "session.json"
    assert sm._pages_open == 0
    assert sm._verified is False


def test_selectors_constants_present() -> None:
    values = [
        LOGGED_IN_INDICATOR,
        SEARCH_RESULT_COUNT,
        GIG_CARD_TITLE,
        GIG_DETAIL_TITLE,
        SELLER_LEVEL_BADGE,
    ]
    assert all(isinstance(value, str) and value for value in values)


def test_random_viewport_returns_dict() -> None:
    viewport = random_viewport()
    assert isinstance(viewport, dict)
    assert "width" in viewport and "height" in viewport


def test_random_user_agent_returns_string() -> None:
    user_agent = random_user_agent()
    assert isinstance(user_agent, str)
    assert user_agent.strip() != ""


def test_attach_human_events_no_crash() -> None:
    page = MagicMock()
    attach_human_events(page, {})


def test_close_cleans_resources() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    calls: list[str] = []
    sm._context = MagicMock()
    sm._context.close = AsyncMock(side_effect=lambda: calls.append("context"))
    sm._browser = MagicMock()
    sm._browser.close = AsyncMock(side_effect=lambda: calls.append("browser"))
    sm._playwright = MagicMock()
    sm._playwright.stop = AsyncMock(side_effect=lambda: calls.append("playwright"))

    _run(sm.close())
    assert calls == ["context", "browser", "playwright"]
    assert sm._context is None
    assert sm._browser is None
    assert sm._playwright is None


def test_new_page_increments_counter() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}, "collection": {"pacing": {}}})
    page = MagicMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    sm._get_context = AsyncMock(return_value=context)

    created = _run(sm.new_page())
    assert created is page
    assert sm._pages_open == 1


def test_close_page_decrements_counter() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._pages_open = 2
    page = MagicMock()
    page.close = AsyncMock()

    _run(sm.close_page(page))
    assert sm._pages_open == 1


def test_headed_login_flow_does_not_require_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda _path, _mode: None)

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

    sm._verify_session_on_page = AsyncMock(return_value=True)
    sm._load_session_headless = AsyncMock(return_value=MagicMock())
    _run(sm._headed_login_flow())


def test_load_or_login_no_session_file() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/not-there.json"}})
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())
    sm._load_session_headless = AsyncMock()

    _run(sm._load_or_login())
    sm._headed_login_flow.assert_awaited_once()
    sm._load_session_headless.assert_not_called()


def test_load_or_login_no_session_file_login_disabled_raises() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/not-there.json"}})
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())

    with pytest.raises(SessionLoginError):
        _run(sm._load_or_login(allow_login=False))

    sm._headed_login_flow.assert_not_awaited()


def test_load_or_login_session_expired(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})
    context = MagicMock()
    context.close = AsyncMock()
    sm._browser = MagicMock()
    sm._browser.close = AsyncMock()
    sm._load_session_headless = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=False)
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())
    browser = sm._browser

    _run(sm._load_or_login())
    sm._verify_session.assert_awaited_once_with(context)
    context.close.assert_awaited_once()
    assert browser is not None
    browser.close.assert_awaited_once()
    sm._headed_login_flow.assert_awaited_once()


def test_verify_session_success() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://www.fiverr.com/"
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html>ok</html>")
    page.query_selector = AsyncMock(side_effect=[MagicMock()])
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)

    result = _run(sm._verify_session(context))
    assert result is True


def test_verify_session_failure() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/"
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html>not fiverr</html>")
    page.query_selector = AsyncMock(side_effect=[None, None])
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)

    result = _run(sm._verify_session(context))
    assert result is False


def test_context_manager_enter_exit() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._initialize = AsyncMock()
    sm.close = AsyncMock()

    async def _exercise() -> None:
        async with sm:
            pass

    _run(_exercise())
    sm._initialize.assert_awaited_once()
    sm.close.assert_awaited_once()


def test_verify_session_uses_fallback_selector() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/"
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html>not fiverr</html>")
    page.query_selector = AsyncMock(side_effect=[None, MagicMock()])
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)

    result = _run(sm._verify_session(context))
    assert result is True
    assert page.query_selector.await_count == 2


def test_force_relogin_sets_context() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    new_context = MagicMock()
    sm.close = AsyncMock()
    sm._headed_login_flow = AsyncMock(return_value=new_context)

    _run(sm.force_relogin())
    sm.close.assert_awaited_once()
    assert sm._context is new_context


def test_is_session_valid_handles_exceptions() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._get_context = AsyncMock(side_effect=RuntimeError("boom"))
    assert _run(sm.is_session_valid()) is False


def test_is_session_valid_does_not_trigger_login_flow(tmp_path: Path) -> None:
    session_path = tmp_path / "missing_session.json"
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})
    sm._headed_login_flow = AsyncMock(return_value=MagicMock())
    sm._verify_session = AsyncMock(return_value=True)

    assert _run(sm.is_session_valid()) is False
    sm._headed_login_flow.assert_not_awaited()
    sm._verify_session.assert_not_awaited()


def test_is_session_valid_true() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    context = MagicMock()
    sm._get_context = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=True)
    assert _run(sm.is_session_valid()) is True


def test_initialize_idempotent_when_context_exists() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._context = MagicMock()
    sm._load_or_login = AsyncMock()
    _run(sm._initialize())
    sm._load_or_login.assert_not_called()


def test_initialize_sets_context() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    context = MagicMock()
    sm._load_or_login = AsyncMock(return_value=context)
    _run(sm._initialize())
    assert sm._context is context


def test_get_context_initializes_when_missing() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    context = MagicMock()
    sm._load_or_login = AsyncMock(return_value=context)
    assert _run(sm._get_context()) is context


def test_get_context_raises_when_initialization_fails() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    sm._load_or_login = AsyncMock(return_value=None)
    with pytest.raises(RuntimeError, match="Session context initialization failed"):
        _run(sm._get_context())


def test_load_or_login_returns_valid_existing_session(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})
    context = MagicMock()
    sm._load_session_headless = AsyncMock(return_value=context)
    sm._verify_session = AsyncMock(return_value=True)

    result = _run(sm._load_or_login())
    assert result is context
    assert sm._verified is True


def test_verify_session_timeout_returns_false() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.goto = AsyncMock(side_effect=session_module.PlaywrightTimeoutError("timeout"))
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    assert _run(sm._verify_session(context)) is False


def test_verify_session_playwright_error_returns_false() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.goto = AsyncMock(side_effect=session_module.PlaywrightError("playwright"))
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)
    assert _run(sm._verify_session(context)) is False


def test_verify_session_on_page_handles_exception() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.query_selector = AsyncMock(side_effect=RuntimeError("oops"))
    assert _run(sm._verify_session_on_page(page)) is False


def test_verify_session_on_page_uses_fallback() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/profile"
    page.content = AsyncMock(return_value="<html>fallback check</html>")
    page.query_selector = AsyncMock(side_effect=[None, MagicMock()])
    assert _run(sm._verify_session_on_page(page)) is True


def test_browser_args_and_context_options_shape() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    args = sm._browser_args()
    options = sm._context_options()
    assert "--disable-blink-features=AutomationControlled" in args
    assert "--disable-extensions" not in args
    assert options["locale"] == "en-US"
    assert isinstance(options["viewport"], dict)


def test_cfg_supports_attribute_and_model_dump() -> None:
    class PacingModel:
        def model_dump(self):
            return {"pacing": {"delay": 1}}

    class ConfigObject:
        fiverr = type("FiverrCfg", (), {"session_file": "data/sessions/fiverr_session.json"})()
        collection = PacingModel()

    sm = SessionManager(ConfigObject())
    assert sm._cfg("fiverr.session_file") == "data/sessions/fiverr_session.json"
    assert sm._cfg("collection.pacing.delay") == 1
    assert sm._cfg("unknown.value", "fallback") == "fallback"


def test_cfg_model_dump_missing_key_returns_default() -> None:
    class ModelOnly:
        def model_dump(self):
            return {"present": 1}

    class ConfigObject:
        nested = ModelOnly()

    sm = SessionManager(ConfigObject())
    assert sm._cfg("nested.missing", "fallback") == "fallback"


def test_load_session_headless_uses_async_playwright(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})

    context = MagicMock()
    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    chromium = MagicMock()
    chromium.launch = AsyncMock(return_value=browser)
    playwright_instance = MagicMock()
    playwright_instance.chromium = chromium

    starter = MagicMock()
    starter.start = AsyncMock(return_value=playwright_instance)
    monkeypatch.setattr(session_module, "async_playwright", lambda: starter)

    loaded = _run(sm._load_session_headless())
    assert loaded is context
    chromium.launch.assert_awaited_once()
    browser.new_context.assert_awaited_once()


def test_load_session_headless_reuses_existing_playwright(tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    session_path.write_text("{}", encoding="utf-8")
    sm = SessionManager({"fiverr": {"session_file": str(session_path)}})

    context = MagicMock()
    browser = MagicMock()
    browser.new_context = AsyncMock(return_value=context)
    chromium = MagicMock()
    chromium.launch = AsyncMock(return_value=browser)
    playwright_instance = MagicMock()
    playwright_instance.chromium = chromium
    sm._playwright = playwright_instance

    loaded = _run(sm._load_session_headless())
    assert loaded is context
    assert sm._playwright is playwright_instance
    chromium.launch.assert_awaited_once()
    browser.new_context.assert_awaited_once()


def test_headed_login_flow_success_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(
        {
            "fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"},
            "playwright": {"require_login": True},
        }
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda _path, _mode: None)

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

    sm._verify_session_on_page = AsyncMock(return_value=True)
    loaded_context = MagicMock()
    sm._load_session_headless = AsyncMock(return_value=loaded_context)

    result = _run(sm._headed_login_flow())
    assert result is loaded_context
    context.storage_state.assert_awaited_once()


def test_headed_login_flow_chmod_oserror(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(
        {
            "fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"},
            "playwright": {"require_login": True},
        }
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("nope")))

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

    sm._verify_session_on_page = AsyncMock(return_value=True)
    sm._load_session_headless = AsyncMock(return_value=MagicMock())
    _run(sm._headed_login_flow())
    context.storage_state.assert_awaited_once()


def test_headed_login_flow_saves_without_verify_loop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager(
        {
            "fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"},
            "playwright": {"require_login": True},
        }
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda _path, _mode: None)

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
    sm._load_session_headless = AsyncMock(return_value=MagicMock())

    _run(sm._headed_login_flow())
    context.storage_state.assert_awaited_once()


def test_verify_session_returns_false_when_redirected_to_login() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://www.fiverr.com/login"
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html>login</html>")
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)

    assert _run(sm._verify_session(context)) is False


def test_verify_session_treats_pxcr_as_valid_session() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://www.fiverr.com/"
    page.goto = AsyncMock()
    page.content = AsyncMock(return_value="<html>PXCR challenge</html>")
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)

    assert _run(sm._verify_session(context)) is True


def test_headed_login_flow_falls_back_when_chrome_channel_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager({"fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"}})
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(session_module.os, "chmod", lambda _path, _mode: None)

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
    chromium.launch = AsyncMock(side_effect=[RuntimeError("missing chrome"), browser])
    playwright_instance = MagicMock()
    playwright_instance.chromium = chromium
    starter = MagicMock()
    starter.start = AsyncMock(return_value=playwright_instance)
    monkeypatch.setattr(session_module, "async_playwright", lambda: starter)

    sm._verify_session_on_page = AsyncMock(return_value=True)
    sm._load_session_headless = AsyncMock(return_value=MagicMock())

    _run(sm._headed_login_flow())

    assert chromium.launch.await_count == 2
    first_call = chromium.launch.await_args_list[0]
    assert first_call.kwargs.get("channel") == "chrome"


def test_headed_login_flow_verify_branch_chmod_oserror(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager({"fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"}})
    monkeypatch.setattr("builtins.input", lambda _prompt: "")
    monkeypatch.setattr(
        session_module.os,
        "chmod",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("chmod denied")),
    )

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

    sm._verify_session_on_page = AsyncMock(return_value=True)
    loaded_context = MagicMock()
    sm._load_session_headless = AsyncMock(return_value=loaded_context)

    assert _run(sm._headed_login_flow()) is loaded_context
    context.storage_state.assert_awaited_once()


def test_headed_login_flow_raises_with_last_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    session_path = tmp_path / "fiverr_session.json"
    sm = SessionManager({"fiverr": {"session_file": str(session_path), "login_url": "https://www.fiverr.com/login"}})
    monkeypatch.setattr("builtins.input", lambda _prompt: "")

    page = MagicMock()
    page.goto = AsyncMock(side_effect=RuntimeError("goto failed"))
    page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=page)
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

    with pytest.raises(SessionLoginError) as exc_info:
        _run(sm._headed_login_flow())

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert chromium.launch.await_count == session_module.MAX_LOGIN_ATTEMPTS


def test_verify_session_on_page_login_url_fails() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://www.fiverr.com/login"
    page.content = AsyncMock(return_value="<html>login</html>")

    assert _run(sm._verify_session_on_page(page)) is False


def test_verify_session_on_page_pxcr_returns_true() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/challenge"
    page.content = AsyncMock(return_value="<html>PXCR</html>")

    assert _run(sm._verify_session_on_page(page)) is True


def test_verify_session_on_page_url_success_without_selectors() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://www.fiverr.com/dashboard"
    page.content = AsyncMock(return_value="<html>dashboard</html>")

    assert _run(sm._verify_session_on_page(page)) is True


def test_verify_session_on_page_title_fallback_success() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/profile"
    page.content = AsyncMock(return_value="<html>fallback</html>")
    page.query_selector = AsyncMock(side_effect=[None, None])
    page.title = AsyncMock(return_value="Fiverr dashboard")

    assert _run(sm._verify_session_on_page(page)) is True


def test_verify_session_on_page_title_fallback_failure() -> None:
    sm = SessionManager({"fiverr": {"session_file": "data/sessions/fiverr_session.json"}})
    page = MagicMock()
    page.url = "https://example.com/profile"
    page.content = AsyncMock(return_value="<html>fallback</html>")
    page.query_selector = AsyncMock(side_effect=[None, None])
    page.title = AsyncMock(return_value="Login required")

    assert _run(sm._verify_session_on_page(page)) is False
