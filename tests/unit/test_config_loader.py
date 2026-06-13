from __future__ import annotations

from pathlib import Path

import pytest
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


def test_load_secrets_prefers_runner_env_even_with_process_env(tmp_path: Path, monkeypatch) -> None:
    env = tmp_path / "runner.env"
    env.write_text("JIRA_API_TOKEN=file-token\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", env)
    monkeypatch.setenv("JIRA_API_TOKEN", "process-token")
    secrets = config_loader.load_secrets()
    assert secrets["JIRA_API_TOKEN"] == "file-token"


def test_get_secret_falls_back_to_process_env_when_runner_env_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", tmp_path / "missing.env")
    monkeypatch.setenv("JIRA_API_TOKEN", "process-token")
    assert config_loader.get_secret("JIRA_API_TOKEN", "") == "process-token"


def test_load_config_raises_on_malformed_repo_yaml(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "automation/config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "automation/config/autonomous_runner.yml").write_text("a: [1,2", encoding="utf-8")
    monkeypatch.setattr(config_loader, "_find_repo_root", lambda: tmp_path)
    import yaml

    with pytest.raises(yaml.YAMLError):
        config_loader.load_config()


def test_load_config_raises_on_malformed_runner_yaml(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "automation/config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "automation/config/autonomous_runner.yml").write_text("a: 1\n", encoding="utf-8")
    runner_cfg = tmp_path / "runner_config.yaml"
    runner_cfg.write_text("b: [x", encoding="utf-8")
    monkeypatch.setattr(config_loader, "_find_repo_root", lambda: tmp_path)
    monkeypatch.setattr(config_loader, "RUNNER_CONFIG_PATH", runner_cfg)
    import yaml

    with pytest.raises(yaml.YAMLError):
        config_loader.load_config()


def test_load_secrets_logs_without_token_value(tmp_path: Path, monkeypatch, caplog) -> None:
    env = tmp_path / "runner.env"
    env.write_text("JIRA_API_TOKEN=super-secret-token\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", env)
    caplog.set_level("DEBUG")
    config_loader.load_secrets()
    combined = "\n".join(record.message for record in caplog.records)
    assert "super-secret-token" not in combined


def test_find_repo_root_walks_up_directory_tree(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / "repo"
    nested = root / "a" / "b" / "c"
    nested.mkdir(parents=True, exist_ok=True)
    (root / "pyproject.toml").write_text("[tool]", encoding="utf-8")
    monkeypatch.chdir(nested)
    assert config_loader._find_repo_root() == root


def test_find_repo_root_falls_back_to_cwd_after_limit(tmp_path: Path, monkeypatch) -> None:
    nested = tmp_path / "x" / "y" / "z"
    nested.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(nested)
    assert config_loader._find_repo_root() == nested


def test_load_env_file_reads_key_value_pairs(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("JIRA_API_TOKEN=token-abc\nJIRA_EMAIL=test@example.com\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "ENV_FILE_PATH", env_file)
    values = config_loader.load_env_file()
    assert values["JIRA_API_TOKEN"] == "token-abc"
    assert values["JIRA_EMAIL"] == "test@example.com"


def test_get_secret_reads_repo_env_as_third_source(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("JIRA_BASE_URL=https://example.atlassian.net\n", encoding="utf-8")
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(config_loader, "ENV_FILE_PATH", env_file)
    monkeypatch.delenv("JIRA_BASE_URL", raising=False)
    assert config_loader.get_secret("JIRA_BASE_URL", "") == "https://example.atlassian.net"


def test_get_secret_returns_none_when_absent_with_none_default(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(config_loader, "RUNNER_ENV_PATH", tmp_path / "missing.env")
    monkeypatch.setattr(config_loader, "ENV_FILE_PATH", tmp_path / "missing.env")
    monkeypatch.delenv("UNSET_KEY", raising=False)
    assert config_loader.get_secret("UNSET_KEY", None) is None
