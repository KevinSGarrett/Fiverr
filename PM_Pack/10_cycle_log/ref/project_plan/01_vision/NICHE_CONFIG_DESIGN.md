# Niche Configuration Design
# Fiverr Research System — Wave 1

**Document Status:** Complete
**Wave:** 1 — Vision and Product Design
**Purpose:** Define the complete niche profile schema for config.yaml, multi-niche run architecture, gating logic, auto-promotion design, and example YAML for all 9 confirmed niches.

---

## Design Principles

1. Every niche is fully configured in config.yaml — no code changes required to add, remove, or adjust a niche
2. Tier 1 and Tier 2 niches share the same schema — only the values differ
3. Depth settings control collection scope, LLM analysis scope, and scoring scope in a single field
4. Gating logic is config-driven — gates are checked at run start and depth is set accordingly
5. Auto-promotion evaluates Tier 2 scores after 3 completed runs and adjusts depth automatically
6. All seed keywords, category paths, and scoring overrides live in the niche profile — no hardcoding

---

## Niche Depth Levels

| Depth Level | Collection Scope | LLM Analysis Scope | Scoring Scope | Use Case |
|---|---|---|---|---|
| `full` | Top 20 gigs + all seller profiles | All LLM tasks (gpt-4o + gpt-4o-mini) | All 11 scores | PRD (Slot 1) — primary niche, every run |
| `standard` | Top 10 gigs + top seller profiles | gpt-4o-mini tasks only + gpt-4o for top 5 gigs | All 11 scores | Tier 2 niches — active research |
| `keyword_only` | Fiverr search results only (no gig detail, no seller) | Keyword expansion + intent classification only | Scores 1–3 only (Demand, Competition, Opportunity) | Tier 1 gated niches before gate is passed |
| `feasibility` | Top 5 gig detail only | gpt-4o-mini tasks + gpt-4o for weakness detection only | Scores 1–5 | MCP (Slot 4) — feasibility research mode |

---

## Complete Niche Profile Schema

```yaml
# Each niche under the niches: key uses this schema
niches:
  - id: string                        # unique identifier, snake_case (e.g., "prd_ai_saas")
    slot: integer                     # portfolio slot number (1–9)
    name: string                      # human-readable niche name
    tier: integer                     # 1 = locked from Wave 10, 2 = new addition
    
    collection:
      depth: string                   # full | standard | keyword_only | feasibility
      top_n_gigs: integer             # override top-N gig detail collection (default by depth)
      top_n_sellers: integer          # override top-N seller profile collection
      
    fiverr:
      primary_category_path: string   # verified category URL path (from DL-023)
      alternative_category_path: string  # optional fallback path
      seed_keywords:                  # list of validated seed keywords
        - string
      autocomplete_collect: boolean   # whether to collect Fiverr autocomplete for these seeds
      
    external_sources:
      google_trends: boolean          # collect Google Trends data for this niche
      reddit: boolean                 # collect Reddit demand signals
      youtube: boolean                # collect YouTube search counts
      
    llm:
      model_override_high: string     # override gpt-4o for this niche (null = use global)
      model_override_low: string      # override gpt-4o-mini for this niche (null = use global)
      gig_quality_analysis: boolean   # run full LLM gig quality analysis (overrides depth default)
      competitor_synthesis: boolean   # run LLM competitor cluster synthesis
      recommendation_generation: boolean  # generate LLM recommendations for GO keywords
      
    scoring:
      profile_override: string        # override active scoring profile for this niche (null = global)
      
    gating:
      enabled: boolean                # whether this niche has a gate before full research
      gate_description: string        # human-readable description of the gate condition
      gate_passed: boolean            # manually set to true when gate is passed
      
    auto_promotion:
      eligible: boolean               # whether this niche can be auto-promoted (Tier 2 only)
      promote_after_runs: integer     # number of completed runs before auto-promotion evaluation
      promote_threshold_score: float  # minimum Final Recommendation Score avg to trigger promotion
      demote_threshold_score: float   # score below which niche is demoted to keyword_only
      
    metadata:
      wave_locked: string             # wave when this niche was locked into the portfolio
      launch_status: string           # GO | GATED | FEASIBILITY | RESEARCH
      starter_price_basic: integer    # from Wave 20 pricing (for Profitability Score context)
      starter_price_standard: integer
      starter_price_premium: integer
      hard_exclusions:                # list of scope exclusions for recommendation engine
        - string
      notes: string                   # free-text notes
```

