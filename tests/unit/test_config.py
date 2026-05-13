"""Unit tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from src.config import ConfigLoader


def test_valid_config_loads_and_returns_niches() -> None:
    loader = ConfigLoader("config.yaml")
    config = loader.load()
    assert len(config.niches) == 9
    assert loader.get_niche("prd_ai_saas").name == "PRD / AI SaaS MVP Roadmap"


def test_scoring_profile_weights_sum_to_one() -> None:
    config = ConfigLoader("config.yaml").load()
    for profile in config.scoring.profiles.values():
        weights = (
            profile.demand
            + profile.competition_inv
            + profile.opportunity
            + profile.feasibility
            + profile.profitability
            + profile.intent
            + profile.saturation_inv
            + profile.weakness
            + profile.trend
        )
        assert abs(weights - 1.0) <= 0.001


def test_missing_niche_id_raises_validation_error(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["niches"][0].pop("niche_id")
    bad_config_path = tmp_path / "bad_config.yaml"
    bad_config_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match="niche_id"):
        ConfigLoader(bad_config_path).load()


def test_env_override_replaces_openai_key(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["llm"]["openai_api_key"] = "${OPENAI_API_KEY}"

    config_path = tmp_path / "env_config.yaml"
    config_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    config = ConfigLoader(config_path).load()
    assert config.llm.openai_api_key == "test-openai-key"
