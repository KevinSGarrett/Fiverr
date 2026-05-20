# User Stories
# Fiverr Research System — Wave 1

**Document Status:** Complete
**Wave:** 1 — Vision and Product Design
**Total Stories:** 32
**Context:** All stories are written from the perspective of a Fiverr seller researching 9 AI/Python/automation niches using this automated system.

---

## Group 1 — Seed Keyword Intake and Niche Configuration (Stages 1–2)

---

**US-001 — Configure niches from a single file**
As a Fiverr seller, I want to configure all 9 research niches and their seed keywords in a single config.yaml file, so that I never have to re-enter my research preferences after initial setup.

Acceptance Criteria:
- config.yaml accepts all 9 niche profiles in a structured YAML block
- Each niche profile contains: name, slot, tier, depth setting, seed keywords, category path, scoring profile override
- System validates config on startup and reports clear errors if any niche profile is malformed
- Changing a seed keyword list in config.yaml causes the keyword expansion module to re-run for that niche on the next run

---

**US-002 — Tier-aware depth configuration**
As a Fiverr seller, I want Tier 1 gated niches (Support-KB, Gumloop/Lindy, MCP) to automatically run at reduced research depth until I manually promote them, so that I don't waste collection time on niches I'm not ready to activate.

Acceptance Criteria:
- config.yaml supports niche_depth values: full, standard, keyword_only, feasibility
- PRD defaults to full on every run without requiring manual setting
- Gated niches default to keyword_only and log a clear message indicating their gate status
- Changing a niche from keyword_only to standard in config.yaml takes effect on the next run with no code changes

---

**US-003 — LLM-assisted niche expansion brainstorm**
As a Fiverr seller, I want the system to use GPT-4o-mini to suggest additional seed keywords and adjacent sub-niches I may not have considered, so that my keyword universe is broader than what I could generate manually.

Acceptance Criteria:
- For each seed keyword, gpt-4o-mini generates at least 10 related keywords, long-tail variants, and buyer-intent modifier combinations
- Generated suggestions are stored in keywords table with source=llm_expansion
- A separate column tracks which keywords came from LLM expansion vs. Fiverr autocomplete vs. Google suggest
- LLM-generated keywords are run through a relevance filter before being added to the collection queue

---

**US-004 — Buyer intent classification for every keyword**
As a Fiverr seller, I want every expanded keyword to be classified by buyer intent (INFORMATIONAL / CONSIDERATION / HIGH INTENT / TRANSACTIONAL), so that I prioritize collecting data for the keywords most likely to convert buyers.

Acceptance Criteria:
- gpt-4o-mini classifies every keyword in the expanded universe
- Classification stored in keywords.intent_class field
- Collection queue prioritizes HIGH INTENT and TRANSACTIONAL keywords for gig detail collection
- Dashboard filters allow viewing keywords by intent class

---

**US-005 — Fiverr autocomplete collection for all 9 niches**
As a Fiverr seller, I want the system to automatically collect Fiverr autocomplete suggestions for every seed keyword across all 9 niches, so that I capture every keyword Fiverr's own algorithm surfaces to buyers.

Acceptance Criteria:
- Playwright session navigates to Fiverr search and collects all autocomplete suggestions for each seed
- Autocomplete position (1–10) is stored alongside each suggestion
- Keywords appearing at positions 1–3 receive a bonus weight in the Demand Score
- Autocomplete collection respects pacing config and runs at natural human rate

---

## Group 2 — Fiverr Collection (Stages 3–5)

---

**US-006 — Authenticated Fiverr search collection**
As a Fiverr seller, I want the system to collect search results using my own authenticated Fiverr session, so that I see the same data that logged-in buyers see and gain access to any fields not visible to guests.

Acceptance Criteria:
- System loads saved session from data/sessions/fiverr_session.json before every collection run
- If session is expired, system triggers headed re-login and saves new session before continuing
- Collection run logs whether it used an authenticated or unauthenticated session for each job
- Gig cards collected include all fields visible in authenticated view

---

**US-007 — First-run Fiverr login with guided prompt**
As a Fiverr seller, I want the system to open a visible browser window on the first run and prompt me to log in, so that I can complete any 2FA or CAPTCHA manually before the session is saved.