---

## Multi-Niche Run Architecture

### Run Sequence

All 9 niches are processed in a single run using the following priority order:

```
Run Start
  │
  ├─ Stage 1–2: Keyword expansion
  │    All 9 niches processed in parallel (keyword expansion is fast)
  │    PRD keywords added to priority queue first
  │
  ├─ Stage 3: Fiverr search collection
  │    Processed in priority order: Slot 1 → Slot 5 → Slot 6 → Slot 7 → Slot 8 → Slot 9
  │    Then gated Tier 1: Slot 2 → Slot 3 → Slot 4 (keyword_only depth)
  │
  ├─ Stage 4: Gig detail collection
  │    Slot 1 (full, top 20) → Slot 5–9 (standard, top 10) → Slot 4 (feasibility, top 5)
  │    Slots 2–3 skipped (keyword_only)
  │
  ├─ Stage 5: Competitor seller profiles
  │    Slot 1 (all sellers from top 20) → Slot 5–9 (top sellers per keyword)
  │    Slots 2–4 skipped or limited
  │
  ├─ Stage 6: External validation
  │    All 9 niches — Google Trends batched by niche seed keywords
  │    Reddit API per niche seed list
  │
  ├─ Stage 7: LLM gig quality analysis
  │    Slot 1 (full: gpt-4o on top 10 gigs per keyword)
  │    Slots 5–9 (standard: gpt-4o on top 5, gpt-4o-mini on top 10)
  │    Slot 4 (feasibility: gpt-4o-mini only)
  │    Slots 2–3 skipped
  │
  ├─ Stage 8–9: Seller strength + clustering
  │    Same depth logic as Stages 7
  │
  ├─ Stages 10–12: Scoring + confidence + ranking
  │    All 9 niches scored at appropriate depth
  │    keyword_only niches get Scores 1–3 only
  │    feasibility niches get Scores 1–5 only
  │
  ├─ Stage 13: Recommendation generation
  │    Only STRONG GO and CONDITIONAL GO keywords above threshold
  │    Only for niches with recommendation_generation: true in config
  │    Slot 1 always generates recommendations; Tier 2 generate after 1+ completed run
  │
  └─ Stages 14–15: Reporting + run log
       All 9 niches included in dashboard refresh and run summary
```

### Niche Priority Queue

The job queue assigns priority tiers to collection jobs:

| Priority | Niches | Rationale |
|---|---|---|
| CRITICAL | Slot 1 (PRD) | Primary launch niche — always first |
| HIGH | Slots 5, 6, 7 (Python Auto, AI Tool, AI Agent) | Highest AOV potential in Tier 2 |
| STANDARD | Slots 8, 9 (Workflow Auto, Python Scraping) | Standard Tier 2 |
| LOW | Slots 2, 3 (Support-KB, Gumloop/Lindy) | Gated — keyword_only |
| BACKGROUND | Slot 4 (MCP) | Feasibility mode |

---

## Gating Logic

### How Gating Works

At run start, the orchestrator reads each niche's `gating.gate_passed` value. If false, the niche's depth is capped at `keyword_only` (or `feasibility` for MCP) regardless of what the depth field says. The user manually sets `gate_passed: true` in config.yaml when the gate condition is satisfied.

### Gate Conditions Per Niche

| Slot | Niche | Gate Condition |
|---|---|---|
| 2 | Support-KB | PRD proof gate passed (85/100 proof score) AND PRD has received at least 3 qualified messages AND PRD has at least 1 completed order |
| 3 | Gumloop/Lindy | Sandbox/blueprint proof exists AND at least 3 clean early PRD orders completed |
| 4 | MCP | PRD proof gate passed AND at least 5+ clean orders AND MCP feasibility sample created |

### Gate Logging

When a gated niche runs in keyword_only mode, the system logs:

```
[INFO] Niche: Support-KB (Slot 2) — running in keyword_only mode
[INFO] Gate condition: PRD proof gate not yet passed. Set gating.gate_passed: true in config.yaml to unlock full research depth.
```

---

## Auto-Promotion Logic (Tier 2 Niches)

### How Auto-Promotion Works

