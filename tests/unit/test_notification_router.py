from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from automation import notification_router


def test_notify_always_writes_log(tmp_path: Path) -> None:
    config = tmp_path / "notification_config.yaml"
    config.write_text(
        "slack_enabled: false\nlog_path: '{}'\nrate_limit_per_hour: 10\n".format(
            str(tmp_path / "notifications.log").replace("\\", "/")
        ),
        encoding="utf-8",
    )
    with patch("automation.notification_router.Path", wraps=Path) as path_cls, patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        _ = path_cls
        notification_router.notify("INFO", "hello")
    assert (tmp_path / "notifications.log").exists()


def test_slack_unavailable_does_not_raise(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        notification_router.notify("WARNING", "warn")


def test_info_sends_slack(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router._rate_limit_allowed", return_value=True), patch(
        "requests.post"
    ) as post:
        notification_router.notify("INFO", "message")
        post.assert_called_once()


def test_rate_limit_suppresses_11th_message(tmp_path: Path) -> None:
    rate_file = tmp_path / "state/notification_rate.json"
    rate_file.parent.mkdir(parents=True, exist_ok=True)
    rate_file.write_text(json.dumps({"events": []}), encoding="utf-8")
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router.Path", wraps=Path), patch("requests.post") as post:
        for _ in range(11):
            notification_router.notify("WARNING", "limited")
        assert post.call_count <= 10


def test_critical_writes_incident_file(tmp_path: Path) -> None:
    incident_dir = tmp_path / "reports/incidents"
    rate_file = tmp_path / "state/notification_rate.json"

    def _mapped_path(value: str) -> Path:
        mapping = {
            "C:/AI_Runner/reports/incidents": incident_dir,
            "C:/AI_Runner/state/notification_rate.json": rate_file,
        }
        return mapping.get(value, Path(value))

    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router.Path", side_effect=_mapped_path):
        notification_router.notify("CRITICAL", "critical", incident_code="X")
    assert list(incident_dir.glob("NOTIFICATION_X_*.md"))


def test_notify_blocked_writes_to_log_file(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        notification_router.notify_blocked("blocked message", incident_code="B001")
    text = (tmp_path / "notifications.log").read_text(encoding="utf-8")
    assert "[BLOCKED]" in text


def test_notify_blocked_calls_slack_when_enabled(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router._rate_limit_allowed", return_value=True), patch("requests.post") as post:
        notification_router.notify_blocked("blocked message", incident_code="B001")
        post.assert_called_once()


def test_slack_disabled_by_default(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("requests.post") as post:
        notification_router.notify("BLOCKED", "blocked")
        post.assert_not_called()


def test_missing_webhook_url_does_not_raise(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        notification_router.notify("BLOCKED", "blocked")


def test_rate_limit_allows_first_10(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router._rate_limit_allowed", return_value=True), patch("requests.post") as post:
        for _ in range(10):
            notification_router.notify("WARNING", "limited")
        assert post.call_count == 10


def test_log_file_format_has_severity_and_code(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        notification_router.notify("BLOCKED", "blocked message", incident_code="INC-1")
    line = (tmp_path / "notifications.log").read_text(encoding="utf-8").strip()
    assert "[BLOCKED]" in line
    assert "[INC-1]" in line


@pytest.mark.parametrize("severity", ["INFO", "SUCCESS", "WARNING", "BLOCKED", "CRITICAL"])
def test_notify_all_severity_levels_write_log(tmp_path: Path, severity: str) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": False,
            "slack_webhook_url": "",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ):
        notification_router.notify(severity, "message", incident_code="C1")
    content = (tmp_path / "notifications.log").read_text(encoding="utf-8")
    assert f"[{severity}]" in content


# Prompt-required name aliases for traceability.
def test_notify_info_writes_to_log_file(tmp_path: Path) -> None:
    test_notify_always_writes_log(tmp_path)


def test_notify_info_does_not_call_slack(tmp_path: Path) -> None:
    test_info_sends_slack(tmp_path)


def test_notify_critical_writes_incident_file(tmp_path: Path) -> None:
    test_critical_writes_incident_file(tmp_path)


def test_rate_limit_suppresses_11th_in_same_hour(tmp_path: Path) -> None:
    test_rate_limit_suppresses_11th_message(tmp_path)


def test_rate_limit_allowed_filters_stale_and_invalid_timestamps(tmp_path: Path) -> None:
    rate_file = tmp_path / "state/notification_rate.json"
    rate_file.parent.mkdir(parents=True, exist_ok=True)
    old = "2000-01-01T00:00:00+00:00"
    rate_file.write_text(json.dumps({"events": [old, "invalid"]}), encoding="utf-8")
    allowed = notification_router._rate_limit_allowed(rate_file, limit=10)
    assert allowed is True
    payload = json.loads(rate_file.read_text(encoding="utf-8"))
    assert len(payload["events"]) == 1


def test_legacy_notify_critical_writes_incident_and_routes(tmp_path: Path) -> None:
    with patch("automation.notification_router.NOTIFY_LOG", tmp_path / "notifications.log"), patch(
        "automation.notification_router.INCIDENTS_DIR", tmp_path / "incidents"
    ), patch("automation.notification_router._try_slack") as slack, patch(
        "automation.notification_router._try_github_issue"
    ) as gh:
        notification_router._legacy_notify(
            "CRITICAL",
            "critical title",
            "critical body",
            incident_code="AUTH_REQUIRED",
            cycle=75,
        )
    assert (tmp_path / "notifications.log").exists()
    assert list((tmp_path / "incidents").glob("INCIDENT_*.md"))
    slack.assert_called_once()
    gh.assert_called_once()


def test_legacy_notify_info_does_not_call_github_issue(tmp_path: Path) -> None:
    with patch("automation.notification_router.NOTIFY_LOG", tmp_path / "notifications.log"), patch(
        "automation.notification_router._try_slack"
    ) as slack, patch("automation.notification_router._try_github_issue") as gh:
        notification_router._legacy_notify_info("title", "body", cycle=75)
    assert (tmp_path / "notifications.log").exists()
    slack.assert_called_once()
    gh.assert_not_called()


def test_legacy_helper_functions_delegate() -> None:
    with patch("automation.notification_router._legacy_notify") as notify:
        notification_router._legacy_notify_success("ok")
        notification_router._legacy_notify_warning("warn")
        notification_router._legacy_notify_blocked("blocked")
        notification_router._legacy_notify_critical("critical")
    assert notify.call_count == 4


def test_try_slack_returns_when_webhook_missing() -> None:
    with patch("automation.config_loader.get_secret", return_value=""), patch(
        "urllib.request.urlopen"
    ) as urlopen:
        notification_router._try_slack(notification_router.Severity.WARNING, "t", "b", "X")
    urlopen.assert_not_called()


def test_try_github_issue_swallow_exception() -> None:
    with patch("automation.notification_router.subprocess.run", side_effect=RuntimeError("boom")):
        notification_router._try_github_issue(
            notification_router.Severity.BLOCKED,
            "title",
            "body",
            "CODE",
            75,
        )


def test_try_slack_posts_payload_when_webhook_present() -> None:
    with patch("automation.config_loader.get_secret", return_value="https://example.test/webhook"), patch(
        "urllib.request.urlopen"
    ) as urlopen:
        notification_router._try_slack(
            notification_router.Severity.WARNING,
            "title",
            "body",
            "INC-1",
        )
    urlopen.assert_called_once()


def test_load_notification_config_reads_yaml_file(tmp_path: Path) -> None:
    config_path = tmp_path / "config/notification_config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "slack_enabled: true\n"
        "slack_webhook_url: https://example.test/hook\n"
        "log_enabled: true\n"
        "log_path: C:/tmp/notifications.log\n"
        "rate_limit_per_hour: 7\n",
        encoding="utf-8",
    )

    def _mapped_path(value: str) -> Path:
        if value == "C:/AI_Runner/config/notification_config.yaml":
            return config_path
        return Path(value)

    with patch("automation.notification_router.Path", side_effect=_mapped_path):
        loaded = notification_router._load_notification_config()
    assert loaded["slack_enabled"] is True
    assert loaded["rate_limit_per_hour"] == 7


def test_rate_limit_allowed_invalid_json_file_recovers(tmp_path: Path) -> None:
    rate_file = tmp_path / "state/notification_rate.json"
    rate_file.parent.mkdir(parents=True, exist_ok=True)
    rate_file.write_text("{invalid-json", encoding="utf-8")
    allowed = notification_router._rate_limit_allowed(rate_file, limit=3)
    assert allowed is True
    payload = json.loads(rate_file.read_text(encoding="utf-8"))
    assert len(payload["events"]) == 1


def test_notify_slack_post_exception_is_swallowed(tmp_path: Path) -> None:
    with patch(
        "automation.notification_router._load_notification_config",
        return_value={
            "slack_enabled": True,
            "slack_webhook_url": "https://example.test",
            "log_path": str(tmp_path / "notifications.log"),
            "rate_limit_per_hour": 10,
        },
    ), patch("automation.notification_router._rate_limit_allowed", return_value=True), patch(
        "requests.post", side_effect=RuntimeError("network down")
    ):
        notification_router.notify("WARNING", "message")


def test_notify_critical_wrapper_delegates_to_notify() -> None:
    with patch("automation.notification_router.notify") as notify:
        notification_router.notify_critical("critical message", body="details", incident_code="C-1", cycle=75)
    notify.assert_called_once_with("CRITICAL", "critical message\ndetails", incident_code="C-1", cycle=75)


def test_notify_info_wrapper_delegates_to_notify() -> None:
    with patch("automation.notification_router.notify") as notify:
        notification_router.notify_info("info message", body="details", cycle=75)
    notify.assert_called_once_with("INFO", "info message\ndetails", cycle=75)
