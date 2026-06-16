from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from automation import provider_usage_ledger as ledger


def _entry(decision: str, cost: float, provider: str = "openai_api") -> ledger.LedgerEntry:
    return ledger.LedgerEntry(
        decision_id=decision,
        provider=provider,
        task_type="prompt_lint",
        estimated_cost_usd=cost,
        actual_cost_usd=None,
        timestamp="2026-06-15T00:00:00Z",
        cycle="079",
    )


def test_record_call_creates_ledger_on_first_write(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))

    ledger.record_call(_entry("d-1", 1.25))

    assert master_path.exists()
    payload = json.loads(master_path.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert len(payload) == 1


def test_record_call_appends_subsequent_entries(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))

    ledger.record_call(_entry("d-1", 1.0))
    ledger.record_call(_entry("d-2", 2.0))

    payload = json.loads(master_path.read_text(encoding="utf-8"))
    assert len(payload) == 2


def test_ledger_file_remains_valid_json_after_multiple_calls(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))

    ledger.record_call(_entry("d-1", 1.0))
    ledger.record_call(_entry("d-2", 2.0))
    ledger.record_call(_entry("d-3", 3.0))

    parsed = json.loads(master_path.read_text(encoding="utf-8"))
    assert isinstance(parsed, list)
    assert len(parsed) == 3


def test_get_daily_spend_sums_correctly(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))

    ledger.record_call(_entry("d-1", 1.5))
    ledger.record_call(_entry("d-2", 2.0))
    ledger.record_call(_entry("d-3", 9.0, provider="cursorcli"))

    assert ledger.get_daily_spend("openai_api", "20260615") == 3.5


def test_get_daily_spend_returns_zero_when_no_file_exists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(tmp_path / "missing_daily"))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))
    assert ledger.get_daily_spend("openai_api") == 0.0


def test_daily_file_rotates_by_date(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))

    timeline = [
        datetime(2026, 6, 15, 23, 59, tzinfo=UTC),
        datetime(2026, 6, 16, 0, 1, tzinfo=UTC),
    ]
    monkeypatch.setattr(ledger, "_utc_now", lambda: timeline.pop(0))

    ledger.record_call(_entry("d-1", 1.0))
    ledger.record_call(_entry("d-2", 1.0))

    assert (daily_dir / "daily_20260615.json").exists()
    assert (daily_dir / "daily_20260616.json").exists()


def test_get_monthly_spend_aggregates_across_days(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 20, tzinfo=UTC))

    daily_dir.mkdir(parents=True, exist_ok=True)
    (daily_dir / "daily_20260601.json").write_text(
        json.dumps([_entry("x1", 1.0).to_dict(), _entry("x2", 2.0).to_dict()]), encoding="utf-8"
    )
    (daily_dir / "daily_20260602.json").write_text(
        json.dumps([_entry("x3", 3.5).to_dict(), _entry("x4", 1.0, provider="cursorcli").to_dict()]),
        encoding="utf-8",
    )
    (daily_dir / "daily_20260531.json").write_text(
        json.dumps([_entry("x0", 10.0).to_dict()]), encoding="utf-8"
    )

    assert ledger.get_monthly_spend("openai_api") == 6.5


def test_get_monthly_spend_returns_zero_when_no_files_exist(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(tmp_path / "missing_daily"))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 20, tzinfo=UTC))
    assert ledger.get_monthly_spend("openai_api") == 0.0


def test_daily_file_created_in_daily_reports_dir(tmp_path: Path, monkeypatch) -> None:
    master_path = tmp_path / "provider_usage_ledger.json"
    daily_dir = tmp_path / "usage_daily"
    monkeypatch.setenv("PROVIDER_LEDGER_PATH", str(master_path))
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))

    ledger.record_call(_entry("d-1", 0.5))
    assert (daily_dir / "daily_20260615.json").exists()