After 3 completed runs, the system evaluates all Tier 2 niches with `auto_promotion.eligible: true`. It calculates the average Final Recommendation Score across all keywords in each niche. The top 2 scoring niches are promoted to `full` depth. The lowest scoring niche is demoted to `keyword_only`. The mid-tier niches remain at `standard`.

### Auto-Promotion Algorithm

```python
# After run 3+, auto-promotion evaluation
tier2_niches = [n for n in niches if n.tier == 2 and n.auto_promotion.eligible]
avg_scores = {n.id: avg(final_recommendation_scores_for_niche(n)) for n in tier2_niches}

sorted_niches = sorted(avg_scores.items(), key=lambda x: x[1], reverse=True)

for rank, (niche_id, avg_score) in enumerate(sorted_niches):
    if rank < 2 and avg_score >= promote_threshold:      # top 2
        set_depth(niche_id, 'full')
    elif rank == len(sorted_niches) - 1 and avg_score < demote_threshold:  # lowest
        set_depth(niche_id, 'keyword_only')
    else:
        set_depth(niche_id, 'standard')

log_auto_promotion_changes()
update_niche_configs_table()
```

Auto-promotion changes are:
- Logged in run_logs with before/after depth for each affected niche
- Displayed in the dashboard as a "Niche Depth Updated" notification
- Reversible by manually setting depth in config.yaml (manual override takes precedence)

---

## Example config.yaml — All 9 Niches

