"""Smoke tests for PM pack loader."""
from __future__ import annotations

from pathlib import Path

from automation.pm_pack_loader import load_file


def test_load_file_reads_repo_relative_path(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    target = repo / "PM_Pack/automation/sample.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("hello", encoding="utf-8")

    content = load_file("PM_Pack/automation/sample.md", repo)
    assert content == "hello"
