# Personas
# Fiverr Research System — Wave 1

**Document Status:** Complete
**Wave:** 1 — Vision and Product Design
**Note:** These are personas for who USES this research tool — not Fiverr buyers. All three are Fiverr sellers researching AI, Python, and automation niches.

---

## Persona 1 — The Systematic Builder

**Name:** Marcus
**Role:** Solo developer / technical freelancer building a Fiverr business alongside a full-time job
**Location:** The Woodlands, TX (or similar suburban professional context)

### Background
Marcus has 5+ years of Python development experience and has been building AI tools and automation systems for personal and client projects for 2 years. He is methodical by nature — the kind of person who built a 350-line hydration pack by hand to maintain research continuity across Claude sessions. He understands the value of systems and processes. He completed 20 waves of manual research before deciding to automate the research function entirely.

### Current Workflow (Before This System)
Marcus manually browses Fiverr search results, copies competitor data into Excel, runs formulas he built himself, writes research notes in markdown documents, and maintains a master cumulative workbook to track findings across sessions. Each research session takes 3–5 hours. He runs these sessions every few weeks. He frequently discovers that data he collected 6 weeks ago is stale when he goes to act on it.

### Goals
- Replace his manual research workflow entirely with an automated system that runs while he sleeps
- Get to the point where he opens a dashboard Monday morning and immediately knows which niche deserves attention that week
- Build a research engine that covers all 9 niches simultaneously rather than cycling through them one at a time
- Have LLM-generated gig assets ready to review so he can spend his limited time deciding and building, not researching

### Pain Points
- Research sessions eat into the hours he has available for building and publishing
- Manual data is inconsistent — what he scored 8 weeks ago used different criteria than what he'd score today
- He can only cover 1–2 niches per research session, so most niches are always operating on stale data
- Synthesizing competitor weaknesses into a differentiation angle takes hours of manual reading and note-taking
- He has no way to know when a niche has shifted — a competitor gaining 40 new reviews in a month matters, but he'd only catch it on his next manual pass

### How He Uses This System
Marcus sets the system up on a Saturday morning, runs `--mode relogin` to authenticate Fiverr, then sets a weekly APScheduler cron for Sunday nights at 11pm. Monday mornings he opens the Streamlit dashboard with coffee, reviews the run summary, checks for new STRONG GO opportunities, reads the competitor synthesis narrative for PRD, and decides what to work on that week. The entire review takes 30 minutes. He exports the recommendation card for any new STRONG GO keyword and uses it directly to draft gig assets.

### Scoring Profile He Uses
`aggressive_new_seller` — he is early-stage with zero reviews and weights New Seller Feasibility and Gig Quality Weakness highest because those determine whether he can realistically enter a niche right now.

### What Success Looks Like
After 3 months using the system, Marcus has published his PRD gig (Slot 1), begun monitoring when Support-KB hits its signal gate, has a ranked list of his 5 Tier 2 niches by opportunity score, and has spent zero hours on manual research. His research is fresher, more consistent, and more actionable than anything he produced manually in 20 waves.

---

## Persona 2 — The Opportunity Sprinter

**Name:** Daniela
**Role:** Full-time freelancer who already has some Fiverr presence and wants to expand into AI niches quickly
**Experience Level:** Intermediate — has Fiverr reviews in a different niche, understands the platform dynamics

### Background
Daniela has been a Fiverr seller in a non-AI niche (e.g., data analysis, web scraping) for 2 years and has accumulated enough reviews to achieve Level 1. She recognizes the AI wave and wants to expand into AI-adjacent niches while the opportunity window is open. She moves fast, has less patience for planning detail, and learns by doing. She wants research to tell her where to point her energy this week — not in three months.

### Current Workflow
Daniela uses Sale Samurai occasionally for keyword lookups but finds it too shallow — it tells her search volume but nothing about competitor quality, differentiation opportunities, or what gig copy would actually win. She manually browses top gigs in niches she's considering and writes quick notes. Her research is opportunistic rather than systematic.

### Goals
- Quickly identify the 2–3 highest-opportunity niches from the 9-niche portfolio that she can enter in the next 30 days
- Get actionable gig assets (titles, tags, package structures) immediately without reading dozens of competitor gigs
- Know which competitor gigs are weak so she can position her first gig to beat them on day one
- Spend her research time on verification and judgment, not data collection