Acceptance Criteria:
- Running python run.py --mode relogin opens a headed Playwright browser navigated to fiverr.com
- Terminal displays: "Please log in to Fiverr in the browser window. Press Enter when complete."
- After Enter is pressed, system verifies the login state before saving the session
- Session saved to data/sessions/fiverr_session.json with chmod 600 permissions
- Subsequent runs load the saved session and operate headlessly

---

**US-008 — Natural human-rate browsing on all Fiverr sessions**
As a Fiverr seller, I want all Fiverr collection to simulate natural human browsing behavior, so that my collection runs at a realistic pace that does not stand out from normal user traffic.

Acceptance Criteria:
- Every page load is followed by a 2–8 second read delay (configurable, with random jitter)
- Mouse hover events occur before clicks with 100–400ms delay
- Random scroll events simulate reading after page load
- Window size is randomized per session within a realistic range
- Occasional dead navigation (loading an adjacent Fiverr page before the target) is included

---

**US-009 — Gig detail collection for top N gigs per keyword**
As a Fiverr seller, I want the system to visit the gig detail page for the top N gigs per keyword (configurable, default 20 for full depth, 10 for standard, 5 for feasibility), so that I have complete gig data beyond what appears in search result cards.

Acceptance Criteria:
- System collects from gig detail pages: full description, all package tiers with prices and deliverables, all gig extras, all tags, FAQ full text, video presence flag, portfolio item count, exact review count and rating, visible review snippets
- Collection respects the depth setting per niche (full=top 20, standard=top 10, feasibility=top 5)
- Collected data stored in gigs table with source_url and collected_at
- Pacing applies between every gig detail page visit

---

**US-010 — Competitor seller profile collection**
As a Fiverr seller, I want the system to visit the seller profile page for every unique seller appearing in the top results across all keywords, so that I understand not just individual gigs but the full competitive landscape of sellers I'm up against.

Acceptance Criteria:
- System collects from seller profile pages: seller level, member since date, response time/rate, all gig titles, total reviews, portfolio count, seller badges
- Deduplicates sellers across niches — each seller profile is only visited once per TTL window
- Seller data stored in sellers table linked to gigs
- System logs how many unique sellers were collected per run

---

**US-011 — Checkpoint-based resumption after interruption**
As a Fiverr seller, I want collection runs to save checkpoints every 50 records so that if my computer sleeps, crashes, or loses internet, I can resume the run from where it left off rather than starting over.

Acceptance Criteria:
- Checkpoint files written to data/checkpoints/[run_id]/[stage].json every 50 records
- Running python run.py --mode resume detects the most recent checkpoint and resumes from it
- Resumed run logs clearly which stage and record it resumed from
- Checkpoint files are cleaned up automatically after a run completes successfully

---

## Group 3 — External Demand Validation (Stage 6)

---

**US-012 — Google Trends data for all confirmed seed keywords**
As a Fiverr seller, I want the system to collect Google Trends 12-month interest scores and slope data for all confirmed seed keywords across all 9 niches, so that I have external demand validation beyond Fiverr's own search counts.

Acceptance Criteria:
- pytrends collects 12-month interest score, 3-month score, and rising/declining slope for every seed keyword
- Keywords are batched (up to 5 per pytrends request) to respect rate limits
- If pytrends returns a 429, system pauses for 10 minutes and retries with exponential backoff
- Trends data stored in external_signals table with signal_type=google_trends and collected_at timestamp

---

**US-013 — Reddit demand intent signal extraction**
As a Fiverr seller, I want the system to search relevant subreddits for each keyword and use GPT-4o-mini to extract buyer intent signals from post text, so that I understand whether real buyers are actively looking for these services beyond just search volume.

Acceptance Criteria:
- Reddit API searches at least 5 relevant subreddits per niche for each keyword
- gpt-4o-mini parses collected post text and returns a demand intent score (0–10) and a list of representative intent phrases
- Intent phrases like "I need someone to X", "looking for X service", "can anyone recommend X" are flagged as HIGH INTENT
- Results stored in external_signals table with signal_type=reddit_demand_intent

---

**US-014 — Google Trends data does not block the run if unavailable**
As a Fiverr seller, I want the run to continue and complete even if Google Trends is unavailable or rate-limited, so that a single blocked data source doesn't prevent all other research from completing.