def test_read_json_falls_back_to_last_payload_for_concatenated_json(tmp_path: Path) -> None:
    payload_path = tmp_path / "broken.json"
    payload_path.write_text('{"entries":[{"estimated_cost_usd":1.0}]} {"entries":[{"estimated_cost_usd":2.0}]}')
    parsed = ledger._read_json(payload_path)
    assert isinstance(parsed, dict)
    assert parsed["entries"][0]["estimated_cost_usd"] == 2.0


def test_read_json_returns_none_when_json_is_unrecoverable(tmp_path: Path) -> None:
    payload_path = tmp_path / "broken.json"
    payload_path.write_text("{this is not valid json")
    assert ledger._read_json(payload_path) is None


def test_get_weekly_spend_zero_no_files(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(tmp_path / "missing"))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))
    assert ledger.get_weekly_spend("openai_api") == 0.0


def test_get_weekly_spend_sums_past_7_days(tmp_path: Path, monkeypatch) -> None:
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    now = datetime(2026, 6, 15, tzinfo=UTC)
    monkeypatch.setattr(ledger, "_utc_now", lambda: now)
    daily_dir.mkdir(parents=True, exist_ok=True)
    for idx, amount in enumerate([1.2, 2.3, 3.4]):
        day_key = (now.date() - timedelta(days=idx)).strftime("%Y%m%d")
        (daily_dir / f"daily_{day_key}.json").write_text(
            json.dumps({"entries": [_entry(f"w-{idx}", amount).to_dict()]}), encoding="utf-8"
        )
    assert ledger.get_weekly_spend("openai_api") == 6.9


def test_get_weekly_spend_excludes_old_files(tmp_path: Path, monkeypatch) -> None:
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    now = datetime(2026, 6, 15, tzinfo=UTC)
    monkeypatch.setattr(ledger, "_utc_now", lambda: now)
    daily_dir.mkdir(parents=True, exist_ok=True)
    in_range = now.date().strftime("%Y%m%d")
    old_key = (now.date() - timedelta(days=9)).strftime("%Y%m%d")
    (daily_dir / f"daily_{in_range}.json").write_text(
        json.dumps({"entries": [_entry("wk-new", 4.0).to_dict()]}), encoding="utf-8"
    )
    (daily_dir / f"daily_{old_key}.json").write_text(
        json.dumps({"entries": [_entry("wk-old", 10.0).to_dict()]}), encoding="utf-8"
    )
    assert ledger.get_weekly_spend("openai_api") == 4.0


def test_get_ledger_summary_returns_all_providers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(tmp_path / "empty"))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))
    summary = ledger.get_ledger_summary()
    assert set(summary) == {"cursorcli", "claudesubscription", "openaiapi", "codexsubscription"}


def test_get_ledger_summary_correct_sums(tmp_path: Path, monkeypatch) -> None:
    daily_dir = tmp_path / "daily"
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(daily_dir))
    now = datetime(2026, 6, 15, tzinfo=UTC)
    monkeypatch.setattr(ledger, "_utc_now", lambda: now)
    daily_dir.mkdir(parents=True, exist_ok=True)
    for date_key, amount in [("20260615", 2.0), ("20260614", 3.0), ("20260601", 4.0)]:
        (daily_dir / f"daily_{date_key}.json").write_text(
            json.dumps({"entries": [_entry(f"sum-{date_key}", amount).to_dict()]}), encoding="utf-8"
        )
    summary = ledger.get_ledger_summary()
    assert summary["openaiapi"]["daily"] == 2.0
    assert summary["openaiapi"]["weekly"] == 5.0
    assert summary["openaiapi"]["monthly"] == 9.0


def test_get_ledger_summary_structure_complete(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROVIDER_DAILY_REPORT_DIR", str(tmp_path / "empty"))
    monkeypatch.setattr(ledger, "_utc_now", lambda: datetime(2026, 6, 15, tzinfo=UTC))
    summary = ledger.get_ledger_summary()
    assert len(summary) == 4
    for provider_totals in summary.values():
        assert set(provider_totals) == {"daily", "weekly", "monthly"}
