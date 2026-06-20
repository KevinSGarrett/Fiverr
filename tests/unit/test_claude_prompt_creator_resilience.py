"""
Unit tests for the PMR (prompt-generation resilience) layer in
automation/claude_prompt_creator.py.

Context: on 2026-06-18 15:31 the autopilot paused with CLAUDE_PM_PARTIAL because
create_agent_prompts_via_claude generated the six agent prompts one-shot with no
retry — a single transient failure (a usage/rate-limit trip after several large
generations, or a per-call timeout) aborted the whole cycle at "partial".

These tests pin the resilience behavior that prevents recurrence:
  * retry-with-backoff   — a transient None is retried, not fatal
  * exponential backoff  — backoff grows and is capped
  * inter-agent spacing  — a pause is inserted between successive generations
  * resume-from-partial  — an already-written substantial prompt is reused
  * preserved contract   — after retries are exhausted, the function still
                           returns a partial dict (None when nothing written),
                           so the controller's SystemExit(1) safety still fires.

Claude is never invoked: _call_claude_pm is monkeypatched, and time.sleep is
stubbed, so the suite is fast and hermetic.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))


def _import_cpc():
    import automation.claude_prompt_creator as cpc
    return cpc


def _patch_common(monkeypatch, cpc, fake_call):
    """Patch out every external/slow dependency and return a list that captures
    the durations passed to time.sleep (so backoff/spacing can be asserted)."""
    monkeypatch.setattr(cpc, "_verify_claude_subscription", lambda: {"passed": True, "probe": "OK"})
    monkeypatch.setattr(cpc, "_build_pm_context", lambda *a, **k: "PMCTX")
    monkeypatch.setattr(cpc, "_build_agent_prompt_request", lambda **k: f"REQ {k.get('agent_id')}")
    monkeypatch.setattr(cpc, "_call_claude_pm", fake_call)
    monkeypatch.setattr(cpc, "_announce_pm_model", lambda *a, **k: None, raising=False)
    # GEN-QUALITY added an in-process validate()->regenerate loop; these tests pin
    # the retry/reuse/spacing layer (not prompt quality), so accept any candidate
    # so the validate step does not trigger an extra regeneration.
    from types import SimpleNamespace as _SNS
    monkeypatch.setattr(cpc, "_validate_generated_prompt",
                        lambda *a, **k: _SNS(passed=True, errors=[]), raising=False)

    # Silence/avoid side effects from the live event bus (local import inside fn).
    import automation.live_events as _le
    monkeypatch.setattr(_le, "emit", lambda *a, **k: None, raising=False)

    # Neutralize the autopilot logger so tests don't write log files or spin threads.
    import automation.autopilot_logger as _L
    for _m in ("section", "info", "warn", "ok", "error", "claude_pm_start", "claude_pm_done"):
        monkeypatch.setattr(_L, _m, lambda *a, **k: None, raising=False)

    class _DummySpinner:
        def __init__(self, *a, **k): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
    monkeypatch.setattr(_L, "Spinner", _DummySpinner, raising=False)

    sleeps: list = []
    import time as _time
    monkeypatch.setattr(_time, "sleep", lambda s: sleeps.append(s))
    return sleeps


def _big(marker: str = "x", lines: int = 600) -> str:
    """A prompt body comfortably over the >500-char success floor."""
    return f"# generated {marker}\n" + (f"{marker} line of content\n" * lines)


class TestResumeFromPartial:
    def test_existing_substantial_prompt_is_reused_not_regenerated(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        a_path = pdir / "CYCLE_085_AGENT_A_PROMPT.md"
        a_path.write_text("# CYCLE 085 — AGENT A PROMPT\n" + ("real content line\n" * 300), encoding="utf-8")
        a_before = a_path.read_text(encoding="utf-8")

        calls: list = []
        def fake_call(agent_id, cycle, request_text):
            calls.append(agent_id)
            return _big("B")
        _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "cycle/085/integration", [], ["A", "B"], pdir)

        assert out is not None and set(out.keys()) == {"A", "B"}
        assert calls == ["B"], "Agent A should be reused (resume-from-partial); only B regenerated"
        assert a_path.read_text(encoding="utf-8") == a_before, "Reused prompt must be left byte-for-byte intact"

    def test_pm_existing_prompt_ok_logic(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        monkeypatch.setattr(cpc, "PM_MIN_PROMPT_CHARS", 2000)

        assert cpc._pm_existing_prompt_ok(tmp_path / "missing.md") is False

        short = tmp_path / "short.md"
        short.write_text("tiny", encoding="utf-8")
        assert cpc._pm_existing_prompt_ok(short) is False

        stub = tmp_path / "stub.md"
        stub.write_text("# Cycle 085 Agent A Prompt\n\n[STUB — populate from PM_Pack ...]\n" + ("x" * 4000), encoding="utf-8")
        assert cpc._pm_existing_prompt_ok(stub) is False, "A long file that is still a [STUB] must not be reused"

        real = tmp_path / "real.md"
        real.write_text("# CYCLE 085 — AGENT A PROMPT\n" + ("real\n" * 1000), encoding="utf-8")
        assert cpc._pm_existing_prompt_ok(real) is True


class TestRetryWithBackoff:
    def test_transient_failure_is_retried_then_succeeds(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 3)

        attempts = {"A": 0}
        def fake_call(agent_id, cycle, request_text):
            attempts[agent_id] += 1
            return None if attempts[agent_id] < 2 else _big("A")  # fail once, then succeed
        sleeps = _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "b", [], ["A"], pdir)

        assert out is not None and set(out.keys()) == {"A"}
        assert attempts["A"] == 2, "Agent A must be retried exactly once before success"
        assert (pdir / "CYCLE_085_AGENT_A_PROMPT.md").exists()
        assert sleeps == [cpc.PM_RETRY_BACKOFF_BASE], "Exactly one backoff sleep between the two attempts"

    def test_backoff_is_exponential_and_capped(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 4)
        monkeypatch.setattr(cpc, "PM_RETRY_BACKOFF_BASE", 10)
        monkeypatch.setattr(cpc, "PM_RETRY_BACKOFF_CAP", 25)
        monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0)

        def fake_call(agent_id, cycle, request_text):
            return None  # never succeeds -> exhausts all attempts
        sleeps = _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "b", [], ["A"], pdir)

        assert out is None, "Nothing written -> returns None (caller halts)"
        # 4 attempts => 3 backoffs: 10, 20, min(40, cap=25) = 25
        assert sleeps == [10, 20, 25]


class TestInterAgentSpacing:
    def test_spacing_inserted_between_agents_not_before_first(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 7)
        monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 3)

        def fake_call(agent_id, cycle, request_text):
            return _big(agent_id)  # all succeed on first attempt
        sleeps = _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "b", [], ["A", "B", "C"], pdir)

        assert out is not None and set(out.keys()) == {"A", "B", "C"}
        assert sleeps == [7, 7], "Spacing fires before B and before C, never before the first agent"


class TestPartialContractPreserved:
    def test_partial_returned_after_retries_exhausted(self, tmp_path, monkeypatch):
        """The single most important guarantee: after retries are exhausted on one
        agent, the function STILL returns the partial dict (so ai_cycle_controller
        raises SystemExit(1) and pauses) rather than silently proceeding."""
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 2)
        monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0)

        calls = {"A": 0, "B": 0}
        def fake_call(agent_id, cycle, request_text):
            calls[agent_id] += 1
            return _big("A") if agent_id == "A" else None  # B always fails
        _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "b", [], ["A", "B"], pdir)

        assert out is not None and set(out.keys()) == {"A"}, "Partial dict with only the succeeded agent"
        assert "B" not in out
        assert calls["A"] == 1
        assert calls["B"] == 2, "Failing agent B must be retried up to PM_MAX_ATTEMPTS before giving up"

    def test_none_returned_when_nothing_written(self, tmp_path, monkeypatch):
        cpc = _import_cpc()
        pdir = tmp_path / "prompts"
        pdir.mkdir()
        monkeypatch.setattr(cpc, "PM_MAX_ATTEMPTS", 2)
        monkeypatch.setattr(cpc, "PM_INTER_AGENT_DELAY", 0)

        def fake_call(agent_id, cycle, request_text):
            return None  # first agent fails -> nothing ever written
        _patch_common(monkeypatch, cpc, fake_call)

        out = cpc.create_agent_prompts_via_claude(85, "b", [], ["A", "B"], pdir)
        assert out is None, "When zero prompts are written the function returns None (not {})"
