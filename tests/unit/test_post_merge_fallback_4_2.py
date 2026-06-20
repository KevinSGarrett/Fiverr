"""ITEM 4.2 — deterministic POST_MERGE fallback + skip-local-validation + retry.

Proves: a Claude-PM flake cannot strand the runner (deterministic facts are the
PASS floor; Claude is advisory); ANTHROPIC_API_KEY-present STILL hard-blocks
(security stance preserved); the skip_local_validation kwarg no longer crashes
and avoids the 13-min double-suite; bounded retry self-clears transient flakes;
and the pre-merge POST_AGENT dead-end (ci_passed pending) is fixed.

All gh/git/claude/suite seams are mocked — no network, no 13-min run.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from automation import post_cycle_review as pcr
from automation import required_checks
from automation.post_cycle_review import (
    PostCycleFacts,
    PostCycleReviewResult,
    ReviewMode,
    ReviewResult,
)


# ── helpers ───────────────────────────────────────────────────────────────────
def _green_merge_facts(cycle: int = 600) -> PostCycleFacts:
    f = PostCycleFacts(cycle=cycle, mode=ReviewMode.POST_MERGE)
    f.pr_merged = True
    f.merge_sha = "abc1234"
    f.ci_passed = True
    f.local_coverage_pct = 0.0  # rides ci_passed
    f.baseline_db_mtime_unchanged = True
    f.scrapfly_enabled_false = True
    for a in ("A", "B", "E", "C", "F", "D"):
        f.agent_reports_present[a] = True
    return f


def _claude(status: str, error: str = "") -> SimpleNamespace:
    return SimpleNamespace(status=status, error=error, request_path="", response_path="")


# ════════════════ T1: deterministic verdict (pure) ════════════════
def test_det_verdict_all_green_passes():
    ok, reasons = pcr._deterministic_post_merge_verdict(_green_merge_facts())
    assert ok is True and reasons == []


@pytest.mark.parametrize("mutate,reason_substr", [
    (lambda f: setattr(f, "pr_merged", False), "not merged"),
    (lambda f: setattr(f, "merge_sha", ""), "no merge SHA"),
    (lambda f: setattr(f, "ci_passed", False), "CI not green"),
    (lambda f: setattr(f, "baseline_db_mtime_unchanged", False), "baseline"),
    (lambda f: setattr(f, "scrapfly_enabled_false", False), "ScrapFly"),
    (lambda f: f.agent_reports_present.__setitem__("D", False), "missing agent reports"),
])
def test_det_verdict_each_red_fact_blocks(mutate, reason_substr):
    f = _green_merge_facts()
    mutate(f)
    ok, reasons = pcr._deterministic_post_merge_verdict(f)
    assert ok is False
    assert any(reason_substr in r for r in reasons), reasons


def test_det_verdict_unmeasured_coverage_rides_ci():
    f = _green_merge_facts()
    f.local_coverage_pct = 0.0  # unmeasured
    f.ci_passed = True
    ok, _ = pcr._deterministic_post_merge_verdict(f)
    assert ok is True  # CI's --cov-fail-under is the floor authority


def test_det_verdict_ci_red_blocks_even_with_local_coverage():
    f = _green_merge_facts()
    f.ci_passed = False
    f.local_coverage_pct = 95.0
    ok, reasons = pcr._deterministic_post_merge_verdict(f)
    assert ok is False
    assert any("CI not green" in r for r in reasons)


# ════════════════ T2: transient classification + bounded retry ════════════════
def test_is_transient_classification():
    assert pcr._is_transient(_claude("ERROR", "spawn crash")) is True
    assert pcr._is_transient(_claude("ADVISORY_ONLY", "Claude review timed out after 10 minutes")) is True
    assert pcr._is_transient(_claude("ADVISORY_ONLY", "Claude Code binary not found on PATH")) is True
    assert pcr._is_transient(_claude("BLOCKED", "ANTHROPIC_API_KEY present")) is False  # config
    assert pcr._is_transient(_claude("PASS")) is False
    assert pcr._is_transient(_claude("FAIL", "verdict fail")) is False
    assert pcr._is_transient(_claude("ADVISORY_ONLY", "")) is False  # unparseable verdict = real


def _patch_retry_env(monkeypatch, results):
    """Patch the adapter to yield `results` in order; no real sleep."""
    monkeypatch.setattr("time.sleep", lambda *a, **k: None)
    calls = {"n": 0}

    def _adapter(cycle, run_dir, review_prompt_text, facts_json):
        i = calls["n"]
        calls["n"] += 1
        return results[min(i, len(results) - 1)]

    monkeypatch.setattr("automation.claude_post_cycle_adapter.run_post_cycle_review", _adapter)
    monkeypatch.setattr(pcr, "SOURCE_PROMPT", _FakePrompt())
    return calls


class _FakePrompt:
    def read_text(self, *a, **k):
        return "review prompt"

    def exists(self):
        return True


def _result_for_retry(cycle=601) -> PostCycleReviewResult:
    return PostCycleReviewResult(cycle=cycle, mode=ReviewMode.POST_MERGE,
                                 result=ReviewResult.PASS, facts=_green_merge_facts(cycle))


def test_retry_clears_transient(monkeypatch):
    calls = _patch_retry_env(monkeypatch, [_claude("ERROR", "x"), _claude("PASS")])
    res = pcr._run_claude_with_retry(_result_for_retry())
    assert res.status == "PASS"
    assert calls["n"] == 2  # retried once, then cleared


def test_retry_bounded_on_persistent_transient(monkeypatch):
    calls = _patch_retry_env(monkeypatch, [_claude("ERROR", "x")])
    monkeypatch.setattr("yaml.safe_load", lambda *a, **k: {"claude_review": {"max_attempts": 2}})
    res = pcr._run_claude_with_retry(_result_for_retry())
    assert res.status == "ERROR"
    assert calls["n"] == 2  # exactly max_attempts, never more


def test_retry_hard_cap_three(monkeypatch):
    calls = _patch_retry_env(monkeypatch, [_claude("ERROR", "x")])
    monkeypatch.setattr("yaml.safe_load", lambda *a, **k: {"claude_review": {"max_attempts": 99}})
    pcr._run_claude_with_retry(_result_for_retry())
    assert calls["n"] <= 3  # hard cap honored even with a bad config


def test_retry_no_retry_on_real_fail(monkeypatch):
    calls = _patch_retry_env(monkeypatch, [_claude("FAIL", "verdict"), _claude("PASS")])
    res = pcr._run_claude_with_retry(_result_for_retry())
    assert res.status == "FAIL"
    assert calls["n"] == 1  # real verdict -> stop immediately


# ════════════════ T1 wiring: GATE 8 inversion in run_review ════════════════
def _run_post_merge(monkeypatch, facts, claude_result):
    monkeypatch.setattr(pcr, "SOURCE_PROMPT", _FakePrompt())
    monkeypatch.setattr(pcr, "_write_queue_request", lambda *a, **k: None)
    monkeypatch.setattr(pcr, "_write_result", lambda *a, **k: None)
    monkeypatch.setattr(pcr, "collect_facts", lambda *a, **k: facts)
    called = {"claude": 0}

    def _retry(result):
        called["claude"] += 1
        return claude_result

    monkeypatch.setattr(pcr, "_run_claude_with_retry", _retry)
    res = pcr.run_review(cycle=facts.cycle, mode=ReviewMode.POST_MERGE, pr_number=1)
    return res, called


def test_post_merge_green_facts_pass_despite_claude_flake(monkeypatch):
    # The core 4.2 guarantee: a Claude flake CANNOT strand a green merged cycle.
    res, _ = _run_post_merge(monkeypatch, _green_merge_facts(),
                             _claude("ADVISORY_ONLY", "Claude review timed out"))
    assert res.result == ReviewResult.PASS
    assert res.blocks_dispatch is False


def test_post_merge_claude_pass_concurs(monkeypatch):
    res, _ = _run_post_merge(monkeypatch, _green_merge_facts(), _claude("PASS"))
    assert res.result == ReviewResult.PASS
    assert res.blocks_dispatch is False


def test_post_merge_claude_dissent_pass_stands(monkeypatch):
    # Claude says FAIL but facts are green -> deterministic PASS stands (advisory).
    res, _ = _run_post_merge(monkeypatch, _green_merge_facts(), _claude("FAIL", "I disagree"))
    assert res.result == ReviewResult.PASS
    assert res.blocks_dispatch is False
    assert any("DISSENT" in w for w in res.warnings)


def test_post_merge_api_key_present_still_hard_blocks(monkeypatch):
    # SECURITY: ANTHROPIC_API_KEY present is a deterministic policy violation and
    # STILL hard-blocks even on green facts (subscription-only stance preserved).
    res, _ = _run_post_merge(monkeypatch, _green_merge_facts(),
                             _claude("BLOCKED", "ANTHROPIC_API_KEY present"))
    assert res.result == ReviewResult.BLOCKED_MODEL_UNVERIFIED
    assert res.blocks_dispatch is True


def test_post_merge_red_facts_block_and_skip_claude(monkeypatch):
    f = _green_merge_facts()
    f.ci_passed = False  # red
    res, called = _run_post_merge(monkeypatch, f, _claude("PASS"))
    assert res.blocks_dispatch is True
    assert called["claude"] == 0  # Claude not even consulted when facts are red


# ════════════════ T3: skip_local_validation kwarg no longer crashes ════════════
def test_run_review_accepts_skip_kwarg(monkeypatch):
    monkeypatch.setattr(pcr, "SOURCE_PROMPT", _FakePrompt())
    monkeypatch.setattr(pcr, "_write_queue_request", lambda *a, **k: None)
    monkeypatch.setattr(pcr, "_write_result", lambda *a, **k: None)
    monkeypatch.setattr(pcr, "collect_facts",
                        lambda *a, **k: PostCycleFacts(cycle=1, mode=ReviewMode.POST_AGENT))
    # Must NOT raise TypeError (the PCR-02 crash).
    res = pcr.run_review(cycle=1, mode=ReviewMode.POST_AGENT, pr_number=1,
                         skip_local_validation=True)
    assert res is not None


# ════════════════ T4: collect_facts skip derivation + no suite run ════════════
def test_collect_facts_skip_does_not_run_suite(monkeypatch):
    spy = {"suite": 0}
    monkeypatch.setattr(pcr, "_run_local_suite", lambda f: spy.__setitem__("suite", spy["suite"] + 1))
    monkeypatch.setattr(pcr, "_git", lambda *a: "")
    monkeypatch.setattr(pcr, "PostCycleReview", _FakeReviewer)
    facts = pcr.collect_facts(700, ReviewMode.POST_AGENT, pr_number=None,
                              skip_local_validation=True)
    assert spy["suite"] == 0  # the ~13-min suite was NOT run
    assert facts.local_validation_skipped is True
    assert facts.local_ruff and facts.local_mypy and facts.local_pytest
    assert facts.local_coverage_pct == 0.0


def test_collect_facts_no_skip_runs_suite(monkeypatch):
    spy = {"suite": 0}
    monkeypatch.setattr(pcr, "_run_local_suite", lambda f: spy.__setitem__("suite", spy["suite"] + 1))
    monkeypatch.setattr(pcr, "_git", lambda *a: "")
    monkeypatch.setattr(pcr, "PostCycleReview", _FakeReviewer)
    facts = pcr.collect_facts(701, ReviewMode.POST_AGENT, pr_number=None,
                              skip_local_validation=False)
    assert spy["suite"] == 1  # the suite ran
    assert facts.local_validation_skipped is False


class _FakeReviewer:
    def __init__(self, cycle):
        self.cycle = cycle

    def collect_github_facts(self, pr_number=None):
        return {}

    def collect_jira_facts(self, merge_sha=""):
        return {}


# ════════════════ dead-end fix: pre-merge POST_AGENT advances on pending CI ════
def test_pre_merge_post_agent_advances_with_pending_ci(monkeypatch):
    # The real dead-end: delegated validation + CI pending + PR present + clean
    # invariants must NOT block (deferred to AWAITING_CI_GREEN).
    f = PostCycleFacts(cycle=702, mode=ReviewMode.POST_AGENT)
    f.local_validation_skipped = True
    f.local_ruff = f.local_mypy = f.local_pytest = True
    f.ci_passed = False  # PR CI still pending at AGENT_COMPLETE
    f.local_coverage_pct = 0.0
    f.baseline_db_mtime_unchanged = True
    f.scrapfly_enabled_false = True
    f.github_health_score = 100
    f.pr_expected = True
    f.pr_number = 1702  # PR present
    r = PostCycleReviewResult(cycle=702, mode=ReviewMode.POST_AGENT,
                              result=ReviewResult.DRAFT_UNMERGED_PREVIEW, facts=f)
    assert r.blocks_dispatch is False  # advances (CI gated downstream)


# ════════════════ Codex round: canonical ci_passed + scrapfly YAML + suite ════
def _fake_gh_factory(rollup, merged=True, merge_oid="sha9"):
    def _gh(*args):
        joined = " ".join(args)
        if "state,mergeCommit" in joined:
            import json as _j
            return _j.dumps({"state": "MERGED" if merged else "OPEN",
                             "mergeCommit": {"oid": merge_oid}, "headRefName": "b"})
        if "statusCheckRollup" in joined:
            import json as _j
            return _j.dumps({"statusCheckRollup": rollup})
        return "{}"
    return _gh


def _all8_green():
    return [{"name": n, "conclusion": "SUCCESS"} for n in required_checks.REQUIRED_CONTEXTS]


def test_collect_facts_ci_passed_uses_canonical_8(monkeypatch):
    # Codex HIGH: a red NON-subset required check (Secret Scan) must make
    # ci_passed False (the old 5-subset ignored it).
    monkeypatch.setattr(pcr, "_git", lambda *a: "")
    monkeypatch.setattr(pcr, "PostCycleReview", _FakeReviewer)
    monkeypatch.setattr(pcr, "_run_local_suite", lambda f: None)
    monkeypatch.setattr(required_checks, "get_required_contexts",
                        lambda *a, **k: set(required_checks.REQUIRED_CONTEXTS))
    # All green EXCEPT Secret Scan failed:
    rollup = [{"name": n, "conclusion": ("FAILURE" if n == "Secret Scan" else "SUCCESS")}
              for n in required_checks.REQUIRED_CONTEXTS]
    monkeypatch.setattr(pcr, "_gh", _fake_gh_factory(rollup))
    facts = pcr.collect_facts(710, ReviewMode.POST_MERGE, pr_number=5,
                              skip_local_validation=True)
    assert facts.ci_passed is False  # canonical set catches the red Secret Scan

    # All 8 green -> ci_passed True
    monkeypatch.setattr(pcr, "_gh", _fake_gh_factory(_all8_green()))
    facts2 = pcr.collect_facts(711, ReviewMode.POST_MERGE, pr_number=5,
                               skip_local_validation=True)
    assert facts2.ci_passed is True


def test_collect_facts_scrapfly_yaml_not_spoofable(monkeypatch, tmp_path):
    # Codex MEDIUM: scrapfly.enabled:true must set scrapfly_enabled_false=False
    # even when an unrelated `enabled: false` exists elsewhere in the config.
    monkeypatch.setattr(pcr, "_git", lambda *a: "")
    monkeypatch.setattr(pcr, "_gh", lambda *a: "{}")
    monkeypatch.setattr(pcr, "PostCycleReview", _FakeReviewer)
    monkeypatch.setattr(pcr, "_run_local_suite", lambda f: None)
    monkeypatch.setattr(pcr, "REPO_ROOT", tmp_path)
    (tmp_path / "config.yaml").write_text(
        "relevance:\n  llm:\n    enabled: false\nscrapfly:\n  enabled: true\n",
        encoding="utf-8")
    facts = pcr.collect_facts(712, ReviewMode.POST_AGENT, pr_number=None,
                              skip_local_validation=True)
    assert facts.scrapfly_enabled_false is False  # not spoofed by relevance.llm

    (tmp_path / "config.yaml").write_text(
        "relevance:\n  llm:\n    enabled: false\nscrapfly:\n  enabled: false\n",
        encoding="utf-8")
    facts2 = pcr.collect_facts(713, ReviewMode.POST_AGENT, pr_number=None,
                               skip_local_validation=True)
    assert facts2.scrapfly_enabled_false is True


def test_run_local_suite_maps_results(monkeypatch):
    # Codex MEDIUM: the extracted _run_local_suite is exercised directly.
    checks = iter([True, False])  # ruff True, mypy False
    monkeypatch.setattr(pcr, "_run_check", lambda cmd: next(checks))

    class _Cov:
        returncode = 0
        stdout = "TOTAL    100    13    87%\n"
        stderr = ""

    monkeypatch.setattr(pcr.subprocess, "run", lambda *a, **k: _Cov())
    f = PostCycleFacts(cycle=714, mode=ReviewMode.POST_AGENT)
    pcr._run_local_suite(f)
    assert f.local_ruff is True
    assert f.local_mypy is False
    assert f.local_pytest is True       # cov_result returncode 0
    assert f.local_coverage_pct == 87.0  # parsed from TOTAL line


def test_full_review_still_gates_on_ci(monkeypatch):
    # A non-skipped (manual) POST_AGENT review STILL enforces ci_passed locally.
    f = PostCycleFacts(cycle=703, mode=ReviewMode.POST_AGENT)
    f.local_validation_skipped = False
    f.local_ruff = f.local_mypy = f.local_pytest = True
    f.ci_passed = False
    f.baseline_db_mtime_unchanged = True
    f.scrapfly_enabled_false = True
    r = PostCycleReviewResult(cycle=703, mode=ReviewMode.POST_AGENT,
                              result=ReviewResult.DRAFT_UNMERGED_PREVIEW, facts=f)
    assert r.blocks_dispatch is True