Acceptance Criteria:
- Google Trends failure is logged and flagged as a missing data warning
- Confidence Score for affected keywords is reduced by 0.15
- All other pipeline stages continue normally
- Dashboard shows a "Google Trends: unavailable for this run" notice on affected keywords

---

## Group 4 — LLM Analysis (Stages 7–9)

---

**US-015 — Gig description quality scoring with specific weakness detection**
As a Fiverr seller, I want the system to use GPT-4o to score every top competitor gig's description and identify specific exploitable weaknesses, so that I enter every niche knowing exactly what to do better — not just knowing that competitors exist.

Acceptance Criteria:
- gpt-4o scores each gig description on: clarity, benefit language, proof elements, CTA strength, package differentiation, niche specificity (0–100 per dimension)
- gpt-4o returns a structured weakness list per gig: vague promises, missing proof, generic copy, unclear deliverables, no FAQ, no video, poor thumbnail
- Weakness data stored as JSON in gig_quality_scores.weakness_list
- At least one weakness is identified for 80%+ of gigs in saturated niches

---

**US-016 — Gig quality analysis runs only on top N gigs to control LLM cost**
As a Fiverr seller, I want full GPT-4o gig quality analysis to run only on the top N gigs per keyword (configurable, default 10 for full depth), so that I get maximum intelligence on the gigs I actually need to beat without burning unnecessary API budget on long-tail gigs.

Acceptance Criteria:
- Full gpt-4o description analysis runs on top 10 gigs for full-depth niches, top 5 for standard-depth
- gpt-4o-mini title and thumbnail analysis runs on all collected gigs
- LLM usage log shows per-stage token usage so cost can be traced by analysis tier
- Config allows overriding the top-N limit per niche

---

**US-017 — Competitor cluster synthesis narrative**
As a Fiverr seller, I want the system to synthesize a strategic competitive landscape narrative for each keyword cluster using GPT-4o, so that I understand who dominates the niche, why they're winning, and exactly where a new entrant can gain a foothold.

Acceptance Criteria:
- gpt-4o receives the top 10 competitor profiles per cluster and returns: dominant sellers (names + why), positioning gaps, specific exploitable weaknesses, entry feasibility assessment (0–10)
- Synthesis stored in competitor_analysis table linked to the keyword cluster
- Dashboard competitor page shows the narrative prominently alongside the score breakdown
- Synthesis runs once per cluster per run (not per keyword) to control cost

---

**US-018 — Keyword clustering with LLM-generated theme labels**
As a Fiverr seller, I want all expanded keywords to be grouped into semantic clusters with clear human-readable labels, so that I can view my research organized by theme (e.g., "PRD — MVP Scoping", "PRD — Technical Roadmap") rather than as a flat list of hundreds of individual keywords.

Acceptance Criteria:
- text-embedding-3-small generates semantic vectors for all keywords
- scikit-learn KMeans or DBSCAN groups keywords into clusters (configurable cluster count)
- gpt-4o-mini generates a human-readable theme label for each cluster
- Cluster labels and keyword assignments stored in keyword_clusters table
- Dashboard keyword page allows browsing keywords by cluster

---

**US-019 — LLM cache prevents redundant API spend**
As a Fiverr seller, I want every LLM call to be cached so that running the system twice in the same week on unchanged data does not charge me twice for the same analysis, so that weekly re-runs are economical.

Acceptance Criteria:
- Every LLM call checks the llm_cache table before calling the API
- Cache key = SHA-256(model + temperature + prompt_text)
- Cache hit rate is logged per run and displayed in the dashboard LLM cost view
- On a re-run with no data changes, at least 60% of LLM calls should be served from cache
- Stale source data (past TTL) correctly invalidates the corresponding cache entry

---

## Group 5 — Scoring (Stages 10–12)

---

**US-020 — All 11 scores calculated automatically after collection**
As a Fiverr seller, I want all 11 scores to be calculated automatically after every collection run without any manual input, so that I always have current scores without maintaining Excel formulas or running manual calculations.

