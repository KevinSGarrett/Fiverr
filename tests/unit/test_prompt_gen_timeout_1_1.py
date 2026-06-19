"""Item 1.1 (T4): per-agent prompt-gen timeout has real headroom + is env-tunable.

#103 already added retry/backoff + resume-from-partial (per-agent skip); the
remaining concrete finding was the 480s budget vs a 469s live p100 (1s margin).
"""
from __future__ import annotations

import importlib

from automation import claude_prompt_creator as cpc


def test_timeout_has_headroom_over_live_p100() -> None:
    # Live p100 was 469s; the budget must have real headroom, not a 1s margin.
    assert cpc.CLAUDE_TIMEOUT >= 900
    assert cpc.CLAUDE_TIMEOUT > 469 * 1.5


def test_timeout_is_env_tunable() -> None:
    assert cpc._pm_int_env("CLAUDE_PM_TIMEOUT", 900) == 900


def test_timeout_env_override(monkeypatch) -> None:
    monkeypatch.setenv("CLAUDE_PM_TIMEOUT", "1200")
    mod = importlib.reload(cpc)
    try:
        assert mod.CLAUDE_TIMEOUT == 1200
    finally:
        monkeypatch.delenv("CLAUDE_PM_TIMEOUT", raising=False)
        importlib.reload(mod)


def test_resume_from_partial_helper_present() -> None:
    # #103 resume-from-partial (per-agent skip) must still be in place (1.1-T2).
    assert hasattr(cpc, "_pm_existing_prompt_ok")
    assert cpc.PM_MAX_ATTEMPTS >= 1 and cpc.PM_MIN_PROMPT_CHARS >= 1
