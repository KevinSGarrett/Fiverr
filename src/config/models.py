"""Pydantic configuration schema for the Fiverr research system."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class FiverrConfig(BaseModel):
    session_mode: Literal["authenticated", "unauthenticated"] = "authenticated"
    session_file: str = "data/sessions/fiverr_session.json"
    login_url: str = "https://www.fiverr.com/login"
    verify_selector: str = "[data-testid='user-menu-button']"


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
    base_delay_seconds: float = Field(default=1.0, ge=0)
    jitter_seconds: float = Field(default=0.5, ge=0)
    max_requests_per_hour: int = Field(default=60, ge=1)
    human_events: bool = False


class CollectionConfig(BaseModel):
    pacing: dict[str, PacingConfig] = Field(default_factory=dict)
    retry_limit: int = Field(default=3, ge=0)
    checkpoint_interval: int = Field(default=50, ge=1)
    proxy_enabled: bool = False


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
    csv: bool = True
    excel: bool = True
    pdf: bool = True
    markdown: bool = True


class ExportConfig(BaseModel):
    output_dir: str = "data/exports"
    formats: ExportFormatsConfig = Field(default_factory=ExportFormatsConfig)
    include_recommendations: bool = True


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


class ScoringConfig(BaseModel):
    active_profile: str = "default"
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
        if self.active_profile not in self.profiles:
            raise ValueError(
                f"scoring.active_profile '{self.active_profile}' not found in scoring.profiles"
            )
        return self


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: SystemConfig = Field(default_factory=SystemConfig)
    fiverr: FiverrConfig = Field(default_factory=FiverrConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    collection: CollectionConfig = Field(default_factory=CollectionConfig)
    scoring: ScoringConfig
    discovery: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    exports: ExportConfig = Field(default_factory=ExportConfig)
    alerts: AlertThresholdsConfig = Field(default_factory=AlertThresholdsConfig)
    niches: list[NicheConfig]
