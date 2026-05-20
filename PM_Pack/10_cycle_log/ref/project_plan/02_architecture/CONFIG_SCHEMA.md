# Config Schema
# Fiverr Research System — Wave 2

**Document Status:** Complete
**Wave:** 2 — Technical Architecture
**Purpose:** Full documentation of every config.yaml field — name, type, default, validation rules, description, examples, and recalculation triggers.

---

## Config Design Rules

1. config.yaml is the single source of truth for all user-configurable parameters
2. Secrets (API keys, credentials) live in .env only — referenced in config.yaml as ${VAR_NAME}
3. Every field has a documented default — missing fields fall back to defaults, never fail
4. Fields that trigger pipeline recalculation when changed are marked with ⚡
5. Changes to niche depth require no code change — the Niche Depth Dispatcher reads config at run start
6. Scoring weight changes trigger automatic score recalculation on the next run start
7. Config is loaded once at startup, validated by Pydantic, and distributed to modules via dependency injection

---

## .env.example (Committed to Repo)

```bash
# .env.example — copy to .env and fill in your values
# NEVER commit .env to source control

# Required: OpenAI API key for LLM analysis
OPENAI_API_KEY=sk-your-key-here

# Optional: Fiverr credentials stored here as a reference reminder for the manual login flow.
# The system does NOT auto-login using these — you log in manually in the headed browser.
# Having them here just helps you remember which account to use.
FIVERR_EMAIL=your-fiverr-email@example.com
```

---

## Full config.yaml Schema

