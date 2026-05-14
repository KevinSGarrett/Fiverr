"""Unit tests for CLI entrypoints."""

from __future__ import annotations

from pathlib import Path

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
