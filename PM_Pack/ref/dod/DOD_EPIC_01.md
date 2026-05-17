# DOD — EPIC 01: Foundation & Infrastructure
# Fiverr Research System — Definitions of Done & Acceptance Criteria

---

## Story 1.1 — Project Scaffolding

### Definition of Done
- [ ] All directories exist and match the specified structure
- [ ] `pip install -e .` completes without errors
- [ ] `playwright install chromium` installs browser binary successfully
- [ ] `.env.example` contains all required environment variables
- [ ] `.gitignore` prevents data/, .env, __pycache__ from being committed
- [ ] README.md contains setup instructions that a new developer can follow from zero to running

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.1.1 | Running `pip install -e .` from project root installs all dependencies | Run command, verify exit code 0 |
| AC-1.1.2 | `python -c "import playwright; import sqlalchemy; import pydantic; import openai; import streamlit"` succeeds | Run command, verify no ImportError |
| AC-1.1.3 | `playwright install chromium` exits 0 and Chromium binary exists | Run command, check browser path |
| AC-1.1.4 | All directories in task 1.1.1 exist after project creation | `os.path.isdir()` check for each |
| AC-1.1.5 | README.md contains sections: Overview, Prerequisites, Installation, Configuration, Running, Architecture | Check file contents |

---

## Story 1.2 — Configuration System

### Definition of Done
- [ ] config.yaml loads without errors using ConfigLoader
- [ ] All 9 niches are present with valid pricing, category paths, and seed keywords
- [ ] 4 scoring profiles are loadable and have correct weight distributions (sum to 1.0)
- [ ] Invalid config files raise clear Pydantic ValidationError with field names
- [ ] Environment variables override config.yaml values

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.2.1 | `ConfigLoader("config.yaml").load()` returns a valid Config object | Unit test |
| AC-1.2.2 | `config.get_niche("prd_ai_saas")` returns NicheConfig with name "PRD / AI SaaS MVP Roadmap" | Unit test |
| AC-1.2.3 | Each of 4 scoring profiles has weights that sum to 1.0 ± 0.001 | `assert abs(sum(profile.weights.values()) - 1.0) < 0.001` |
| AC-1.2.4 | Config with missing `niche_id` field raises `ValidationError` mentioning "niche_id" | Unit test with invalid YAML |
| AC-1.2.5 | Setting `OPENAI_API_KEY` env var overrides config.yaml value | Unit test with os.environ mock |
| AC-1.2.6 | All 9 niches have `category_path` starting with a valid Fiverr category prefix | Regex validation test |
| AC-1.2.7 | Niche pricing tiers are ascending: basic < standard < premium for all 9 niches | Loop assertion test |
| AC-1.2.8 | Discovery config has valid `skill_profile` with non-empty `primary_skills` list | Unit test |

---

## Story 1.3 — Database Models

### Definition of Done
- [ ] All 28 models create tables successfully via `Base.metadata.create_all()`
- [ ] All foreign key relationships resolve without errors
- [ ] JSON fields (packages, gig_extras, score_components, etc.) serialize and deserialize correctly
- [ ] All indexes are created for query-critical columns
- [ ] Model unit tests cover creation, read, update, delete for each model

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.3.1 | `Base.metadata.create_all(engine)` creates **at least 28 tables** (current implementation creates 30 — 28 spec tables + 2 report tables + collection runtime tables; see DL-025) | Integration test against SQLite |
| AC-1.3.2 | Creating a Keyword with all required fields and committing does not raise | Unit test |
| AC-1.3.3 | Creating a Gig with `packages={"basic": {"price": 50}}` JSON field, reading back returns dict | Roundtrip test |
| AC-1.3.4 | Keyword → KeywordScore relationship: `keyword.scores` returns related scores | Relationship test |
| AC-1.3.5 | Keyword → Gig many-to-many via KeywordGigAssociation works bidirectionally | Association test |
| AC-1.3.6 | KeywordScore model accepts all 11 score fields as nullable Float | Null insertion test |
| AC-1.3.7 | Recommendation model's 14 JSON fields (gig_titles, package_structure, pricing_strategy, etc.) roundtrip correctly | Roundtrip test with sample data |
| AC-1.3.8 | Discovery fields on Keyword model (is_discovery, hypothesis_confidence, discovery_mode) are present and default correctly | Default value test |
| AC-1.3.9 | GigVisualAnalysis model's classification fields accept all enum values from GIG_VISUAL_ANALYSIS.md | Enum insertion test |
| AC-1.3.10 | `init_db.py` creates database file if it doesn't exist, skips if tables already present | Idempotency test |
| AC-1.3.11 | All indexed columns (`keyword_id`, `niche_id`, `run_id`, etc.) have indexes confirmed via inspector | Schema inspection test |

---

## Story 1.4 — CLI Entry Point