```yaml
# ================================================================
# FIVERR RESEARCH SYSTEM — config.yaml
# Full schema with all fields, types, defaults, and descriptions
# ================================================================

# ----------------------------------------------------------------
# SYSTEM — Core runtime settings
# ----------------------------------------------------------------
system:
  run_mode: full
  # Type: string
  # Values: full | collect-only | analyze-only | score-only | report-only | keyword-only | resume | relogin
  # Default: full
  # Description: Default run mode when no --mode flag is passed to run.py
  # Overridden by: --mode CLI flag (CLI flag always wins)

  checkpoint_interval: 50
  # Type: integer
  # Default: 50
  # Range: 10–200
  # Description: Write a checkpoint file every N records during collection stages
  # Lower values = more resilient to interruption, slightly slower I/O
  # Higher values = fewer file writes, less resilient to interruption

  log_level: INFO
  # Type: string
  # Values: DEBUG | INFO | WARNING | ERROR
  # Default: INFO
  # Description: Logging verbosity. DEBUG produces very verbose output including all SQL queries.

  data_dir: data
  # Type: string (path)
  # Default: data
  # Description: Root directory for all data files (db, sessions, checkpoints, exports, raw)
  # Can be an absolute path or relative to the project root

# ----------------------------------------------------------------
# FIVERR — Session and browser settings
# ----------------------------------------------------------------
fiverr:
  session_mode: authenticated
  # Type: string
  # Values: authenticated | unauthenticated
  # Default: authenticated
  # Description: Whether to use the user's Fiverr account for collection.
  #   authenticated = load saved session, run headlessly after first login
  #   unauthenticated = no session, browse as a guest (fallback only)

  session_file: data/sessions/fiverr_session.json
  # Type: string (path)
  # Default: data/sessions/fiverr_session.json
  # Description: Path to the Playwright storage_state session file.
  # This file is auto-created on first --mode relogin run.
  # SECURITY: This file must be in .gitignore. chmod 600 is set automatically.

  login_url: https://www.fiverr.com/login
  # Type: string (URL)
  # Default: https://www.fiverr.com/login
  # Description: Fiverr login page URL. Unlikely to need changing.

  verify_selector: "[data-testid='user-menu-button']"
  # Type: string (CSS selector)
  # Default: [data-testid='user-menu-button']
  # Description: CSS selector used to verify logged-in state after session load.
  # If Fiverr updates their DOM structure, update this selector.

# ----------------------------------------------------------------
# LLM — Provider and model settings
# ----------------------------------------------------------------
llm:
  provider: openai
  # Type: string
  # Values: openai | ollama
  # Default: openai
  # Description: Primary LLM provider.
  #   openai = OpenAI API (requires OPENAI_API_KEY in .env)
  #   ollama = Local Ollama server (requires Ollama running at localhost:11434)

  openai_api_key: ${OPENAI_API_KEY}
  # Type: string (env var reference)
  # Default: loaded from .env
  # Description: OpenAI API key. NEVER hardcode here — always use ${OPENAI_API_KEY}.

  ollama_base_url: http://localhost:11434
  # Type: string (URL)
  # Default: http://localhost:11434
  # Description: Ollama server URL. Only used when provider = ollama.

  cache_enabled: true
  # Type: boolean
  # Default: true
  # Description: Whether to cache LLM responses in the llm_cache SQLite table.
  # Setting to false forces all LLM calls to hit the API every run.
  # Recommended: always true in production to control costs.

  cache_ttl_hours: 72
  # Type: integer
  # Default: 72
  # Description: How long to keep LLM cache entries (hours).
  # Cache entries older than this are invalidated on the next run.
  # Should match or exceed the TTL of the source data that generated the prompt.
  # ⚡ Changing this value does not affect existing cache entries — only future ones.

  max_tpm: 90000
  # Type: integer
  # Default: 90000
  # Description: Maximum tokens per minute across all LLM calls. Enforced by the LLM client.
  # Adjust based on your OpenAI tier rate limit (check platform.openai.com/account/limits).
  # Tier 1 (new accounts): typically 30,000–100,000 TPM depending on model.

  cost_alert_daily_usd: 5.00
  # Type: float
  # Default: 5.00
  # Description: Daily LLM spend threshold in USD. Alert fires when exceeded.
  # Alert is shown in dashboard and included in run summary.
  # Set to 0 to disable alerts. Set higher for heavy research use.

  log_all_calls: true
  # Type: boolean
  # Default: true
  # Description: Whether to log every LLM call to llm_usage_logs table.
  # Enables the LLM cost dashboard view and per-run cost tracking.

  models:
    tier_high: gpt-4o
    # Type: string (OpenAI model ID)
    # Default: gpt-4o
    # Description: Model used for nuanced, strategic, user-facing LLM tasks.
    # Used for: gig description quality, weakness detection, competitor synthesis,
    #   recommendation titles, package design, description drafts, differentiation angles,
    #   red flags, score explanations, competitor summaries, niche viability assessment.
    # ⚡ Changing this model affects all tier_high LLM calls on the next run.
    #   Cached responses from the old model remain valid until their TTL expires.

    tier_low: gpt-4o-mini
    # Type: string (OpenAI model ID)
    # Default: gpt-4o-mini
    # Description: Model used for high-volume, templated, lower-complexity LLM tasks.
    # Used for: keyword expansion, intent classification, review themes, cluster labeling,
    #   tag generation, FAQ entries, buyer personas, trend narratives, run summaries.
    # ⚡ Same caching behavior as tier_high.

    embeddings: text-embedding-3-small
    # Type: string (OpenAI embedding model ID)
    # Default: text-embedding-3-small
    # Description: Embedding model for semantic keyword clustering.
    # ⚡ Changing this model invalidates all existing keyword embeddings.
    #   All keywords will be re-embedded on the next run (may increase cost significantly
    #   for large keyword universes).

    # Per-stage model overrides (null = use tier_high or tier_low default)
    keyword_expansion: null           # Uses tier_low by default
    gig_description_quality: null     # Uses tier_high by default
    competitor_synthesis: null        # Uses tier_high by default
    recommendation_titles: null       # Uses tier_high by default
    opportunity_explanation: null     # Uses tier_high by default
    run_summary: null                 # Uses tier_low by default
    # Set to a specific model ID to override, e.g.: gig_description_quality: gpt-4o-mini

  ollama_models:
    tier_high: llama3:70b
    # Ollama model for tier_high tasks when provider = ollama
    tier_low: llama3:8b
    # Ollama model for tier_low tasks when provider = ollama

# ----------------------------------------------------------------
# SCORING — Weights, profiles, and thresholds
# ----------------------------------------------------------------
scoring:
  active_profile: aggressive_new_seller
  # Type: string
  # Values: any key in scoring.profiles
  # Default: aggressive_new_seller
  # Description: Which scoring weight profile to use for all score calculations.
  # ⚡ Changing this triggers automatic score recalculation on the next run start
  #   (equivalent to running --mode score-only before the full run).

  profiles:
    # Each profile must have exactly 9 weight fields that sum to 1.0.
    # A validation error is raised at startup if weights don't sum to 1.0.

    default:
      demand: 0.20           # Demand Score weight
      competition_inv: 0.20  # Competition Score (inverted) weight
      opportunity: 0.25      # Opportunity Score weight — highest
      feasibility: 0.15      # New Seller Feasibility Score weight
      profitability: 0.10    # Profitability Score weight
      intent: 0.10           # Conversion Intent Score weight
      saturation_inv: 0.05   # Saturation Score (inverted) weight
      weakness: 0.10         # Gig Quality Weakness Score weight
      trend: 0.05            # Trend Score weight

    aggressive_new_seller:
      # Optimized for: entering niches with weak competition where a new seller can win fast
      feasibility: 0.25
      weakness: 0.20
      opportunity: 0.20
      demand: 0.15
      competition_inv: 0.10
      profitability: 0.05
      intent: 0.05
      saturation_inv: 0.00
      trend: 0.00

    profitability_focus:
      # Optimized for: finding the highest-revenue niches
      profitability: 0.25
      intent: 0.20
      opportunity: 0.20
      demand: 0.15
      competition_inv: 0.10
      feasibility: 0.05
      weakness: 0.05
      saturation_inv: 0.00
      trend: 0.00

    trend_chaser:
      # Optimized for: finding niches growing fastest right now
      trend: 0.25
      demand: 0.25
      opportunity: 0.20
      competition_inv: 0.15
      feasibility: 0.10
      profitability: 0.05
      intent: 0.00
      weakness: 0.00
      saturation_inv: 0.00

  thresholds:
    # GO/PASS tag thresholds — configurable
    strong_go: 80      # Score >= 80 → STRONG GO
    conditional_go: 60 # Score >= 60 → CONDITIONAL GO
    monitor: 40        # Score >= 40 → MONITOR
    caution: 20        # Score >= 20 → CAUTION
    # Score < 20 → PASS

# ----------------------------------------------------------------
# PACING — Request rate limits and delays per source
# ----------------------------------------------------------------
pacing:
  fiverr_search:
    base_delay_seconds: 4
    # Type: float | Default: 4 | Description: Minimum wait between Fiverr search requests
    jitter_seconds: 3
    # Type: float | Default: 3 | Description: Additional random delay (uniform 0 to jitter_seconds)
    max_requests_per_hour: 60
    # Type: integer | Default: 60 | Description: Hard cap on Fiverr search requests per hour
    human_events: true
    # Type: boolean | Default: true | Description: Enable scroll/hover/dwell simulation on this source

  fiverr_gig_detail:
    base_delay_seconds: 6
    jitter_seconds: 4
    max_requests_per_hour: 40
    human_events: true

  fiverr_seller_profile:
    base_delay_seconds: 5
    jitter_seconds: 3
    max_requests_per_hour: 40
    human_events: true

  google_trends:
    base_delay_seconds: 10
    jitter_seconds: 5
    max_requests_per_hour: 20
    human_events: false

  reddit_api:
    base_delay_seconds: 2
    jitter_seconds: 1
    max_requests_per_hour: 60
    human_events: false

  youtube:
    base_delay_seconds: 3
    jitter_seconds: 2
    max_requests_per_hour: 60
    human_events: false

  external_default:
    # Applied to any source not explicitly listed above
    base_delay_seconds: 3
    jitter_seconds: 2
    max_requests_per_hour: 100
    human_events: false

# ----------------------------------------------------------------
# OPPORTUNITY THRESHOLDS — GO/PASS tag thresholds
# ----------------------------------------------------------------
opportunity_thresholds:
  strong_go: 80
  conditional_go: 60
  monitor: 40
  caution: 20
  # Note: these are duplicated from scoring.thresholds for convenience.
  # scoring.thresholds takes precedence if both are set.

# ----------------------------------------------------------------
# SCHEDULER — Automated run scheduling (APScheduler v1)
# ----------------------------------------------------------------
scheduler:
  enabled: true
  # Type: boolean | Default: true
  # Description: Whether to run on a schedule. Set to false for manual-only runs.

  timezone: "America/Chicago"
  # Type: string (IANA timezone name)
  # Default: America/Chicago
  # Description: Timezone for all cron expressions

  jobs:
    weekly_full_run:
      mode: full
      cron: "0 23 * * 0"
      # Type: string (cron expression) | Default: "0 23 * * 0" (Sunday 11pm)
      # Description: When to trigger the weekly full research run
      on_overlap: skip
      # Type: string | Values: skip | replace | queue | Default: skip
      # Description: What to do if a scheduled run is triggered while a run is still active

# ----------------------------------------------------------------
# PROXY — Proxy layer settings (v1: disabled)
# ----------------------------------------------------------------
proxy:
  enabled: false
  # Type: boolean | Default: false
  # Description: Set to true in v2 to enable proxy rotation.
  #   In v1, leave as false. Direct residential IP + authenticated session is sufficient.
  provider: none
  # Type: string | Values: none | brightdata | oxylabs | smartproxy | custom
  rotation_mode: round_robin
  proxy_list_file: data/proxies.txt

# ----------------------------------------------------------------
# REVENUE GATES — From Wave 19–20 revenue model
# ----------------------------------------------------------------
revenue_gates:
  target_net_usd: 30000
  # Type: float | Default: 30000
  # Description: Target net revenue after Fiverr 20% share ($30k net = $37.5k gross)

  target_gross_usd: 37500
  # Type: float | Default: 37500
  # Description: Required gross revenue to achieve target_net_usd

  fiverr_share: 0.20
  # Type: float (0.0–1.0) | Default: 0.20
  # Description: Fiverr's commission rate (20% of order value)

  gates:
    - month: 4
      target_gross: 1720
      floor_gross: 1200
      # If cumulative gross is below floor_gross at this month gate → RED alert
    - month: 6
      target_gross: 4770
      floor_gross: 3500
    - month: 9
      target_gross: 17795
      floor_gross: 13000
    - month: 10
      target_gross: 25045
      floor_gross: null
    - month: 12
      target_gross: 37500
      floor_gross: null

# ----------------------------------------------------------------
# DATABASE — SQLite / PostgreSQL settings
# ----------------------------------------------------------------
database:
  provider: sqlite
  # Type: string | Values: sqlite | postgresql | Default: sqlite

  sqlite_path: data/db/fiverr_research.db
  # Type: string (path) | Default: data/db/fiverr_research.db
  # Description: SQLite database file path (used when provider = sqlite)

  postgresql_url: null
  # Type: string | Default: null
  # Description: PostgreSQL connection URL (used when provider = postgresql)
  #   Format: postgresql+psycopg2://user:password@host:port/dbname
  #   Set via environment variable for security: ${DATABASE_URL}

  echo_sql: false
  # Type: boolean | Default: false
  # Description: Set to true to log all SQL statements (useful for debugging)

# ----------------------------------------------------------------
# CLUSTERING — Keyword clustering settings
# ----------------------------------------------------------------
clustering:
  algorithm: kmeans
  # Type: string | Values: kmeans | dbscan | Default: kmeans
  # Description: scikit-learn clustering algorithm for keyword grouping

  n_clusters_per_niche: auto
  # Type: integer or "auto" | Default: auto
  # Description: Number of clusters per niche for KMeans.
  #   auto = system chooses based on keyword count (roughly sqrt(n_keywords / 2))
  #   Override with a specific integer to force cluster count

  min_cluster_size: 3
  # Type: integer | Default: 3
  # Description: Minimum keywords required to form a cluster (DBSCAN only)

  dbscan_eps: 0.3
  # Type: float | Default: 0.3
  # Description: DBSCAN epsilon parameter (maximum distance for neighborhood membership)

# ----------------------------------------------------------------
# EXPORTS — Report and export settings
# ----------------------------------------------------------------
exports:
  output_dir: data/exports
  # Type: string (path) | Default: data/exports

  formats:
    csv: true
    excel: true
    pdf: true
    markdown: true
    # Type: boolean | Default: all true
    # Description: Which export formats to generate after each run

  pdf_template: src/reporting/templates/opportunity_report.html
  # Type: string (path) | Description: Jinja2/HTML template for PDF report

  include_recommendations: true
  # Type: boolean | Default: true
  # Description: Whether to include LLM recommendation outputs in PDF/Excel exports

# ----------------------------------------------------------------
# ALERTS — Staleness and opportunity alert settings
# ----------------------------------------------------------------
alerts:
  stale_data_warning_hours: 120
  # Type: integer | Default: 120 (5 days)
  # Description: Raise a staleness alert when PRD keyword data is older than this many hours

  new_strong_go_notify: true
  # Type: boolean | Default: true
  # Description: Show a dashboard notification when a new STRONG GO keyword appears
  #   (i.e., a keyword that was not STRONG GO in the previous run)

  run_failure_notify: true
  # Type: boolean | Default: true
  # Description: Show a dashboard alert if any HIGH-impact job ends in DEAD_LETTER status

  llm_cost_alert_daily_usd: 5.00
  # Type: float | Default: 5.00
  # Description: Alias of llm.cost_alert_daily_usd — can be set in either location

# ----------------------------------------------------------------
# NICHES — All 9 research niche profiles
# (See NICHE_CONFIG_DESIGN.md in 01_vision for full per-niche YAML)
# ----------------------------------------------------------------
niches:
  # ... (all 9 niche profiles — see NICHE_CONFIG_DESIGN.md for the complete YAML)
  # Each niche follows the 17-field schema documented in NICHE_CONFIG_DESIGN.md
```

