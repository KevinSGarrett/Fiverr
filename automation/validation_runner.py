"""
validation_runner.py â€” Run local validation commands (ruff, mypy, pytest, config-check).
Returns structured results with PASS/FAIL per gate.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

VENV_PYTHON = Path("C:/Fiverr/Fiverr/.venv/Scripts/python.exe")
REPO_ROOT = Path(__file__).parent.parent


@dataclass
class GateResult:
    name: str
    passed: bool
    output: str
    exit_code: int


@dataclass
class ValidationResult:
    gates: list[GateResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(g.passed for g in self.gates)

    def failed_gates(self) -> list[GateResult]:
        return [g for g in self.gates if not g.passed]

    def summary(self) -> str:
        lines = []
        for g in self.gates:
            icon = "PASS" if g.passed else "FAIL"
            lines.append(f"  [{icon}] {g.name}")
        return "\n".join(lines)


def run_gate(name: str, cmd: list[str], cwd: Path = REPO_ROOT,
             timeout: int = 300) -> GateResult:
    try:
        r = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout
        )
        output = (r.stdout + r.stderr).strip()
        return GateResult(name=name, passed=(r.returncode == 0),
                          output=output, exit_code=r.returncode)
    except subprocess.TimeoutExpired:
        return GateResult(name=name, passed=False,
                          output=f"TIMEOUT after {timeout}s", exit_code=-1)
    except Exception as e:
        return GateResult(name=name, passed=False,
                          output=str(e), exit_code=-1)


def run_full_validation(repo_root: Path = REPO_ROOT) -> ValidationResult:
    """Run all required gates in order."""
    py = str(VENV_PYTHON)
    result = ValidationResult()

    result.gates.append(run_gate("ruff",
        [py, "-m", "ruff", "check", "."], cwd=repo_root))

    result.gates.append(run_gate("mypy",
        [py, "-m", "mypy", "src"], cwd=repo_root))

    result.gates.append(run_gate("pytest-coverage",
        [py, "-m", "pytest", "-q",
         "--cov=src", "--cov-report=xml",
         "--cov-report=term-missing",
         "--cov-fail-under=90"], cwd=repo_root))

    result.gates.append(run_gate("config-check",
        [py, "run.py", "config-check", "--config-path", "config.yaml"],
        cwd=repo_root))

    result.gates.append(run_gate("foundation-gate",
        [py, "run.py", "foundation-gate",
         "--database-url", "sqlite:///data/foundation_gate_runner.db"],
        cwd=repo_root, timeout=120))

    result.gates.append(run_gate("phase2-smoke",
        [py, "run.py", "phase2-smoke"], cwd=repo_root, timeout=120))

    return result


def run_targeted_validation(gates: list[str],
                             repo_root: Path = REPO_ROOT) -> ValidationResult:
    """Run only specified gates (e.g., ['ruff', 'mypy'] after a repair)."""
    py = str(VENV_PYTHON)
    result = ValidationResult()
    gate_map = {
        "ruff": [py, "-m", "ruff", "check", "."],
        "mypy": [py, "-m", "mypy", "src"],
        "config-check": [py, "run.py", "config-check", "--config-path", "config.yaml"],
    }
    for name in gates:
        if name in gate_map:
            result.gates.append(run_gate(name, gate_map[name], cwd=repo_root))
        else:
            result.gates.append(GateResult(name=name, passed=False,
                                            output=f"Unknown gate: {name}", exit_code=-1))
    return result