### Definition of Done
- [ ] `python run.py --mode full` starts the pipeline orchestrator
- [ ] All 8 run modes are accepted
- [ ] Invalid mode shows help text with valid options
- [ ] Run ID is generated and logged at start
- [ ] Ctrl+C gracefully saves checkpoint and exits
- [ ] `python run.py init-db` creates database tables
- [ ] `python run.py dashboard` launches Streamlit on localhost:8501

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.4.1 | `python run.py --mode full` prints "Starting run {run_id} in mode: full" | CLI output test |
| AC-1.4.2 | `python run.py --mode invalid` prints error listing valid modes | CLI test with capture |
| AC-1.4.3 | `python run.py init-db` creates fiverr_research.db in data/ directory | File existence check |
| AC-1.4.4 | `python run.py --mode resume` reads latest checkpoint and prints last completed stage | CLI test with pre-seeded checkpoint |
| AC-1.4.5 | Run ID format matches `run_{YYYYMMDD}_{HHMMSS}_{mode}` pattern | Regex test |
| AC-1.4.6 | RunLog entry is created in database at run start with status="RUNNING" | DB assertion after run start |
| AC-1.4.7 | KeyboardInterrupt during run sets RunLog.status="CANCELLED" and saves checkpoint | Signal handler test |

---

## Story 1.5 — LLM Client and Cache

### Definition of Done
- [ ] LLMClient calls OpenAI API and returns structured responses
- [ ] Cache prevents duplicate API calls for identical prompts
- [ ] Cost per call is calculated and logged to llm_usage_logs
- [ ] Self-correction retry fixes common JSON formatting issues
- [ ] Jinja2 templates render with the RecommendationContext object
- [ ] Cache TTL is enforced (expired entries return cache miss)

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.5.1 | `LLMClient.complete(prompt, model="gpt-4o-mini", temperature=0.2)` returns a string response | Integration test (mocked or live API) |
| AC-1.5.2 | Two identical calls with same prompt return the same result; second call has `cache_hit=True` | Unit test with mock |
| AC-1.5.3 | `build_cache_key("gpt-4o", 0.2, "test prompt")` returns 64-char hex string | Unit test |
| AC-1.5.4 | Cache entry with TTL=1 hour expires after 1 hour (use time mock) | Unit test with freezegun |
| AC-1.5.5 | Cost for gpt-4o call with 1000 input + 500 output tokens = $0.0125 | Unit test (price table) |
| AC-1.5.6 | On `ValidationError`, retry appends error text and makes one more call | Unit test with mock that fails first, succeeds second |
| AC-1.5.7 | `render_template("gig_titles.j2", context)` returns a string with context variables substituted | Unit test with sample context |
| AC-1.5.8 | LLMUsageLog entry is created for every API call (not cache hits) | DB assertion test |

---

## Story 1.6 — Utility Modules

### Definition of Done
- [ ] All utility functions have docstrings and type hints
- [ ] All functions have unit tests with edge cases

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.6.1 | `format_duration(7380)` returns "2h 3m" | Unit test |
| AC-1.6.2 | `format_duration(45)` returns "45s" | Unit test |
| AC-1.6.3 | `validate_price(50.0)` returns True; `validate_price(-5.0)` returns False | Unit test |
| AC-1.6.4 | `jaccard_similarity("ai saas prd", "ai saas product requirements")` returns float between 0-1 | Unit test |
| AC-1.6.5 | `sha256_hash("test")` returns consistent 64-char hex string | Idempotency test |
| AC-1.6.6 | `ensure_export_dirs()` creates all export subdirectories | Directory existence test |

---

## Story 1.7 — Niche Seed Data

### Definition of Done
- [ ] 9 seed YAML files exist with 6-8 keywords each
- [ ] Import script inserts all seeds into keywords table
- [ ] Seeds have source="seed" and correct niche_id associations
- [ ] Re-running import does not create duplicates

### Acceptance Criteria
| AC ID | Criteria | Validation Method |
|---|---|---|
| AC-1.7.1 | Each of 9 YAML files contains `niche_id` and `keywords` list with 6-8 entries | File validation test |
| AC-1.7.2 | After import, `db.query(Keyword).count()` equals total seed keywords across all files | DB count test |
| AC-1.7.3 | All imported keywords have `source="seed"` | DB filter test |
| AC-1.7.4 | Running import twice does not duplicate keywords (upsert behavior) | Idempotency test |
| AC-1.7.5 | Seed keywords match the seed lists from CONFIG_SCHEMA.md / NICHE_CONFIG_DESIGN.md | Content comparison test |

---

## Epic 01 — Overall Definition of Done

The Foundation epic is DONE when:

1. ✅ `python run.py init-db` creates a valid database with all 28 tables
2. ✅ `python run.py --mode full` starts and logs a run (even if subsequent stages are not yet implemented — it should reach Stage 1 and exit cleanly)
3. ✅ Config loads all 9 niches with valid data
4. ✅ LLM client can make a test call and cache the result
5. ✅ All seed keywords are imported
6. ✅ All unit tests pass (pytest runs green)
7. ✅ No Python import errors when running `python -c "from src.models import *; from src.config import *; from src.llm import *"`
