"""
config_loader.py — Load and merge runner config from repo-side and runner-side sources.
Secrets always come from C:\\AI_Runner\\secrets\\runner.env, never from repo.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values

REPO_CONFIG_PATH = Path("automation/config/autonomous_runner.yml")
RUNNER_CONFIG_PATH = Path("C:/AI_Runner/config/runner_config.yaml")
RUNNER_ENV_PATH = Path("C:/AI_Runner/secrets/runner.env")


def load_config(repo_root: Path | None = None) -> dict[str, Any]:
    """Load merged config. Repo config + runner config, no secrets."""
    root = repo_root or _find_repo_root()
    cfg: dict[str, Any] = {}

    repo_cfg_file = root / REPO_CONFIG_PATH
    if repo_cfg_file.exists():
        with open(repo_cfg_file) as f:
            cfg = yaml.safe_load(f) or {}

    runner_cfg_file = RUNNER_CONFIG_PATH
    if runner_cfg_file.exists():
        with open(runner_cfg_file) as f:
            runner_cfg = yaml.safe_load(f) or {}
        _deep_merge(cfg, runner_cfg)

    return cfg


def load_secrets() -> dict[str, str]:
    """Load secrets from runner.env. Never committed to repo."""
    env_file = RUNNER_ENV_PATH
    if not env_file.exists():
        return {}
    return {k: v or '' for k, v in dotenv_values(str(env_file)).items()}


def get_secret(key: str, default: str = "") -> str:
    """Get a single secret value."""
    secrets = load_secrets()
    return secrets.get(key, os.environ.get(key, default))


def _find_repo_root() -> Path:
    """Walk up from cwd to find repo root (contains pyproject.toml)."""
    p = Path.cwd()
    for _ in range(10):
        if (p / "pyproject.toml").exists():
            return p
        p = p.parent
    return Path.cwd()


def _deep_merge(base: dict, override: dict) -> None:
    """Merge override into base in-place (shallow for non-dict values)."""
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
