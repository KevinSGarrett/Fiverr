from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from automation.codex_thread_reader import (
    CodexDispositionResult,
    CodexThread,
    _classify_body,
    read_threads,
    write_disposition_report,
)


def test_summary_empty_threads_is_pass() -> None:
    result = CodexDispositionResult(pr_number=123)
    assert "PASS" in result.summary()


def test_summary_includes_blocked_message() -> None:
    result = CodexDispositionResult(
        pr_number=123,
        threads=[CodexThread("1", False, False, "bot", "needs fix", "UNCLASSIFIED")],
        merge_blocked=True,
    )
    text = result.summary()
    assert "MERGE BLOCKED" in text


def test_classify_body_categories() -> None:
    assert _classify_body("this is not applicable") == "NOT_APPLICABLE"
    assert _classify_body("false positive scanner noise") == "FALSE_POSITIVE"
    assert _classify_body("duplicate issue already tracked") == "DUPLICATE"
    assert _classify_body("fixed in latest commit") == "VALID_FIXED"
    assert _classify_body("critical blocker must fix") == "VALID_DEFERRED_BLOCKER"
    assert _classify_body("misc note") == "UNCLASSIFIED"


def test_read_threads_returns_empty_when_gh_fails() -> None:
    with patch("automation.codex_thread_reader.subprocess.run") as run:
        run.return_value = MagicMock(returncode=1, stdout="")
        result = read_threads(321)
    assert result.threads == []
    assert result.merge_blocked is False


def test_read_threads_parses_reviews_and_ignores_github_actions() -> None:
    payload = {
        "reviews": [
            {"id": "r1", "state": "COMMENTED", "body": "fixed now", "author": {"login": "alice"}},
            {"id": "r2", "state": "COMMENTED", "body": "critical blocker", "author": {"login": "bob"}},
            {"id": "r3", "state": "COMMENTED", "body": "noise", "author": {"login": "github-actions"}},
        ]
    }
    with patch("automation.codex_thread_reader.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout=json.dumps(payload))
        result = read_threads(123)
    assert len(result.threads) == 2
    assert any(t.classification == "VALID_FIXED" for t in result.threads)
    assert any(t.classification == "VALID_DEFERRED_BLOCKER" for t in result.threads)
    assert result.merge_blocked is True


def test_read_threads_marks_all_resolved_when_dismissed() -> None:
    payload = {
        "reviews": [
            {"id": "r1", "state": "DISMISSED", "body": "fixed", "author": {"login": "alice"}},
            {"id": "r2", "state": "DISMISSED", "body": "duplicate", "author": {"login": "bob"}},
        ]
    }
    with patch("automation.codex_thread_reader.subprocess.run") as run:
        run.return_value = MagicMock(returncode=0, stdout=json.dumps(payload))
        result = read_threads(123)
    assert result.all_resolved is True
    assert result.merge_blocked is False


def test_read_threads_exception_path_records_error() -> None:
    with patch("automation.codex_thread_reader.subprocess.run", side_effect=RuntimeError("boom")):
        result = read_threads(123)
    assert result.disposition_table
    assert "error" in result.disposition_table[0]


def test_write_disposition_report_writes_expected_json(tmp_path: Path) -> None:
    result = CodexDispositionResult(
        pr_number=123,
        threads=[CodexThread("t1", True, False, "alice", "fixed", "VALID_FIXED")],
        blockers=[],
        all_resolved=True,
        merge_blocked=False,
        disposition_table=[{"thread_id": "t1", "resolved": True, "category": "VALID_FIXED"}],
    )
    out = write_disposition_report(result, tmp_path)
    assert out.exists()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["pr_number"] == 123
    assert payload["thread_count"] == 1
