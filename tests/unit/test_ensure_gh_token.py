"""Autonomy hardening: _ensure_gh_token falls back to gh's keyring auth.

The 24/7 runner must do PR/merge ops on gh's native `gh auth login` credential when
no PAT env var is exported — otherwise open_cycle_pr fails-closed ("no gh token") on
every cycle even though `gh` itself is authenticated (observed on the live runner:
no runner.env, no GH_AUTOMATION_TOKEN, but `gh auth token` returns a valid token).
"""
from __future__ import annotations

import subprocess

import automation.pr_builder as pb


def _clear_token_env(monkeypatch):
    for k in ("GH_AUTOMATION_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
        monkeypatch.delenv(k, raising=False)


def test_env_token_wins_no_gh_call(monkeypatch):
    """An explicit env token is used directly — no `gh auth token` subprocess."""
    _clear_token_env(monkeypatch)
    monkeypatch.setenv("GH_AUTOMATION_TOKEN", "env-pat-123")
    called = {"n": 0}
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    assert pb._ensure_gh_token() == "env-pat-123"
    assert called["n"] == 0, "must not shell out when an env token is present"


def test_keyring_fallback_when_env_empty(monkeypatch):
    """No env token → fall back to `gh auth token` and export GH_TOKEN."""
    _clear_token_env(monkeypatch)

    def fake_run(args, **kwargs):
        assert args == ["gh", "auth", "token"]
        return subprocess.CompletedProcess(args, 0, stdout="keyring-tok-abc\n", stderr="")
    monkeypatch.setattr(subprocess, "run", fake_run)

    assert pb._ensure_gh_token() == "keyring-tok-abc"
    import os
    assert os.environ.get("GH_TOKEN") == "keyring-tok-abc", "resolved token must be exported"


def test_empty_when_no_env_and_gh_fails(monkeypatch):
    """No env token and `gh auth token` fails → empty string (caller fails closed)."""
    _clear_token_env(monkeypatch)

    def fake_run(args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="not logged in")
    monkeypatch.setattr(subprocess, "run", fake_run)
    assert pb._ensure_gh_token() == ""


def test_empty_when_gh_raises(monkeypatch):
    """`gh` missing/hung (exception) → empty string, never propagates."""
    _clear_token_env(monkeypatch)
    monkeypatch.setattr(subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("gh")))
    assert pb._ensure_gh_token() == ""
