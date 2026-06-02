"""
Suite count guard - R9.1 (SCRUM-630).

Fails if total test count drops below C055 verified floor (3829).
A failure means a test was accidentally deleted. Investigate before merging.
"""
from __future__ import annotations

import re
import subprocess
import sys

SUITE_COUNT_FLOOR = 3829
"""Verified test count after C055 merge. Never decrease this without PM approval."""


def _parse_collected_count(output: str) -> int:
    """Extract the pytest collected-count integer from collect-only output text."""
    numbers = re.findall(r"(\d+) (?:test|item)", output)
    return int(numbers[-1]) if numbers else 0


def test_suite_count_meets_floor() -> None:
    """Regression: total collected test count must not drop below 3829 (C055 baseline)."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        capture_output=True,
        check=False,
        text=True,
        cwd=".",
    )
    output = result.stdout + result.stderr
    collected = _parse_collected_count(output)
    assert collected >= SUITE_COUNT_FLOOR, (
        f"Suite count {collected} dropped below floor {SUITE_COUNT_FLOOR} - "
        f"a test was removed or collection failed. "
        f"Check recent commits for test deletions or import errors."
    )
