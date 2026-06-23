"""The autonomous runner's own PR title+body MUST pass its required 'Validate PR' check
(.github/workflows/pr-checks.yml). The old defaults ("[C084] Autonomous runner cycle 084"
+ a ~24-char body) failed the conventional-commit regex AND the >=50-char body rule, so
every PR the loop opened was rejected and could never merge — the runner could not
self-merge at all (the operator merged manually all session). These tests pin the defaults
to CI's exact rules, parsed from pr-checks.yml so they can't drift.
"""
from __future__ import annotations

import pathlib
import re
import types

import automation.pr_builder as pb

_PR_CHECKS = pathlib.Path(__file__).resolve().parents[2] / ".github/workflows/pr-checks.yml"


def _ci_title_regex() -> re.Pattern:
    txt = _PR_CHECKS.read_text(encoding="utf-8")
    m = re.search(r"const pattern = /(.+)/;", txt)
    assert m, "could not find the title regex in pr-checks.yml"
    return re.compile(m.group(1))


def _capture_create_pr(monkeypatch) -> dict:
    captured: dict = {}

    def _fake_run(args, **kwargs):
        captured["args"] = list(args)
        return types.SimpleNamespace(
            returncode=0,
            stdout="https://github.com/KevinSGarrett/Fiverr/pull/1",
            stderr="",
        )

    monkeypatch.setattr("subprocess.run", _fake_run)
    pb.create_pr(cycle=84, branch="cycle/084/integration", base="develop")
    args = captured["args"]
    title = args[args.index("--title") + 1]
    body = args[args.index("--body") + 1]
    return {"title": title, "body": body}


def test_default_title_passes_ci_regex_and_limits(monkeypatch):
    got = _capture_create_pr(monkeypatch)
    title = got["title"]
    assert _ci_title_regex().match(title), f"title fails CI regex: {title!r}"
    assert len(title) <= 72, f"title too long ({len(title)}): {title!r}"
    assert not title.endswith("."), "title must not end with a period"


def test_default_body_meets_min_length(monkeypatch):
    got = _capture_create_pr(monkeypatch)
    assert len(got["body"].strip()) >= 50, f"body too short: {got['body']!r}"


def test_explicit_title_is_respected(monkeypatch):
    captured: dict = {}

    def _fake_run(args, **kwargs):
        captured["args"] = list(args)
        return types.SimpleNamespace(returncode=0, stdout="https://x/pull/2", stderr="")

    monkeypatch.setattr("subprocess.run", _fake_run)
    pb.create_pr(cycle=84, branch="b", base="develop", title="feat(x): explicit", body="x" * 60)
    args = captured["args"]
    assert args[args.index("--title") + 1] == "feat(x): explicit"
