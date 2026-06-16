from __future__ import annotations

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
