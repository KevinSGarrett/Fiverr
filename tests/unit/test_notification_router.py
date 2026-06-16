from __future__ import annotations

<<<<<<< HEAD
import inspect
from pathlib import Path

import pytest

from automation import notification_router as router


def _router_source() -> str:
    return inspect.getsource(router).lower()


def test_notification_writes_to_local_log(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    notify_log = tmp_path / "notifications"
    monkeypatch.setattr(router, "NOTIFY_LOG", notify_log)
    router.route_notification("INFO", "hello", {"a": 1})
    files = list(notify_log.glob("*.log"))
    assert files
    assert files[0].read_text(encoding="utf-8")


def test_no_slack_references() -> None:
    assert "slack" not in _router_source()


def test_no_webhook_references() -> None:
    assert "webhook" not in _router_source()


def test_notification_router_class_only_routes_blocked_and_above(tmp_path: Path) -> None:
    log_path = tmp_path / "notifications.jsonl"
    notifier = router.NotificationRouter(log_path=log_path)
    notifier.route_notification("INFO", "ignore", {})
    assert not log_path.exists()
    notifier.route_notification("BLOCKED", "persist", {"channel": "local"})
    assert log_path.exists()
    assert "persist" in log_path.read_text(encoding="utf-8")
=======
from automation.notification_router import NotificationRouter


def test_no_webhook_url_no_crash(monkeypatch) -> None:
    monkeypatch.setattr("automation.config_loader.get_secret", lambda *args, **kwargs: "")
    router = NotificationRouter()
    router.send_slack_notification("msg", "#ch", "BLOCKED")


def test_blocked_severity_triggers_post(monkeypatch) -> None:
    called: dict[str, object] = {"count": 0, "url": ""}

    def _fake_post(url: str, json: dict, timeout: int):  # noqa: A002
        called["count"] = int(called["count"]) + 1
        called["url"] = url
        called["json"] = json
        called["timeout"] = timeout

    monkeypatch.setattr("automation.config_loader.get_secret", lambda *args, **kwargs: "http://fake")
    monkeypatch.setattr("requests.post", _fake_post)
    router = NotificationRouter()
    router.route_notification("BLOCKED", "message", {"channel": "#ch"})
    assert called["count"] == 1
    assert called["url"] == "http://fake"


def test_info_severity_no_post_via_route(monkeypatch) -> None:
    called = {"count": 0}

    def _fake_send(*args, **kwargs) -> None:
        _ = args, kwargs
        called["count"] += 1

    router = NotificationRouter()
    monkeypatch.setattr(router, "send_slack_notification", _fake_send)
    router.route_notification("INFO", "message", {"channel": "#ch"})
    assert called["count"] == 0
>>>>>>> origin/develop