Acceptance Criteria:
- All 11 scores (Demand, Competition, Opportunity, Feasibility, Profitability, Intent, Saturation, Gig Quality Weakness, Trend, Final, Confidence) are calculated for every keyword that has completed collection
- Scores stored in keyword_scores table with scored_at timestamp
- Score calculation runs immediately after Stage 9 completes for each niche
- Recalculation can be triggered independently with python run.py --mode score-only

---

**US-021 — Confidence Modifier reduces scores for thin data**
As a Fiverr seller, I want the Final Recommendation Score to be automatically reduced when data is incomplete or stale, so that I never confidently act on a high score that was built on thin or outdated evidence.

Acceptance Criteria:
- Confidence Modifier is calculated per keyword based on data completeness, freshness, and source diversity
- Final Recommendation Score = weighted composite × Confidence Modifier (never higher than the composite alone)
- Keywords with Confidence Modifier below 0.5 are visually flagged in the dashboard with a warning indicator
- The confidence_reason field on every keyword explains in plain text exactly what reduced the confidence

---

**US-022 — Named scoring profiles switchable from config**
As a Fiverr seller, I want to switch between scoring profiles (default, aggressive_new_seller, profitability_focus, trend_chaser) by changing a single line in config.yaml, so that I can re-score my entire keyword universe with a different strategic lens without rebuilding anything.

Acceptance Criteria:
- Setting scoring.active_profile in config.yaml to any named profile triggers score recalculation with the new weights
- All named profiles are validated: weights must sum to 1.0
- Profile name is logged in each score record so historical scores are traceable to their profile
- Dashboard shows which scoring profile was used for the currently displayed scores

---

**US-023 — Opportunity ranking with GO/PASS tags**
As a Fiverr seller, I want every keyword to be tagged with a clear decision label (STRONG GO, CONDITIONAL GO, MONITOR, CAUTION, PASS) based on its Final Recommendation Score, so that I can immediately see which keywords deserve action without manually interpreting numeric scores.

Acceptance Criteria:
- Tags applied based on configurable score thresholds (default: 80–100=STRONG GO, 60–79=CONDITIONAL GO, 40–59=MONITOR, 20–39=CAUTION, 0–19=PASS)
- Tags stored in opportunity_rankings table alongside final scores
- Dashboard opportunities page defaults to showing STRONG GO and CONDITIONAL GO keywords first
- Thresholds are configurable in config.yaml without code changes

---

## Group 6 — Recommendation Generation (Stage 13)

---

**US-024 — Complete LLM gig recommendation for every STRONG GO keyword**
As a Fiverr seller, I want a complete gig recommendation package generated for every keyword scoring STRONG GO, including titles, tags, packages, description outline, FAQ, buyer persona, and differentiation angle, so that I can begin building a gig immediately without any additional research.

Acceptance Criteria:
- For every STRONG GO keyword: 5 optimized gig title variants, 5 tag sets, starter/standard/premium package structure, full gig description outline, 5–7 FAQ entries, buyer persona, thumbnail concept direction, upsell structure, and differentiation angle
- All outputs are LLM-generated (gpt-4o for strategic outputs, gpt-4o-mini for templated outputs)
- Full recommendation stored as structured JSON in recommendations table
- Dashboard recommendation cards display all components with copy-paste formatting

---

**US-025 — Differentiation angle grounded in competitor weaknesses**
As a Fiverr seller, I want the differentiation angle for each recommendation to be grounded in specific competitor weaknesses identified during gig quality analysis, so that my positioning is based on real evidence rather than generic advice.

Acceptance Criteria:
- gpt-4o receives the competitor weakness list from Stage 7 when generating the differentiation angle
- Differentiation angle explicitly references the specific weaknesses being exploited (e.g., "Top 10 gigs in this niche have generic descriptions with no proof elements — position as the specialist with a verifiable process")
- Red flags field includes any warning signals that might undermine the differentiation angle
- Differentiation angle is regenerated if competitor weakness data is refreshed

---

**US-026 — Niche viability assessment for every opportunity**
As a Fiverr seller, I want a strategic niche viability paragraph generated by GPT-4o for every GO-tier opportunity, synthesizing all signals into a single plain-English judgment, so that I can read one paragraph and understand whether to act on this opportunity.