---

## Field Change Impact Reference

Changes to certain fields trigger automatic side effects at run start:

| Field Changed | Side Effect | Recalculation Needed? |
|---|---|---|
| `scoring.active_profile` | ⚡ Score recalculation for all keywords | Yes — run --mode score-only or full |
| `scoring.profiles.*` (any weight) | ⚡ Score recalculation | Yes |
| `scoring.thresholds.*` | ⚡ GO/PASS tag re-assignment | Yes — run --mode score-only |
| `llm.models.tier_high` | ⚡ Existing cache still valid; new calls use new model | No recalculation needed |
| `llm.models.embeddings` | ⚡ All keyword embeddings invalidated | Yes — run --mode keyword-only to re-embed |
| `niches[*].depth` | ⚡ Niche Depth Dispatcher reads new depth on next run | No recalculation; new collection run needed |
| `niches[*].gating.gate_passed` | Gate lifted; niche promoted to configured depth | Needs collect + analyze + score on next run |
| `niches[*].fiverr.seed_keywords` | New keywords added to expansion queue | Needs keyword-only or full run |
| `pacing.*` | Applied immediately on next run | No |
| `scheduler.jobs.weekly_full_run.cron` | APScheduler re-registers the job on next startup | No |
| `llm.cache_ttl_hours` | Affects future cache entries only | No |
| `llm.max_tpm` | Applied immediately on next run | No |

