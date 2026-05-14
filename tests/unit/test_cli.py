"""Unit tests for CLI entrypoints."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import run as run_module
import src.orchestrator as orchestrator_module
from click.testing import CliRunner
from run import cli


def test_config_check_exits_zero() -> None:
    runner = CliRunner()
    config_path = Path("config.yaml").resolve()

    result = runner.invoke(cli, ["config-check", "--config-path", str(config_path)])

    assert result.exit_code == 0
    assert "Config OK:" in result.output


def test_invalid_config_path_exits_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["config-check", "--config-path", "missing_config.yaml"])

    assert result.exit_code != 0


def test_init_db_creates_temp_database(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "cli_init.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    result = runner.invoke(cli, ["init-db", "--database-url", db_url])

    assert result.exit_code == 0
    assert db_path.exists()


def test_smoke_exits_zero() -> None:
    runner = CliRunner()
    config_path = Path("config.yaml").resolve()

    result = runner.invoke(cli, ["smoke", "--config-path", str(config_path)])

    assert result.exit_code == 0
    assert "Smoke OK:" in result.output


def test_help_lists_foundation_export_and_dashboard_commands() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "foundation-gate" in result.output
    assert "export" in result.output
    assert "dashboard" in result.output
    assert "collection-dry-run" in result.output
    assert "analysis-dry-run" in result.output
    assert "phase2-smoke" in result.output


def test_foundation_gate_succeeds_with_temp_sqlite_db(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "foundation_gate.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    config_path = Path("config.yaml").resolve()

    result = runner.invoke(
        cli,
        [
            "foundation-gate",
            "--config-path",
            str(config_path),
            "--database-url",
            db_url,
        ],
    )

    assert result.exit_code == 0
    assert "[PASS]" in result.output


def test_foundation_gate_fails_for_invalid_config_path(tmp_path: Path) -> None:
    runner = CliRunner()
    db_path = tmp_path / "foundation_gate_invalid_config.db"
    db_url = f"sqlite:///{db_path.as_posix()}"

    result = runner.invoke(
        cli,
        [
            "foundation-gate",
            "--config-path",
            "missing_config.yaml",
            "--database-url",
            db_url,
        ],
    )

    assert result.exit_code != 0
    assert "[FAIL] config_load" in result.output


def test_foundation_gate_fails_for_malformed_database_url() -> None:
    runner = CliRunner()
    config_path = Path("config.yaml").resolve()

    result = runner.invoke(
        cli,
        [
            "foundation-gate",
            "--config-path",
            str(config_path),
            "--database-url",
            "not-a-valid-db-url://",
        ],
    )

    assert result.exit_code != 0
    assert "[FAIL] database_registry" in result.output


def test_export_invalid_format_returns_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--format", "xml", "--input-path", "data/input.json"])
    assert result.exit_code != 0


def test_export_missing_input_returns_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["export", "--format", "csv"])
    assert result.exit_code != 0
    assert "Missing option '--input-path'" in result.output


def test_dashboard_stub_does_not_launch_streamlit() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["dashboard", "--mode", "local"])
    assert result.exit_code == 0
    assert "Epic 09" in result.output
    assert "streamlit" not in result.output.lower()


def test_collection_dry_run_invalid_fixture_path_returns_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "collection-dry-run",
            "--fixture-path",
            "tests/fixtures/collection/does_not_exist.json",
        ],
    )
    assert result.exit_code != 0


def test_collection_dry_run_fails_for_empty_seed_keywords(tmp_path: Path) -> None:
    fixture_path = tmp_path / "empty_seeds_fixture.json"
    fixture_path.write_text(json.dumps({"seed_keywords": ["  ", ""]}), encoding="utf-8")
    output_path = tmp_path / "checkpoint.json"
    assert orchestrator_module.run_collection_dry_run(str(fixture_path), str(output_path), sample_size=10) == 2


@pytest.mark.parametrize("sample_size", [0, -3])
def test_collection_dry_run_non_positive_sample_sizes_use_safe_positive_candidate_cap(
    sample_size: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_path = tmp_path / f"fixture_non_positive_{sample_size}.json"
    fixture_path.write_text(
        json.dumps(
            {
                "seed_keywords": ["logo design", "seo audit"],
                "niche_metadata": {"modifiers": []},
                "max_pages": 1,
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "checkpoint_non_positive.json"
    captured: dict[str, Any] = {}

    def _fake_run_collection_dry_run(seeds: list[str], **kwargs: Any) -> Any:
        captured["seeds"] = seeds
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            status="success",
            records_seen=len(seeds),
            records_written=len(seeds),
            checkpoint_path=kwargs["checkpoint_path"],
            errors=[],
        )

    monkeypatch.setattr(
        orchestrator_module.importlib,
        "import_module",
        lambda _name: SimpleNamespace(run_collection_dry_run=_fake_run_collection_dry_run),
    )

    assert (
        orchestrator_module.run_collection_dry_run(
            str(fixture_path),
            str(output_path),
            sample_size=sample_size,
        )
        == 0
    )
    assert captured["seeds"] == ["logo design", "seo audit"]
    assert captured["kwargs"]["max_candidates"] == 2
    assert captured["kwargs"]["max_candidates"] > 0
    assert captured["kwargs"]["niche_metadata"] == {"modifiers": []}


def test_collection_dry_run_large_positive_sample_size_preserves_forwarded_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_path = tmp_path / "fixture_large_sample_size.json"
    fixture_path.write_text(
        json.dumps(
            {
                "seed_keywords": ["logo design", "seo audit"],
                "niche_metadata": {"modifiers": []},
                "max_pages": 1,
            }
        ),
        encoding="utf-8",
    )
    output_path = tmp_path / "checkpoint_large_sample.json"
    captured: dict[str, Any] = {}

    def _fake_run_collection_dry_run(seeds: list[str], **kwargs: Any) -> Any:
        captured["seeds"] = seeds
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            status="success",
            records_seen=len(seeds),
            records_written=len(seeds),
            checkpoint_path=kwargs["checkpoint_path"],
            errors=[],
        )

    monkeypatch.setattr(
        orchestrator_module.importlib,
        "import_module",
        lambda _name: SimpleNamespace(run_collection_dry_run=_fake_run_collection_dry_run),
    )

    assert orchestrator_module.run_collection_dry_run(str(fixture_path), str(output_path), sample_size=10_000) == 0
    assert captured["seeds"] == ["logo design", "seo audit"]
    assert captured["kwargs"]["max_candidates"] == 10_000
    assert captured["kwargs"]["max_candidates"] > 0
    assert captured["kwargs"]["niche_metadata"] == {"modifiers": []}


def test_analysis_dry_run_invalid_fixture_path_returns_nonzero() -> None:
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "analysis-dry-run",
            "--fixture-path",
            "tests/fixtures/analysis/does_not_exist.json",
        ],
    )
    assert result.exit_code != 0


def test_collection_dry_run_can_be_monkeypatched_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fixture_path = tmp_path / "collection_fixture.json"
    fixture_path.write_text('{"seed_keywords": ["ai agent", "mcp server"]}', encoding="utf-8")
    output_path = tmp_path / "checkpoint.json"

    monkeypatch.setattr(run_module, "run_collection_dry_run", lambda **_kwargs: 0)
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "collection-dry-run",
            "--fixture-path",
            str(fixture_path),
            "--output-path",
            str(output_path),
            "--sample-size",
            "2",
        ],
    )
    assert result.exit_code == 0


def test_phase2_smoke_reports_collection_and_analysis() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["phase2-smoke", "--config-path", "config.yaml"])
    assert result.exit_code == 0
    assert "Phase2 smoke OK: collection package" in result.output
    assert "Phase2 smoke OK: analysis package" in result.output
