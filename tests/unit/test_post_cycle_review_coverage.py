"""Coverage tests for post_cycle_review gates and artifact writes."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from automation import post_cycle_review


def test_collect_facts_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo = tmp_path / "repo"
    (repo / "docs/cycle_reports").mkdir(parents=True, exist_ok=True)
    (repo / "data").mkdir(parents=True, exist_ok=True)
    (repo / ".venv/Scripts").mkdir(parents=True, exist_ok=True)
    for agent in ["A", "B", "C", "D", "E", "F"]:
        (repo / f"docs/cycle_reports/CYCLE_077_AGENT_{agent}.md").write_text("ok", encoding="utf-8")
    (repo / "data/cycle037_live.db").write_text("x", encoding="utf-8")
    (repo / "config.yaml").write_text("scrapfly.enabled: false", encoding="utf-8")

    monkeypatch.setattr(post_cycle_review, "REPO_ROOT", repo)
    monkeypatch.setattr(post_cycle_review, "_git", lambda *a: "sha")
    monkeypatch.setattr(post_cycle_review, "_run_check", lambda cmd: True)

    def fake_gh(*args: str) -> str:
        if args[0:2] == ("pr", "view") and "state,mergeCommit,headRefName" in args:
            return json.dumps({"state": "MERGED", "mergeCommit": {"oid": "msha"}})
        if args[0:2] == ("pr", "view") and "statusCheckRollup" in args:
            return json.dumps(
                {
                    "statusCheckRollup": [
                        {"name": "CI / lint", "conclusion": "success"},
                        {"name": "CI / type-check", "conclusion": "success"},
                        {"name": "CI / tests-coverage", "conclusion": "success"},
                        {"name": "CI / smoke-gates", "conclusion": "success"},
                        {"name": "codecov/project", "conclusion": "success"},
                        {"name": "codecov/patch", "conclusion": "failure"},
                    ]
                }
            )
        raise RuntimeError("unexpected")

    monkeypatch.setattr(post_cycle_review, "_gh", fake_gh)
    fake_requests = SimpleNamespace(
        get=lambda *a, **k: SimpleNamespace(
            status_code=200,
            json=lambda: {"issues": [{"fields": {"status": {"name": "Done"}}}]},
        )
    )
    monkeypatch.setitem(__import__("sys").modules, "requests", fake_requests)
    monkeypatch.setitem(
        __import__("sys").modules,
        "automation.config_loader",
        SimpleNamespace(get_secret=lambda key: "x"),
    )

    facts = post_cycle_review.collect_facts(77, post_cycle_review.ReviewMode.POST_MERGE, 88)
    assert facts.pr_merged is True
    assert facts.ci_passed is True
    assert facts.codecov_project == "SUCCESS"
    assert facts.codecov_patch == "FAILURE"
    assert facts.agent_reports_present["F"] is True
    assert facts.scrapfly_enabled_false is True


def test_run_review_missing_prompt_blocks(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(post_cycle_review, "SOURCE_PROMPT", tmp_path / "missing.md")
    out_dir = tmp_path / "reviews"
    monkeypatch.setattr(post_cycle_review, "REVIEWS_DIR", out_dir)
    result = post_cycle_review.run_review(77, post_cycle_review.ReviewMode.POST_MERGE, 88)
    assert result.result == post_cycle_review.ReviewResult.BLOCKED_SOURCE_PROMPT_MISSING
    assert result.blocks_dispatch is True
    assert any("Source prompt missing" in e for e in result.errors)


def test_run_review_post_agent_preview(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "prompt.md"
    src.write_text("prompt", encoding="utf-8")
    monkeypatch.setattr(post_cycle_review, "SOURCE_PROMPT", src)
    monkeypatch.setattr(post_cycle_review, "REVIEWS_DIR", tmp_path / "reviews")
    monkeypatch.setattr(post_cycle_review, "QUEUE_DIR", tmp_path / "queue")
    monkeypatch.setattr(
        post_cycle_review,
        "collect_facts",
        lambda c, m, p: post_cycle_review.PostCycleFacts(
            cycle=c,
            mode=m,
            pr_merged=False,
            baseline_db_mtime_unchanged=True,
            scrapfly_enabled_false=True,
            agent_reports_present={k: True for k in ["A", "B", "C", "D", "E", "F"]},
        ),
    )
    result = post_cycle_review.run_review(77, post_cycle_review.ReviewMode.POST_AGENT, None)
    assert result.result == post_cycle_review.ReviewResult.DRAFT_UNMERGED_PREVIEW
    assert result.blocks_dispatch is False


def test_run_review_post_merge_claude_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "prompt.md"
    src.write_text("prompt", encoding="utf-8")
    monkeypatch.setattr(post_cycle_review, "SOURCE_PROMPT", src)
    monkeypatch.setattr(post_cycle_review, "REVIEWS_DIR", tmp_path / "reviews")
    monkeypatch.setattr(post_cycle_review, "QUEUE_DIR", tmp_path / "queue")
    base_facts = post_cycle_review.PostCycleFacts(
        cycle=77,
        mode=post_cycle_review.ReviewMode.POST_MERGE,
        pr_merged=True,
        baseline_db_mtime_unchanged=True,
        scrapfly_enabled_false=True,
        agent_reports_present={k: True for k in ["A", "B", "C", "D", "E", "F"]},
    )
    monkeypatch.setattr(post_cycle_review, "collect_facts", lambda *a, **k: base_facts)
    _pass_adapter = SimpleNamespace(
        run_post_cycle_review=lambda **kwargs: SimpleNamespace(
            status="PASS",
            error="",
            request_path=str(tmp_path / "req.md"),
            response_path=str(tmp_path / "resp.md"),
        )
    )
    monkeypatch.setattr(post_cycle_review, "claude_post_cycle_adapter", _pass_adapter)
    result = post_cycle_review.run_review(77, post_cycle_review.ReviewMode.POST_MERGE, 88)
    assert result.result == post_cycle_review.ReviewResult.PASS
    assert result.blocks_dispatch is False

    _blocked_adapter = SimpleNamespace(
        run_post_cycle_review=lambda **kwargs: SimpleNamespace(
            status="BLOCKED", error="x", request_path="", response_path=""
        )
    )
    monkeypatch.setattr(post_cycle_review, "claude_post_cycle_adapter", _blocked_adapter)
    blocked = post_cycle_review.run_review(77, post_cycle_review.ReviewMode.POST_MERGE, 88)
    assert blocked.result == post_cycle_review.ReviewResult.BLOCKED_MODEL_UNVERIFIED