---

## Config Validation Rules (Enforced at Startup)

```python
class SystemConfig(BaseModel):
    # Scoring profile weights must sum to 1.0
    @validator("scoring")
    def validate_scoring_weights(cls, scoring):
        for profile_name, profile in scoring.profiles.items():
            weight_sum = sum(profile.dict().values())
            if not (0.999 <= weight_sum <= 1.001):  # float tolerance
                raise ValueError(
                    f"Scoring profile '{profile_name}' weights sum to {weight_sum:.4f}, must be 1.0"
                )
        return scoring

    # Active profile must exist in profiles dict
    @validator("scoring")
    def validate_active_profile(cls, scoring):
        if scoring.active_profile not in scoring.profiles:
            raise ValueError(
                f"scoring.active_profile '{scoring.active_profile}' not found in scoring.profiles"
            )
        return scoring

    # Niche slot numbers must be unique and sequential
    @validator("niches")
    def validate_niche_slots(cls, niches):
        slots = [n.slot for n in niches]
        if len(slots) != len(set(slots)):
            raise ValueError("Niche slot numbers must be unique")
        return niches

    # At least one niche must be active (depth != keyword_only or feasibility)
    @validator("niches")
    def validate_active_niches(cls, niches):
        active = [n for n in niches if n.collection.depth in ("full", "standard")]
        if not active:
            raise ValueError("At least one niche must have depth = full or standard")
        return niches
```