Acceptance Criteria:
- gpt-4o receives all 11 scores, confidence modifier, competitor synthesis, trend classification, and revenue gate context before generating the viability paragraph
- Paragraph is 100–200 words and covers: why this niche is an opportunity right now, what the competitive risk is, what the seller needs to do to win, and any timing considerations
- Stored in recommendations.niche_viability_assessment
- Dashboard shows viability paragraph prominently at the top of each recommendation card

---

**US-027 — Red flags are explicit and actionable**
As a Fiverr seller, I want every recommendation to include a specific list of red flags rather than just a generic warning, so that I make informed decisions about risk before pursuing any opportunity.

Acceptance Criteria:
- gpt-4o scans all collected data fields for warning signals: high competition with no visible weak spots, declining trend, low conversion intent, saturation indicators, missing data that reduces confidence
- Red flags returned as a structured list with: flag_type, flag_description, severity (LOW/MEDIUM/HIGH)
- HIGH severity red flags are displayed prominently with a warning indicator in the dashboard
- Missing data warnings are listed separately from strategic red flags

---

## Group 7 — Reporting and Dashboard (Stages 14–15)

---

**US-028 — LLM-generated score explanation for every keyword**
As a Fiverr seller, I want every keyword's score to include a plain-English explanation generated by GPT-4o, so that I understand why a keyword scored 74 vs. 51 without needing to interpret raw numbers.

Acceptance Criteria:
- gpt-4o generates a 2–4 sentence explanation per keyword referencing the actual score component values
- Explanation stored in keyword_scores.explanation_text
- Dashboard displays the explanation directly below the score breakdown chart
- Explanation is regenerated when scores change but cached when scores are unchanged

---

**US-029 — Revenue gate tracker in the dashboard**
As a Fiverr seller, I want the dashboard to display a revenue gate tracker showing current cumulative gross vs. month 4, 6, 9, 10, and 12 targets from the Wave 19–20 revenue model, so that I can see at a glance whether I am on track toward the $30,000 net target.

Acceptance Criteria:
- Dashboard run history page includes a revenue gate section showing: target vs. actual cumulative gross for each gate month
- User manually inputs completed order values (the system does not scrape order data from Fiverr)
- Status for each gate is color-coded: GREEN (on track), YELLOW (approaching floor), RED (below floor)
- Gate floors from Wave 20 are pre-configured: Month 4 floor $1,200, Month 6 floor $3,500, Month 9 floor $13,000

---

**US-030 — LLM-generated run summary after every completed run**
As a Fiverr seller, I want a natural language run summary generated by GPT-4o-mini at the end of every run, describing what was collected, what changed since the last run, which new opportunities emerged, and what the next recommended action is, so that I get a briefing without needing to dig through raw data.

Acceptance Criteria:
- Run summary generated and stored in run_logs.summary_text and exported to data/exports/run_summary_[timestamp].md
- Summary includes: niches processed, keywords expanded, gigs collected, LLM API cost for this run, new STRONG GO opportunities since last run, top mover (keyword whose score changed most), next recommended action
- Summary is displayed on the dashboard run history page for every past run
- Summary generation uses cached LLM responses where underlying data is unchanged

---

**US-031 — Staleness alert when critical data goes stale**
As a Fiverr seller, I want the system to alert me when PRD niche keyword data or top competitor review counts go past their TTL, so that I always know when my research needs refreshing and never make decisions on stale data.

Acceptance Criteria:
- Alert fires when any PRD keyword's collected_at is older than its ttl_hours value
- Alert fires when any tracked top-competitor's seller profile data is stale
- Alerts are displayed in the dashboard header as a banner notification
- Alert log is stored in run_logs and included in the run summary

---

**US-032 — One-command weekly research refresh**
As a Fiverr seller, I want to run a single command (python run.py --mode full) on a weekly schedule and have the system automatically handle all 15 pipeline stages across all 9 niches — collection, analysis, scoring, recommendations, and reporting — so that my research is always current without any manual work after initial setup.

Acceptance Criteria:
- python run.py --mode full successfully completes all 15 stages for all 9 niches (at configured depth) without any user interaction after launch
- Run completes in under 6 hours with default pacing settings and 9 niches at their configured depths
- System sends a dashboard alert if any stage fails so the user knows to check run logs
- APScheduler config supports scheduling weekly runs via cron-style schedule in config.yaml