```yaml
# ============================================================
# FIVERR RESEARCH SYSTEM — config.yaml
# All 9 niche profiles with verified category paths and seeds
# ============================================================

system:
  run_mode: full                      # full | collect-only | analyze-only | score-only | report-only | keyword-only | resume | relogin
  checkpoint_interval: 50            # write checkpoint every N records

fiverr:
  session_mode: authenticated
  session_file: data/sessions/fiverr_session.json

llm:
  provider: openai
  openai_api_key: ${OPENAI_API_KEY}
  cache_enabled: true
  cache_ttl_hours: 72
  max_tpm: 90000
  cost_alert_daily_usd: 5.00
  models:
    tier_high: gpt-4o
    tier_low: gpt-4o-mini
    embeddings: text-embedding-3-small

scoring:
  active_profile: aggressive_new_seller
  profiles:
    default:
      demand: 0.20
      competition_inv: 0.20
      opportunity: 0.25
      feasibility: 0.15
      profitability: 0.10
      intent: 0.10
      saturation_inv: 0.05
      weakness: 0.10
      trend: 0.05
    aggressive_new_seller:
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
      trend: 0.25
      demand: 0.25
      opportunity: 0.20
      competition_inv: 0.15
      feasibility: 0.10
      profitability: 0.05
      intent: 0.00
      weakness: 0.00
      saturation_inv: 0.00

pacing:
  fiverr_search:
    base_delay_seconds: 4
    jitter_seconds: 3
    max_requests_per_hour: 60
    human_events: true
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
  reddit_api:
    base_delay_seconds: 2
    jitter_seconds: 1
    max_requests_per_hour: 60

opportunity_thresholds:
  strong_go: 80
  conditional_go: 60
  monitor: 40
  caution: 20

revenue_gates:
  target_net_usd: 30000
  target_gross_usd: 37500
  fiverr_share: 0.20
  gates:
    - month: 4
      target_gross: 1720
      floor_gross: 1200
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

# ============================================================
# NICHE PROFILES — ALL 9 NICHES
# ============================================================

niches:

  # ----------------------------------------------------------
  # SLOT 1 — PRD / AI SaaS MVP Roadmap (TIER 1 — FULL DEPTH)
  # ----------------------------------------------------------
  - id: prd_ai_saas
    slot: 1
    name: "PRD / AI SaaS MVP Roadmap"
    tier: 1

    collection:
      depth: full
      top_n_gigs: 20
      top_n_sellers: 20

    fiverr:
      primary_category_path: "programming-tech/ai-coding/AI-Technology-Consulting"
      alternative_category_path: "writing-translation/technical-writing"
      seed_keywords:
        - "product requirements document"
        - "AI SaaS PRD"
        - "MVP PRD"
        - "technical roadmap AI"
        - "SaaS roadmap"
        - "AI product roadmap"
        - "developer ready PRD"
        - "PRD document writing"
        - "software requirements specification"
        - "MVP technical specification"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: true

    llm:
      model_override_high: null
      model_override_low: null
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    scoring:
      profile_override: null

    gating:
      enabled: false
      gate_description: "No gate — PRD is the primary research niche"
      gate_passed: true

    auto_promotion:
      eligible: false
      promote_after_runs: null
      promote_threshold_score: null
      demote_threshold_score: null

    metadata:
      wave_locked: "Wave 10 (confirmed Wave 20)"
      launch_status: "GO"
      starter_price_basic: 95
      starter_price_standard: 225
      starter_price_premium: 395
      hard_exclusions:
        - "No coding or software development"
        - "No UI/UX design"
        - "No full system architecture"
        - "No investor deck or pitch deck"
        - "No market research"
        - "No unlimited revisions"
      notes: "PRD must pass 85/100 proof gate before publishing. Proof assets: 3 gig images, sample PDF, FAQ/exclusions, buyer requirements."

  # ----------------------------------------------------------
  # SLOT 2 — Support-KB Readiness (TIER 1 — GATED)
  # ----------------------------------------------------------
  - id: support_kb_readiness
    slot: 2
    name: "Support-KB Readiness"
    tier: 1

    collection:
      depth: keyword_only
      top_n_gigs: 0
      top_n_sellers: 0

    fiverr:
      primary_category_path: "writing-translation/technical-writing"
      alternative_category_path: null
      seed_keywords:
        - "support knowledge base AI"
        - "chatbot handoff document"
        - "help center AI readiness"
        - "support KB audit"
        - "AI chatbot handoff"
        - "knowledge base readiness"
        - "help desk AI automation"
        - "customer support AI readiness"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: false

    llm:
      model_override_high: null
      model_override_low: null
      gig_quality_analysis: false
      competitor_synthesis: false
      recommendation_generation: false

    scoring:
      profile_override: null

    gating:
      enabled: true
      gate_description: "Gate: PRD proof gate (85/100) passed AND PRD has 3+ qualified messages AND 1+ completed PRD order"
      gate_passed: false

    auto_promotion:
      eligible: false
      promote_after_runs: null
      promote_threshold_score: null
      demote_threshold_score: null

    metadata:
      wave_locked: "Wave 10 (confirmed Wave 20)"
      launch_status: "GATED"
      starter_price_basic: 75
      starter_price_standard: 175
      starter_price_premium: 325
      hard_exclusions:
        - "No full chatbot build"
        - "No RAG pipeline build"
        - "No guaranteed deflection rates"
        - "No PII-heavy data ingestion"
      notes: "Scope is READINESS/AUDIT/HANDOFF only. 10-article audit for Basic. No full chatbot implementation."

  # ----------------------------------------------------------
  # SLOT 3 — Gumloop/Lindy Workflow (TIER 1 — GATED)
  # ----------------------------------------------------------
  - id: gumloop_lindy_workflow
    slot: 3
    name: "Gumloop/Lindy One-Workflow AI Automation"
    tier: 1

    collection:
      depth: keyword_only
      top_n_gigs: 0
      top_n_sellers: 0

    fiverr:
      primary_category_path: "programming-tech/software-development/automations-workflows"
      alternative_category_path: null
      seed_keywords:
        - "Gumloop workflow"
        - "Lindy AI automation"
        - "AI workflow automation"
        - "no-code AI workflow"
        - "Gumloop automation"
        - "Lindy workflow builder"
        - "AI process automation"
        - "no-code automation workflow"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: false

    llm:
      gig_quality_analysis: false
      competitor_synthesis: false
      recommendation_generation: false

    gating:
      enabled: true
      gate_description: "Gate: Sandbox/blueprint proof created AND 3+ clean early PRD orders completed"
      gate_passed: false

    auto_promotion:
      eligible: false

    metadata:
      wave_locked: "Wave 10 (confirmed Wave 20)"
      launch_status: "GATED"
      starter_price_basic: 95
      starter_price_standard: 195
      starter_price_premium: 350
      hard_exclusions:
        - "No live sends or writes"
        - "No scraping"
        - "No ongoing monitoring"
        - "No broad AI automation"
      notes: "Scope is BLUEPRINT/SANDBOX only. No live implementation in first 10 orders."

  # ----------------------------------------------------------
  # SLOT 4 — MCP Server / AI-Agent Integration (TIER 1 — FEASIBILITY)
  # ----------------------------------------------------------
  - id: mcp_ai_agent
    slot: 4
    name: "MCP Server / AI-Agent Integration"
    tier: 1

    collection:
      depth: feasibility
      top_n_gigs: 5
      top_n_sellers: 5

    fiverr:
      primary_category_path: "programming-tech/ai-coding/ai-agents-development"
      alternative_category_path: "programming-tech/ai-coding/ai-integrations"
      seed_keywords:
        - "MCP server integration"
        - "AI agent integration"
        - "model context protocol"
        - "MCP tool integration"
        - "MCP server Fiverr"
        - "AI agent MCP"
        - "AI agent development"
        - "autonomous AI agent"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: false

    llm:
      gig_quality_analysis: false
      competitor_synthesis: false
      recommendation_generation: false

    gating:
      enabled: true
      gate_description: "Gate: PRD proof gate passed AND 5+ clean orders AND MCP feasibility sample (public API/read-only demo) created"
      gate_passed: false

    auto_promotion:
      eligible: false

    metadata:
      wave_locked: "Wave 10 (confirmed Wave 20)"
      launch_status: "FEASIBILITY"
      starter_price_basic: 125
      starter_price_standard: 250
      starter_price_premium: 450
      hard_exclusions:
        - "No production server deployment"
        - "No regulated data"
        - "No enterprise SSO"
        - "No security certification"
        - "No unlimited debugging"
      notes: "FEASIBILITY/PROTOTYPE scope only. Public API/read-only MCP demo only until trust established."

  # ----------------------------------------------------------
  # SLOT 5 — Python Automation Scripts (TIER 2 — STANDARD)
  # ----------------------------------------------------------
  - id: python_automation
    slot: 5
    name: "Python Automation Scripts"
    tier: 2

    collection:
      depth: standard
      top_n_gigs: 10
      top_n_sellers: 10

    fiverr:
      primary_category_path: "programming-tech/buy/web-programming-services/python"
      alternative_category_path: null
      seed_keywords:
        - "Python automation script"
        - "Python automation"
        - "automate with Python"
        - "Python task automation"
        - "Python bot"
        - "Python script development"
        - "Python scripting service"
        - "automate repetitive tasks Python"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: true

    llm:
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    gating:
      enabled: false
      gate_passed: true

    auto_promotion:
      eligible: true
      promote_after_runs: 3
      promote_threshold_score: 65.0
      demote_threshold_score: 35.0

    metadata:
      wave_locked: "Wave 0 Niche Expansion"
      launch_status: "RESEARCH"
      starter_price_basic: 50
      starter_price_standard: 125
      starter_price_premium: 250
      notes: "Highest-volume Python gig type. Short deliveries, recurring buyers, fast portfolio builder."

  # ----------------------------------------------------------
  # SLOT 6 — AI Tool / LLM App Integration (TIER 2 — STANDARD)
  # ----------------------------------------------------------
  - id: ai_tool_llm_integration
    slot: 6
    name: "AI Tool / LLM App Integration"
    tier: 2

    collection:
      depth: standard
      top_n_gigs: 10
      top_n_sellers: 10

    fiverr:
      primary_category_path: "programming-tech/ai-coding/ai-integrations"
      alternative_category_path: null
      seed_keywords:
        - "LLM integration"
        - "AI tool development"
        - "OpenAI API integration"
        - "ChatGPT integration"
        - "custom AI tool"
        - "LLM app development"
        - "Claude API integration"
        - "AI API integration"
        - "GPT API development"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: true

    llm:
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    gating:
      enabled: false
      gate_passed: true

    auto_promotion:
      eligible: true
      promote_after_runs: 3
      promote_threshold_score: 65.0
      demote_threshold_score: 35.0

    metadata:
      wave_locked: "Wave 0 Niche Expansion"
      launch_status: "RESEARCH"
      starter_price_basic: 95
      starter_price_standard: 225
      starter_price_premium: 450
      notes: "Fastest-growing AI subcategory. Buyers are businesses integrating OpenAI/Claude/Gemini into products."

  # ----------------------------------------------------------
  # SLOT 7 — AI Agent Development (TIER 2 — STANDARD)
  # ----------------------------------------------------------
  - id: ai_agent_development
    slot: 7
    name: "AI Agent Development"
    tier: 2

    collection:
      depth: standard
      top_n_gigs: 10
      top_n_sellers: 10

    fiverr:
      primary_category_path: "programming-tech/ai-coding/ai-agents-development"
      alternative_category_path: null
      seed_keywords:
        - "AI agent development"
        - "autonomous AI agent"
        - "build AI agent"
        - "AI assistant development"
        - "agentic AI"
        - "AI agent Python"
        - "LangChain agent"
        - "AutoGPT agent"
        - "CrewAI agent"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: true

    llm:
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    gating:
      enabled: false
      gate_passed: true

    auto_promotion:
      eligible: true
      promote_after_runs: 3
      promote_threshold_score: 65.0
      demote_threshold_score: 35.0

    metadata:
      wave_locked: "Wave 0 Niche Expansion"
      launch_status: "RESEARCH"
      starter_price_basic: 125
      starter_price_standard: 295
      starter_price_premium: 550
      notes: "Highest AOV in entire AI coding category. Technical buyers who need implementation help."

  # ----------------------------------------------------------
  # SLOT 8 — Workflow Automation n8n/Make/Zapier (TIER 2 — STANDARD)
  # ----------------------------------------------------------
  - id: workflow_automation
    slot: 8
    name: "Workflow Automation (n8n / Make / Zapier)"
    tier: 2

    collection:
      depth: standard
      top_n_gigs: 10
      top_n_sellers: 10

    fiverr:
      primary_category_path: "programming-tech/software-development/automations-workflows"
      alternative_category_path: null
      seed_keywords:
        - "n8n automation"
        - "Make automation"
        - "Zapier automation"
        - "workflow automation"
        - "business process automation"
        - "no-code automation workflow"
        - "n8n workflow"
        - "Make.com workflow"
        - "Zapier workflow setup"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: false

    llm:
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    gating:
      enabled: false
      gate_passed: true

    auto_promotion:
      eligible: true
      promote_after_runs: 3
      promote_threshold_score: 65.0
      demote_threshold_score: 35.0

    metadata:
      wave_locked: "Wave 0 Niche Expansion"
      launch_status: "RESEARCH"
      starter_price_basic: 75
      starter_price_standard: 175
      starter_price_premium: 350
      notes: "High-demand confirmed subcategory. Avg pricing $120-140/project. Complements Gumloop/Lindy Tier 1 niche."

  # ----------------------------------------------------------
  # SLOT 9 — Python Web Scraping / Data Scripts (TIER 2 — STANDARD)
  # ----------------------------------------------------------
  - id: python_web_scraping
    slot: 9
    name: "Python Web Scraping / Data Scripts"
    tier: 2

    collection:
      depth: standard
      top_n_gigs: 10
      top_n_sellers: 10

    fiverr:
      primary_category_path: "programming-tech/buy/web-programming-services/python"
      alternative_category_path: null
      seed_keywords:
        - "Python web scraping"
        - "web scraper Python"
        - "data scraping script"
        - "BeautifulSoup scraper"
        - "website data extraction"
        - "Python data scraper"
        - "Scrapy spider"
        - "web data collection Python"
        - "custom web scraper"
      autocomplete_collect: true

    external_sources:
      google_trends: true
      reddit: true
      youtube: false

    llm:
      gig_quality_analysis: true
      competitor_synthesis: true
      recommendation_generation: true

    gating:
      enabled: false
      gate_passed: true

    auto_promotion:
      eligible: true
      promote_after_runs: 3
      promote_threshold_score: 65.0
      demote_threshold_score: 35.0

    metadata:
      wave_locked: "Wave 0 Niche Expansion"
      launch_status: "RESEARCH"
      starter_price_basic: 50
      starter_price_standard: 100
      starter_price_premium: 200
      notes: "High consistent demand. Fast deliveries. Natural entry point with strong repeat business and upsells."
```

---

## LLM-Assisted Niche Profile Generation

When the user wants to add a new niche not already in the config, they can run:

```bash
python run.py --mode generate-niche-profile --description "I want to research Streamlit dashboard development for data teams"
```

The system will:
1. Use gpt-4o-mini to suggest seed keywords for the described niche
2. Use gpt-4o-mini to suggest the most likely Fiverr category path
3. Generate a draft niche profile YAML block
4. Print the draft to the terminal for the user to review and paste into config.yaml

This keeps the config as the single source of truth while using LLM to reduce the friction of adding new niches.
