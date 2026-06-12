from __future__ import annotations

from pathlib import Path

from automation import config_loader


def test_deep_merge_overrides_scalar() -> None:
    base = {"a": 1}
    config_loader._deep_merge(base, {"a": 2})
    assert base["a"] == 2


def test_deep_merge_merges_nested_dicts() -> None:
    base = {"a": {"x": 1}}
    config_loader._deep_merge(base, {"a": {"y": 2}})
    assert base["a"] == {"x": 1, "y": 2}


def test_load_config_reads_repo_yaml(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "automation/config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "automation/config/autonomous_runner.yml").write_text("a: 1\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "_find_repo_root", lambda: tmp_path)
    cfg = config_loader.load_config()
    assert cfg["a"] == 1


def test_load_config_merges_runner_yaml(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "automation/config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "automation/config/autonomous_runner.yml").write_text("a:\n  x: 1\n", encoding="utf-8")
    runner_cfg = tmp_path / "runner_config.yaml"
    runner_cfg.write_text("a:\n  y: 2\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(config_loader, "RUNNER_CONFIG_PATH", runner_cfg)
    cfg = config_loader.load_config()
    assert cfg["a"] == {"x": 1, "y": 2}


def test_load_secrets_returns_empty_when_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", tmp_path / "missing.env")
    assert config_loader.load_secrets() == {}


def test_load_secrets_reads_env_file(tmp_path: Path, monkeypatch) -> None:
    env = tmp_path / "runner.env"
    env.write_text("JIRA_EMAIL=test@example.com\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", env)
    secrets = config_loader.load_secrets()
    assert secrets["JIRA_EMAIL"] == "test@example.com"


def test_get_secret_prefers_file_value(tmp_path: Path, monkeypatch) -> None:
    env = tmp_path / "runner.env"
    env.write_text("X_KEY=file_value\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", env)
    assert config_loader.get_secret("X_KEY", "default") == "file_value"


def test_get_secret_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setattr(config_loader, "load_secrets", lambda: {})
    assert config_loader.get_secret("MISSING_KEY", "default") == "default"