### Pain Points
- Sale Samurai and similar tools give her surface-level data — she can see result counts but not whether the top sellers are actually strong or exploitable
- She doesn't have a system for tracking which niches she's investigated and when — everything lives in browser bookmarks and scattered notes
- She often starts building a gig in a niche only to discover mid-way through that the competition is stronger than she thought — wasted effort
- She wants LLM-generated gig title options because brainstorming titles takes her disproportionate time

### How She Uses This System
Daniela runs the system in `--mode keyword-only` first to get a fast competitive overview across all 9 niches. Once she sees which niches score STRONG GO or CONDITIONAL GO, she triggers `--mode analyze-only` on those niches specifically for the full LLM analysis. She reads the differentiation angle and competitor synthesis narrative, picks her target niche, and uses the recommendation card's title variants and package structure directly. Her total research time from system run to gig draft is under 2 hours.

### Scoring Profile She Uses
`profitability_focus` — she already has reviews and Level 1 status, so New Seller Feasibility is less critical for her. She weights Profitability and Conversion Intent highest because she wants niches where buyers have clear budgets and high purchase intent.

### What Success Looks Like
Daniela publishes 2 Tier 2 gigs (Python Automation and AI Tool/LLM Integration) within 30 days of first running the system, using titles and packages directly informed by the system's recommendations. Her gigs are positioned on specific competitor weaknesses rather than generic claims. She monitors the dashboard weekly for new opportunities without doing any manual browsing.

---

## Persona 3 — The Research Architect

**Name:** Priya
**Role:** Freelance consultant who treats her Fiverr business as a strategic portfolio to be optimized quarterly
**Experience Level:** Advanced — analytical background, comfortable with data, has managed multiple Fiverr gigs simultaneously

### Background
Priya approaches her Fiverr business like a product manager approaches a product portfolio. She thinks in terms of opportunity windows, revenue gates, niche sequencing, and competitive positioning. She is the kind of person who would build the Wave 19–20 revenue model herself. She has experience with data tools, is comfortable writing Python, and has opinions about how research systems should work.

### Current Workflow
Priya does quarterly deep-dive research sessions using a combination of Fiverr browsing, Google Trends, Reddit exploration, and SEO tool exports. She maintains her own scoring spreadsheet with custom formulas. She tracks competitor review velocity manually. Her research is high-quality but extremely time-intensive — 2–3 full days per quarter per niche.

### Goals
- Automate the mechanical data collection so she can focus entirely on strategic interpretation
- Have score histories per keyword so she can see which niches are trending up or down over time
- Understand LLM costs per run so she can optimize the balance between analysis depth and expense
- Use the system as a strategic portfolio management tool — not just "find good keywords" but "decide which niche to activate next quarter based on all signals"

### Pain Points
- Her quarterly research model means she's always 1–2 months behind on fast-moving niches like AI Agent Development
- She has no systematic way to detect when a competitor has significantly strengthened their position (new reviews, price changes, new gigs) between her research sessions
- LLM cost is a concern — she wants quality analysis but not an open-ended API bill
- She wants to be able to adjust scoring weights and immediately see which niche rankings change, without rebuilding formulas

### How She Uses This System
Priya runs the full system weekly and checks the dashboard on Friday afternoons as her "portfolio review." She uses the score history view to track week-over-week changes in her 9 niches. She switches between scoring profiles monthly to stress-test her portfolio from different strategic angles. She monitors the LLM cost view closely and adjusts the top-N gig analysis depth per niche based on cost vs. insight tradeoff. She uses the opportunity explanation texts in her own quarterly planning documents.

### Scoring Profile She Uses
She rotates between profiles quarterly: `default` in Q1 for baseline ranking, `trend_chaser` in Q2 to find emerging niches before they peak, `aggressive_new_seller` when evaluating new niche entry, and `profitability_focus` in Q4 for AOV optimization.

### What Success Looks Like
After 6 months, Priya has replaced all quarterly manual research with the automated system, reduced her research time from 6–9 days per quarter to 2 hours per week, has a score history showing clear trend lines for each of her 9 niches, and has activated her Tier 2 niche portfolio in priority order as determined by the system's opportunity rankings rather than intuition.
