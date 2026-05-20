# Decision Log — Wave 1 Additions
# Fiverr Research System

*(Append to existing DECISION_LOG.md — DL-025 through DL-028)*

---

## DL-025 — Niche Profile Schema: 17-Field Structure Finalized

| Field | Value |
|---|---|
| Decision | The niche profile schema in config.yaml uses 17 top-level sections: id, slot, name, tier, collection (depth/top_n_gigs/top_n_sellers), fiverr (primary_category_path/alternative/seed_keywords/autocomplete_collect), external_sources (google_trends/reddit/youtube), llm (model overrides + 3 boolean flags), scoring (profile_override), gating (enabled/gate_description/gate_passed), auto_promotion (eligible/promote_after_runs/thresholds), metadata (wave_locked/launch_status/pricing/exclusions/notes). |
| Rationale | A single unified schema for both Tier 1 and Tier 2 niches eliminates branching logic in the orchestrator. Values differ, not structure. |
| Wave Decided | 1 |

---

## DL-026 — Multi-Niche Job Queue: 5 Priority Tiers

| Field | Value |
|---|---|
| Decision | Collection jobs are prioritized in 5 tiers: CRITICAL (PRD/Slot 1), HIGH (Slots 5/6/7 — Python Auto, AI Tool, AI Agent), STANDARD (Slots 8/9 — Workflow Auto, Python Scraping), LOW (Slots 2/3 — gated Tier 1 keyword_only), BACKGROUND (Slot 4 — MCP feasibility). |
| Rationale | PRD must always complete first. Tier 2 high-AOV niches (AI Agent, AI Tool) get priority over lower-AOV niches (Workflow Auto, Python Scraping). Gated Tier 1 niches run last since their keyword_only depth requires minimal resources. |
| Wave Decided | 1 |

---

## DL-027 — Auto-Promotion Algorithm for Tier 2 Niches

| Field | Value |
|---|---|
| Decision | After 3 completed runs, the system calculates average Final Recommendation Score for all Tier 2 niches with auto_promotion.eligible: true. Top 2 scoring niches (if score >= promote_threshold_score, default 65.0) are promoted to full depth. The lowest scoring niche (if score < demote_threshold_score, default 35.0) is demoted to keyword_only. Mid-tier niches remain at standard. Changes are logged in run_logs and displayed as dashboard notifications. Manual config.yaml depth settings override auto-promotion. |
| Rationale | Prevents the system from spending full collection resources on Tier 2 niches that prove uncompetitive, while automatically deepening research on the niches that show the strongest opportunity signal. |
| Wave Decided | 1 |

---

## DL-028 — LLM-Assisted Niche Profile Generation CLI Command

| Field | Value |
|---|---|
| Decision | A CLI command python run.py --mode generate-niche-profile --description "[niche description]" uses gpt-4o-mini to suggest seed keywords and a likely Fiverr category path, then generates a draft niche profile YAML block printed to the terminal for user review before manual insertion into config.yaml. |
| Rationale | Keeps config.yaml as the single source of truth while reducing friction of adding new niches. User always reviews and approves before any niche is added to the active run queue. |
| Wave Decided | 1 |
