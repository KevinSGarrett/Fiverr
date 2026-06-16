from __future__ import annotations

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
