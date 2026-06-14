"""Run unit tests in small batches to avoid long-session interrupts."""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

_PASSED_RE = re.compile(r"(?P<count>\d+)\s+passed")


@dataclass
class BatchResult:
    """Result for a single pytest batch invocation."""

    index: int
    files: list[Path]
    passed: bool
    exit_code: int
    passed_count: int
    output: str
    interrupted: bool


@dataclass
class BatchedPytestResult:
    """Aggregate result for batched unit test execution."""

    batches: list[BatchResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(batch.passed for batch in self.batches)

    @property
    def total_passed(self) -> int:
        return sum(batch.passed_count for batch in self.batches)

    @property
    def interrupted_batches(self) -> int:
        return sum(1 for batch in self.batches if batch.interrupted)


def discover_unit_test_files(repo_root: Path) -> list[Path]:
    """Return sorted unit test files under tests/unit."""
    tests_root = repo_root / "tests" / "unit"
    return sorted(path for path in tests_root.glob("test_*.py") if path.is_file())


def build_batches(test_files: list[Path], batch_size: int) -> list[list[Path]]:
    """Split test files into contiguous batches."""
    if batch_size <= 0:
        raise ValueError("batch_size must be > 0")
    return [test_files[i : i + batch_size] for i in range(0, len(test_files), batch_size)]


def run_batched_unit_pytest(
    repo_root: Path,
    batch_size: int = 12,
    per_batch_timeout_seconds: int = 240,
) -> BatchedPytestResult:
    """
    Run `tests/unit` in file batches.

    This avoids long single-session runs that can be interrupted by environment-level
    watchdogs or terminal-session limits.
    """
    files = discover_unit_test_files(repo_root)
    result = BatchedPytestResult()
    if not files:
        return result

    batches = build_batches(files, batch_size=batch_size)
    for idx, batch_files in enumerate(batches, start=1):
        rel_files = [str(path.relative_to(repo_root)) for path in batch_files]
        cmd = [sys.executable, "-m", "pytest", *rel_files, "--tb=no", "-q"]
        try:
            run = subprocess.run(
                cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                timeout=per_batch_timeout_seconds,
                check=False,
            )
            output = (run.stdout + "\n" + run.stderr).strip()
            passed_count = _extract_passed_count(output)
            interrupted = "KeyboardInterrupt" in output
            result.batches.append(
                BatchResult(
                    index=idx,
                    files=batch_files,
                    passed=run.returncode == 0 and not interrupted,
                    exit_code=run.returncode,
                    passed_count=passed_count,
                    output=output,
                    interrupted=interrupted,
                )
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _coerce_text(exc.stdout)
            stderr = _coerce_text(exc.stderr)
            output = (stdout + "\n" + stderr).strip()
            result.batches.append(
                BatchResult(
                    index=idx,
                    files=batch_files,
                    passed=False,
                    exit_code=-1,
                    passed_count=_extract_passed_count(output),
                    output=f"TIMEOUT after {per_batch_timeout_seconds}s\n{output}".strip(),
                    interrupted=False,
                )
            )
            break
    return result


def _extract_passed_count(output: str) -> int:
    counts = [int(match.group("count")) for match in _PASSED_RE.finditer(output)]
    return max(counts) if counts else 0


def _coerce_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode(errors="replace")
    return value
