"""Configuration loading utilities."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from src.config.models import AppConfig, CollectionConfig, NicheConfig, ScoringProfileConfig

ENV_VAR_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


class ConfigLoader:
    """Loads and validates config files into typed Pydantic models."""

    def __init__(self, config_path: str | Path = "config.yaml") -> None:
        self.config_path = Path(config_path)
        self._config: AppConfig | None = None

    def load(self) -> AppConfig:
        if not self.config_path.exists():
            raise ValueError(f"Config file not found: {self.config_path}")

        raw_content = yaml.safe_load(self.config_path.read_text(encoding="utf-8")) or {}
        resolved_content = self._resolve_env_vars(raw_content)

        try:
            self._config = AppConfig.model_validate(resolved_content)
        except ValidationError:
            raise
        except Exception as exc:
            raise ValueError(f"Failed to parse config '{self.config_path}': {exc}") from exc

        return self._config

    def get_niche(self, niche_id: str) -> NicheConfig:
        config = self._require_config()
        for niche in config.niches:
            if niche.niche_id == niche_id:
                return niche
        raise ValueError(f"Niche '{niche_id}' not found in config")

    def get_scoring_profile(self, name: str | None = None) -> ScoringProfileConfig:
        config = self._require_config()
        profile_name = name or config.scoring.active_profile
        profile = config.scoring.profiles.get(profile_name)
        if profile is None:
            raise ValueError(f"Scoring profile '{profile_name}' not found")
        return profile

    def get_collection_config(self) -> CollectionConfig:
        return self._require_config().collection

    def _require_config(self) -> AppConfig:
        if self._config is None:
            return self.load()
        return self._config

    def _resolve_env_vars(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._resolve_env_vars(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._resolve_env_vars(item) for item in value]
        if isinstance(value, str):
            return self._resolve_env_string(value)
        return value

    @staticmethod
    def _resolve_env_string(value: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            env_var = match.group(1)
            return os.environ.get(env_var, "")

        return ENV_VAR_PATTERN.sub(replacer, value)
