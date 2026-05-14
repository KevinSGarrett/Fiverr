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


def test_invalid_weight_sum_fails_validation(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["scoring"]["profiles"]["default"]["demand"] = 0.7
    invalid_path = tmp_path / "invalid_weight_sum.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match="weights must sum to 1.0"):
        ConfigLoader(invalid_path).load()


def test_duplicate_niche_id_fails_validation(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["niches"][1]["niche_id"] = source["niches"][0]["niche_id"]
    invalid_path = tmp_path / "duplicate_niche_id.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match="Duplicate niche IDs"):
        ConfigLoader(invalid_path).load()


def test_missing_required_profile_fails_validation(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["scoring"]["profiles"].pop("trend_chaser")
    invalid_path = tmp_path / "missing_profile.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match="Missing required scoring profile"):
        ConfigLoader(invalid_path).load()


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


def test_niche_category_paths_match_known_fiverr_prefixes() -> None:
    valid_prefixes = ("programming-tech/", "writing-translation/")
    config = ConfigLoader("config.yaml").load()
    assert len(config.niches) == 9
    for niche in config.niches:
        assert niche.category_path.startswith(valid_prefixes)


def test_niche_pricing_tiers_ascending() -> None:
    config = ConfigLoader("config.yaml").load()
    for niche in config.niches:
        prices = niche.starter_prices
        basic = prices["basic"]
        standard = prices["standard"]
        premium = prices["premium"]
        assert basic < standard < premium


def test_discovery_skill_profile_has_primary_skills() -> None:
    config = ConfigLoader("config.yaml").load()
    assert config.discovery.skill_profile.primary_skills


def test_empty_seed_keywords_fail_validation(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["niches"][0]["seed_keywords"] = []
    invalid_path = tmp_path / "empty_seed_keywords.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValidationError, match="empty seed_keywords"):
        ConfigLoader(invalid_path).load()


def test_loader_missing_required_top_level_section_fails_fast(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source.pop("collection")
    invalid_path = tmp_path / "missing_collection_section.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required section"):
        ConfigLoader(invalid_path).load()


def test_phase2_collection_defaults_disable_live_connectors() -> None:
    config = ConfigLoader("config.yaml").load()
    assert config.phase2_collection.fixture_only_mode is True
    assert config.phase2_collection.allow_live_connectors is False
    assert not any(config.phase2_collection.connectors_enabled.values())


def test_phase2_fixture_only_mode_loads(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["phase2_collection"]["fixture_only_mode"] = True
    config_path = tmp_path / "phase2_fixture_mode.yaml"
    config_path.write_text(yaml.safe_dump(source), encoding="utf-8")
    config = ConfigLoader(config_path).load()
    assert config.phase2_collection.fixture_only_mode is True


def test_phase2_negative_limits_fail_validation(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["phase2_collection"]["dry_run_sample_limit"] = -1
    invalid_path = tmp_path / "phase2_negative_limit.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(ValidationError):
        ConfigLoader(invalid_path).load()


def test_phase2_connector_enable_requires_explicit_opt_in(tmp_path: Path) -> None:
    source = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    source["phase2_collection"]["allow_live_connectors"] = False
    source["phase2_collection"]["connectors_enabled"]["google_trends"] = True
    invalid_path = tmp_path / "phase2_live_connector_invalid.yaml"
    invalid_path.write_text(yaml.safe_dump(source), encoding="utf-8")
    with pytest.raises(ValidationError, match="allow_live_connectors"):
        ConfigLoader(invalid_path).load()


def test_phase2_analysis_threshold_ranges_are_consistent() -> None:
    config = ConfigLoader("config.yaml").load()
    assert 0.0 <= config.phase2_analysis.min_confidence <= 1.0
    assert 0.0 <= config.phase2_analysis.strong_confidence <= 1.0
    assert 0.0 <= config.phase2_analysis.quality_score_min <= 100.0
    assert 0.0 <= config.phase2_analysis.quality_score_strong <= 100.0
    assert config.phase2_analysis.strong_confidence >= config.phase2_analysis.min_confidence
    assert config.phase2_analysis.quality_score_strong >= config.phase2_analysis.quality_score_min
