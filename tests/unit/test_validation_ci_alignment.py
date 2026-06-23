"""The runner's pre-commit validation MUST mirror CI's authoritative ruff/mypy gates.

Observed live (cycle-84 agent B): B's code PASSED CI (ruff + `mypy src`) but the runner's
_run_validation used different flags — ruff WITHOUT CI's `--ignore I001,UP035,W605` and
mypy WITH `--ignore-missing-imports` — so it reported 32 ruff + 12 mypy "errors" CI
ignores (including in files B never touched) and wrongly routed a valid delivery to the
repair loop. These tests pin the runner's gate args to CI's so the two can't drift.
"""
from __future__ import annotations

import pathlib
import re

import automation.run_agent_lifecycle as ral

_CI_YML = pathlib.Path("C:/Fiverr/Fiverr/.github/workflows/ci.yml")


def test_runner_ruff_args_match_ci_yml():
    ci = _CI_YML.read_text(encoding="utf-8")
    m = re.search(r"ruff check ([^\n]+)", ci)
    assert m, "could not find the ruff check command in ci.yml"
    ci_ruff = m.group(1).strip()
    runner_ruff = " ".join(ral._CI_RUFF_ARGS[2:])  # drop leading 'ruff','check'
    assert runner_ruff == ci_ruff, f"runner ruff {runner_ruff!r} != CI {ci_ruff!r}"


def test_runner_mypy_args_match_ci_yml():
    ci = _CI_YML.read_text(encoding="utf-8")
    m = re.search(r"python -m mypy ([^\n]+)", ci)
    assert m, "could not find the mypy command in ci.yml"
    ci_mypy = m.group(1).strip()
    runner_mypy = " ".join(ral._CI_MYPY_ARGS[1:])  # drop leading 'mypy'
    assert runner_mypy == ci_mypy, f"runner mypy {runner_mypy!r} != CI {ci_mypy!r}"


def test_runner_mypy_has_no_ignore_missing_imports():
    # The flag CI does not use — it caused spurious unused-"type: ignore" failures.
    assert "--ignore-missing-imports" not in ral._CI_MYPY_ARGS


def test_runner_ruff_ignores_ci_ignored_rules():
    assert "--ignore" in ral._CI_RUFF_ARGS
    i = ral._CI_RUFF_ARGS.index("--ignore")
    assert ral._CI_RUFF_ARGS[i + 1] == "I001,UP035,W605"
    assert "tests/" in ral._CI_RUFF_ARGS  # CI lints tests/ too
