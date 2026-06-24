"""Audit C — model-gate freshness auto-refresh (zero-intervention enabler).

Dispatch forces --model codex-5.3 on every call, so a successful agent run proves the
model works. refresh_verified_at_if_verified() bumps verified_at AFTER such a run, but
ONLY when the state is already a passing VERIFIED config — keeping a 24/7 runner's gate
fresh without a weekly human re-verification, and NEVER false-verifying.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from automation.model_gate import refresh_verified_at_if_verified


def _write(tmp_path, **over):
    base = {
        "status": "VERIFIED",
        "observed_model": "Codex 5.3",
        "observed_effort": "medium",
        "auto_model_disabled": True,
        "verified_at": (datetime.now(UTC) - timedelta(days=6)).isoformat(),
    }
    base.update(over)
    p = tmp_path / "cursor_model_state.json"
    p.write_text(json.dumps(base))
    return p


def test_refreshes_when_already_verified(tmp_path):
    p = _write(tmp_path)
    old = json.loads(p.read_text())["verified_at"]
    assert refresh_verified_at_if_verified(p) is True
    new = json.loads(p.read_text())
    assert new["verified_at"] > old              # timestamp bumped forward
    assert new["status"] == "VERIFIED"           # substance preserved
    assert new["observed_model"] == "Codex 5.3"
    assert new.get("freshness_refreshed_by")


def test_no_refresh_when_not_verified(tmp_path):
    p = _write(tmp_path, status="UNVERIFIED")
    old = json.loads(p.read_text())["verified_at"]
    assert refresh_verified_at_if_verified(p) is False  # cannot bless an unverified state
    assert json.loads(p.read_text())["verified_at"] == old  # untouched


def test_no_refresh_when_auto_enabled(tmp_path):
    p = _write(tmp_path, auto_model_disabled=False)
    assert refresh_verified_at_if_verified(p) is False


def test_no_refresh_on_wrong_model(tmp_path):
    p = _write(tmp_path, observed_model="gpt-4o")
    assert refresh_verified_at_if_verified(p) is False


def test_no_refresh_on_missing_state(tmp_path):
    assert refresh_verified_at_if_verified(tmp_path / "does_not_exist.json") is False
