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
