"""Pydantic configuration schema for the Fiverr research system."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

REQUIRED_NICHE_COUNT = 9
REQUIRED_SCORING_PROFILES = ("default", "aggressive_new_seller", "profitability_focus", "trend_chaser")


def _validate_safe_relative_path(value: str, field_name: str) -> str:
    path_value = value.strip()
    if not path_value:
        raise ValueError(f"{field_name} cannot be empty.")
    normalized = path_value.replace("\\", "/")
    if normalized.startswith("/") or ":/" in normalized:
        raise ValueError(f"{field_name} must be a relative safe path, got '{value}'.")
    if ".." in normalized.split("/"):
        raise ValueError(f"{field_name} cannot traverse parent directories.")
    return normalized


class SystemConfig(BaseModel):
    run_mode: Literal[
        "full",
        "collect-only",
        "analyze-only",
        "score-only",
        "report-only",
        "keyword-only",
        "resume",
        "relogin",
    ] = "full"
    checkpoint_interval: int = Field(default=50, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    data_dir: str = "data"

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, value: str) -> str:
        return _validate_safe_relative_path(value, "system.data_dir")


class FiverrConfig(BaseModel):
    session_mode: Literal["authenticated", "unauthenticated"] = "authenticated"
    session_file: str = "data/sessions/fiverr_session.json"
    login_url: str = "https://www.fiverr.com/login"
    verify_selector: str = "[data-testid='user-menu-button']"

    @field_validator("session_file")
    @classmethod
    def validate_session_file(cls, value: str) -> str:
        return _validate_safe_relative_path(value, "fiverr.session_file")


class LLMModelsConfig(BaseModel):
    tier_high: str = "gpt-4o"
    tier_low: str = "gpt-4o-mini"
    embeddings: str = "text-embedding-3-small"


class LLMConfig(BaseModel):
    provider: Literal["openai", "ollama"] = "openai"
    openai_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    cache_enabled: bool = True
    cache_ttl_hours: int = Field(default=72, ge=1)
    max_tpm: int = Field(default=90000, ge=1)
    cost_alert_daily_usd: float = Field(default=5.0, ge=0)
    log_all_calls: bool = True
    models: LLMModelsConfig = Field(default_factory=LLMModelsConfig)


class PacingConfig(BaseModel):
    base_delay_seconds: float = Field(default=1.0, gt=0)
    jitter_seconds: float = Field(default=0.5, gt=0)
    max_requests_per_hour: int = Field(default=60, ge=1)
    human_events: bool = False


class ScrapFlyCollectionConfig(BaseModel):
    """ScrapFly API settings for PerimeterX bypass.

    Set enabled=True and export SCRAPFLY_API_KEY=scp-live-... to activate.
    When enabled, collection workflows use ScrapFly instead of Playwright
    for page fetching; all existing HTML parsers are untouched.
    """

    enabled: bool = False
    api_key_env_var: str = "SCRAPFLY_API_KEY"
    asp: bool = True
    render_js: bool = True
    country: str = "US"
    auto_scroll: bool = True
    max_retries: int = 3
    timeout_seconds: int = 60
    cost_budget_credits: int | None = None


class CollectionConfig(BaseModel):
    pacing: dict[str, PacingConfig] = Field(default_factory=dict)
    retry_limit: int = Field(default=3, ge=0)
    checkpoint_interval: int = Field(default=50, ge=1)
    proxy_enabled: bool = False
    scrapfly: ScrapFlyCollectionConfig = Field(default_factory=ScrapFlyCollectionConfig)

    @model_validator(mode="after")
    def validate_pacing_profiles(self) -> CollectionConfig:
        if not self.pacing:
            raise ValueError("collection.pacing must define at least one pacing profile.")
        for profile_name, profile in self.pacing.items():
            if profile.base_delay_seconds <= 0 or profile.jitter_seconds <= 0:
                raise ValueError(
                    f"Invalid collection pacing values for '{profile_name}': "
                    "base_delay_seconds and jitter_seconds must be positive."
                )
            if profile.max_requests_per_hour <= 0:
                raise ValueError(
                    f"Invalid collection pacing values for '{profile_name}': "
                    "max_requests_per_hour must be positive."
                )
        return self


class RedditConfig(BaseModel):
    source_mode: Literal["disabled", "manual_import", "devvit_bridge", "praw_oauth"] = "devvit_bridge"
    enabled: bool = True
    devvit_import_dir: str = "data/imports/reddit_devvit"
    bridge_ingest_enabled: bool = False
    collection_method: str = "reddit_devvit_bridge"
    match_strategy: str = "devvit_listing_keyword_filter"

    @field_validator("devvit_import_dir")
    @classmethod
    def validate_devvit_import_dir(cls, value: str) -> str:
        return _validate_safe_relative_path(value, "reddit.devvit_import_dir")


class Phase2CollectionConfig(BaseModel):
    fixture_only_mode: bool = True
    dry_run_sample_limit: int = Field(default=25, ge=1)
    dry_run_max_pages: int = Field(default=2, ge=1)
    allow_live_connectors: bool = False
    connectors_enabled: dict[str, bool] = Field(
        default_factory=lambda: {
            "google_trends": False,
            "reddit_api": False,
            "external_marketplaces": False,
        }
    )

    @model_validator(mode="after")
    def validate_live_connector_opt_in(self) -> Phase2CollectionConfig:
        if not self.allow_live_connectors and any(self.connectors_enabled.values()):
            raise ValueError(
                "phase2_collection.connectors_enabled cannot enable live connectors unless "
                "phase2_collection.allow_live_connectors is true."
            )
        return self


class Phase2AnalysisConfig(BaseModel):
    min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    strong_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    quality_score_min: float = Field(default=60.0, ge=0.0, le=100.0)
    quality_score_strong: float = Field(default=80.0, ge=0.0, le=100.0)
    max_keywords_per_run: int = Field(default=250, ge=1)
    max_competitors_per_run: int = Field(default=100, ge=1)
    max_text_chars: int = Field(default=12000, ge=1)

    @model_validator(mode="after")
    def validate_threshold_ordering(self) -> Phase2AnalysisConfig:
        if self.strong_confidence < self.min_confidence:
            raise ValueError("phase2_analysis.strong_confidence must be >= min_confidence.")
        if self.quality_score_strong < self.quality_score_min:
            raise ValueError("phase2_analysis.quality_score_strong must be >= quality_score_min.")
        return self


class ScoringProfileConfig(BaseModel):
    demand: float = Field(default=0.2, ge=0.0, le=1.0)
    competition_inv: float = Field(default=0.2, ge=0.0, le=1.0)
    opportunity: float = Field(default=0.25, ge=0.0, le=1.0)
    feasibility: float = Field(default=0.15, ge=0.0, le=1.0)
    profitability: float = Field(default=0.1, ge=0.0, le=1.0)
    intent: float = Field(default=0.1, ge=0.0, le=1.0)
    saturation_inv: float = Field(default=0.0, ge=0.0, le=1.0)
    weakness: float = Field(default=0.0, ge=0.0, le=1.0)
    trend: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weight_sum(self) -> ScoringProfileConfig:
        total = (
            self.demand
            + self.competition_inv
            + self.opportunity
            + self.feasibility
            + self.profitability
            + self.intent
            + self.saturation_inv
            + self.weakness
            + self.trend
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Scoring profile weights must sum to 1.0, got {total:.4f}")
        return self


class ScoringDemandConfig(BaseModel):
    """Runtime knobs for demand-score cluster integration behavior."""

    use_cluster_boost: bool = True
    cluster_boost: float = Field(default=5.0, ge=0.0, le=10.0)
    min_cluster_size: int = Field(default=3, ge=1)


class ScoringCompetitionConfig(BaseModel):
    """Runtime knobs for competition-score Stage 10 profile integration."""

    use_competitor_profile: bool = True


class ScoringFeasibilityConfig(BaseModel):
    """Runtime knobs for feasibility-score Stage 10 gap-signal integration."""

    gap_boost_per_flag: float = Field(default=10.0, ge=0.0, le=30.0)
    max_gap_boost: float = Field(default=30.0, ge=0.0, le=30.0)

    @model_validator(mode="after")
    def validate_gap_boost_bounds(self) -> ScoringFeasibilityConfig:
        if self.max_gap_boost < self.gap_boost_per_flag:
            raise ValueError("scoring.feasibility.max_gap_boost must be >= gap_boost_per_flag.")
        return self


class ScoringSaturationConfig(BaseModel):
    """Runtime knobs for saturation-score Stage 13 integration behavior."""

    use_analysis_output: bool = True


class DiscoverySkillProfileConfig(BaseModel):
    primary_skills: list[str] = Field(default_factory=list, min_length=1)
    secondary_skills: list[str] = Field(default_factory=list)


class DiscoveryConfig(BaseModel):
    enabled: bool = True
    max_hypotheses_per_run: int = Field(default=10, ge=1)
    max_cost_per_run: float = Field(default=5.0, ge=0)
    min_confidence: float = Field(default=0.6, ge=0, le=1)
    gold_threshold: float = Field(default=0.8, ge=0, le=1)
    enabled_modes: list[str] = Field(default_factory=lambda: ["full"])
    skill_profile: DiscoverySkillProfileConfig = Field(
        default_factory=lambda: DiscoverySkillProfileConfig(primary_skills=["market_research"])
    )


class ExportFormatsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    csv: bool = True
    excel: bool = True
    pdf: bool = True
    markdown: bool = True


class ExportConfig(BaseModel):
    output_dir: str = "data/exports"
    formats: ExportFormatsConfig = Field(default_factory=ExportFormatsConfig)
    include_recommendations: bool = True

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, value: str) -> str:
        return _validate_safe_relative_path(value, "exports.output_dir")

    @model_validator(mode="after")
    def validate_formats_enabled(self) -> ExportConfig:
        enabled = {
            "csv": self.formats.csv,
            "excel": self.formats.excel,
            "pdf": self.formats.pdf,
            "markdown": self.formats.markdown,
        }
        if not any(enabled.values()):
            raise ValueError("exports.formats must enable at least one export format.")
        return self


class AlertThresholdsConfig(BaseModel):
    stale_data_warning_hours: int = Field(default=120, ge=1)
    llm_cost_alert_daily_usd: float = Field(default=5.0, ge=0)
    run_failure_notify: bool = True
    new_strong_go_notify: bool = True


class NicheConfig(BaseModel):
    niche_id: str
    name: str
    depth: Literal["full", "standard", "keyword_only", "feasibility"] = "standard"
    category_path: str
    seed_keywords: list[str] = Field(default_factory=list)
    starter_prices: dict[str, float] = Field(default_factory=dict)
    hard_exclusions: list[str] = Field(default_factory=list)
    is_active: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_seed_keywords(self) -> NicheConfig:
        if not self.seed_keywords:
            raise ValueError(f"niche '{self.niche_id}' has an empty seed_keywords list.")
        return self


class ScoringConfig(BaseModel):
    active_profile: str = "default"
    demand: ScoringDemandConfig = Field(default_factory=ScoringDemandConfig)
    competition: ScoringCompetitionConfig = Field(default_factory=ScoringCompetitionConfig)
    feasibility: ScoringFeasibilityConfig = Field(default_factory=ScoringFeasibilityConfig)
    saturation: ScoringSaturationConfig = Field(default_factory=ScoringSaturationConfig)
    profiles: dict[str, ScoringProfileConfig] = Field(default_factory=dict)
    thresholds: dict[str, float] = Field(
        default_factory=lambda: {
            "strong_go": 80.0,
            "conditional_go": 60.0,
            "monitor": 40.0,
            "caution": 20.0,
        }
    )

    @model_validator(mode="after")
    def validate_active_profile(self) -> ScoringConfig:
        missing_profiles = [name for name in REQUIRED_SCORING_PROFILES if name not in self.profiles]
        if missing_profiles:
            missing = ", ".join(missing_profiles)
            raise ValueError(f"Missing required scoring profile(s): {missing}")
        if self.active_profile not in self.profiles:
            raise ValueError(
                f"scoring.active_profile '{self.active_profile}' not found in scoring.profiles"
            )
        return self


class RelevanceConfig(BaseModel):
    enable_sponsored_exclusion: bool = True
    enable_zombie_filter: bool = True
    zombie_threshold: float = Field(default=0.50, ge=0.0, le=1.0)
    min_account_age_days: int = Field(default=180, ge=1)
    top_n_for_scoring: int = Field(default=10, ge=1)


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: SystemConfig = Field(default_factory=SystemConfig)
    fiverr: FiverrConfig = Field(default_factory=FiverrConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    reddit: RedditConfig = Field(default_factory=RedditConfig)
    phase2_collection: Phase2CollectionConfig = Field(default_factory=Phase2CollectionConfig)
    phase2_analysis: Phase2AnalysisConfig = Field(default_factory=Phase2AnalysisConfig)
    scoring: ScoringConfig
    relevance: RelevanceConfig = Field(default_factory=RelevanceConfig)
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    exports: ExportConfig = Field(default_factory=ExportConfig)
    alerts: AlertThresholdsConfig = Field(default_factory=AlertThresholdsConfig)
    niches: list[NicheConfig]

    @model_validator(mode="after")
    def validate_niches(self) -> AppConfig:
        if len(self.niches) != REQUIRED_NICHE_COUNT:
            raise ValueError(
                f"Config must define exactly {REQUIRED_NICHE_COUNT} niches, got {len(self.niches)}."
            )
        niche_ids = [niche.niche_id for niche in self.niches]
        duplicate_ids = sorted({niche_id for niche_id in niche_ids if niche_ids.count(niche_id) > 1})
        if duplicate_ids:
            raise ValueError(f"Duplicate niche IDs are not allowed: {', '.join(duplicate_ids)}")
        return self
