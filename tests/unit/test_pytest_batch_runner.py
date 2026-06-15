from __future__ import annotations

import subprocess
from pathlib import Path

from automation.pytest_batch_runner import (
    build_batches,
    run_batched_unit_pytest,
)


def test_build_batches_rejects_non_positive_size() -> None:
    try:
        build_batches([], batch_size=0)
    except ValueError as exc:
        assert "batch_size must be > 0" in str(exc)
        return
    raise AssertionError("Expected ValueError for batch_size=0")


def test_run_batched_unit_pytest_marks_keyboard_interrupt_failure(
    tmp_path: Path, monkeypatch
) -> None:
    repo_root = tmp_path / "repo"
    tests_dir = repo_root / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_one.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    def _fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="1 passed\n",
            stderr="KeyboardInterrupt\n",
        )

    monkeypatch.setattr("automation.pytest_batch_runner.subprocess.run", _fake_run)
    result = run_batched_unit_pytest(repo_root=repo_root, batch_size=1, per_batch_timeout_seconds=5)
    assert len(result.batches) == 1
    assert result.batches[0].interrupted is True
    assert result.batches[0].passed is False


def test_run_batched_unit_pytest_collects_pass_counts(tmp_path: Path, monkeypatch) -> None:
    repo_root = tmp_path / "repo"
    tests_dir = repo_root / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    (tests_dir / "test_a.py").write_text("def test_a():\n    assert True\n", encoding="utf-8")
    (tests_dir / "test_b.py").write_text("def test_b():\n    assert True\n", encoding="utf-8")

    def _fake_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="2 passed in 0.01s\n",
            stderr="",
        )

    monkeypatch.setattr("automation.pytest_batch_runner.subprocess.run", _fake_run)
    result = run_batched_unit_pytest(repo_root=repo_root, batch_size=2, per_batch_timeout_seconds=5)
    assert result.all_passed is True
    assert result.total_passed == 2
    assert len(result.batches) == 1
