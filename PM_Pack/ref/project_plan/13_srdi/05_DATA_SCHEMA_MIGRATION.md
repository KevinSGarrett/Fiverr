# 05 — SRDI Data Schema & Migration Plan
# Search Relevance & Data Integrity Initiative
# Fiverr Research System

**Source:** WAVE_I (authoritative). **Owning epic:** R8. **Tier:** 0 (ships first).

All changes are **additive** — no column is dropped, renamed, or type-changed. NULL = include (backward compatible).

---

## 1. COMPLETE COLUMN INVENTORY

### 1.1 New table: `result_set_validations` (M1)
```
id PK · keyword_id FK→keywords (idx) · run_id (idx)
result_set_relevance_score REAL NOT NULL DEFAULT 1.0
total_gigs_analyzed INT · relevant_gig_count INT · sponsored_gig_count INT · organic_relevant_count INT
category_contamination_flag BOOL · ghost_market_flag BOOL
used_fallback_strictness BOOL · fallback_strictness_used VARCHAR(20)
confidence_deduction REAL NOT NULL DEFAULT 0.0
llm_validated BOOL · llm_relevant_count INT · llm_verdict VARCHAR(20)
contamination_explanation VARCHAR(500) · dominant_competing_service VARCHAR(200)
per_gig_relevance JSON · validation_warnings JSON · validated_at DATETIME
UNIQUE(keyword_id, run_id)
```

### 1.2 `gigs` additive (M2)
`is_sponsored` BOOL (idx) · `is_zombie` BOOL (idx) · `zombie_score` REAL · `zombie_signals` JSON · `last_reviewed_at` DATETIME · `relevance_flag` BOOL (idx) · `relevance_score` REAL · `category_path` VARCHAR(200)

### 1.3 `search_results` additive (M3)
`search_strictness_used` VARCHAR(20) NOT NULL DEFAULT 'NONE' · `result_set_relevance_score` REAL · `category_contamination_flag` BOOL · `ghost_market_flag` BOOL · `sponsored_gig_count` INT DEFAULT 0 · `organic_gig_count` INT · `pages_collected` INT DEFAULT 1

### 1.4 `keyword_scores` additive (M4)
`relevance_qualifier` REAL DEFAULT 1.0 · `trc_reliability_score` REAL · `qualified_trc` REAL · `sponsored_gigs_excluded` INT DEFAULT 0 · `zombie_gigs_excluded` INT DEFAULT 0 · `clean_gig_count` INT

### 1.5 `keywords` additive (M5)
`discovery_needs_recollection` BOOL DEFAULT FALSE · `pre_validation_data` JSON · `specificity_confidence` REAL

### 1.6 `discovery_outcomes` additive (M6)
`is_invalid` BOOL DEFAULT FALSE · `is_contaminated` BOOL DEFAULT FALSE · `invalid_reason` VARCHAR · `relevance_score` REAL · `pre_validation_passed` BOOL

### 1.7 `external_signals` additive (M-ext)
`fiverr_relevance_qualifier` REAL · `signal_quality_score` REAL

---

## 2. MIGRATION ORDER (MANDATORY)

| # | Migration | Creates/Alters | Why This Order |
|---|---|---|---|
| M1 | `create_result_set_validations_table` | New table + 5 indexes | Foundation; no FK deps |
| M2 | `extend_gigs_table_relevance_integrity` | 8 cols + 4 indexes | Flags consumed by R3/R4/R5/R10 |
| M3 | `extend_search_results_relevance_integrity` | 7 cols + 3 indexes | Strictness/ghost flags by R1/R2/R10 |
| M4 | `extend_keyword_scores_integrity` | 6 cols | Populated by R4; read by R10 |
| M5 | `extend_keywords_discovery_integrity` | 3 cols + 1 index | Discovery (R6) |
| M6 | `extend_discovery_outcomes_integrity` | 5 cols + 2 indexes | Discovery outcomes (R6) |
| M-ext | `extend_external_signals_quality` | 2 cols | R7 (after M1) |

Each migration is **idempotent**: guard every `ALTER TABLE ADD COLUMN` with column-exists check.

---

## 3. CANONICAL DDL

```sql
-- M1: New result_set_validations table
CREATE TABLE IF NOT EXISTS result_set_validations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    keyword_id INTEGER NOT NULL REFERENCES keywords(id),
    run_id VARCHAR NOT NULL,
    result_set_relevance_score REAL NOT NULL DEFAULT 1.0,
    total_gigs_analyzed INTEGER NOT NULL DEFAULT 0,
    relevant_gig_count INTEGER NOT NULL DEFAULT 0,
    sponsored_gig_count INTEGER NOT NULL DEFAULT 0,
    organic_relevant_count INTEGER NOT NULL DEFAULT 0,
    category_contamination_flag BOOLEAN DEFAULT FALSE,
    ghost_market_flag BOOLEAN DEFAULT FALSE,
    used_fallback_strictness BOOLEAN DEFAULT FALSE,
    fallback_strictness_used VARCHAR(20),
    confidence_deduction REAL NOT NULL DEFAULT 0.0,
    llm_validated BOOLEAN DEFAULT FALSE,
    llm_relevant_count INTEGER,
    llm_verdict VARCHAR(20),
    contamination_explanation VARCHAR(500),
    dominant_competing_service VARCHAR(200),
    per_gig_relevance JSON,
    validation_warnings JSON,
    validated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_rsv_keyword_run UNIQUE (keyword_id, run_id)
);
CREATE INDEX IF NOT EXISTS idx_rsv_keyword_id ON result_set_validations(keyword_id);
CREATE INDEX IF NOT EXISTS idx_rsv_run_id ON result_set_validations(run_id);
CREATE INDEX IF NOT EXISTS idx_rsv_keyword_run ON result_set_validations(keyword_id, run_id);
CREATE INDEX IF NOT EXISTS idx_rsv_ghost_market ON result_set_validations(ghost_market_flag) WHERE ghost_market_flag = TRUE;
CREATE INDEX IF NOT EXISTS idx_rsv_contamination ON result_set_validations(category_contamination_flag) WHERE category_contamination_flag = TRUE;

-- M2: Gigs extension (each guarded with column-exists check)
ALTER TABLE gigs ADD COLUMN is_sponsored     BOOLEAN;
ALTER TABLE gigs ADD COLUMN is_zombie        BOOLEAN;
ALTER TABLE gigs ADD COLUMN zombie_score     REAL;
ALTER TABLE gigs ADD COLUMN zombie_signals   JSON;
ALTER TABLE gigs ADD COLUMN last_reviewed_at DATETIME;
ALTER TABLE gigs ADD COLUMN relevance_flag   BOOLEAN;
ALTER TABLE gigs ADD COLUMN relevance_score  REAL;
ALTER TABLE gigs ADD COLUMN category_path    VARCHAR(200);
CREATE INDEX IF NOT EXISTS idx_gigs_is_sponsored ON gigs(is_sponsored) WHERE is_sponsored = TRUE;
CREATE INDEX IF NOT EXISTS idx_gigs_is_zombie    ON gigs(is_zombie)    WHERE is_zombie    = TRUE;
CREATE INDEX IF NOT EXISTS idx_gigs_relevance    ON gigs(relevance_flag);
CREATE INDEX IF NOT EXISTS idx_gigs_scoring_filter ON gigs(is_sponsored, is_zombie, relevance_flag);

-- M3: SearchResult extension
ALTER TABLE search_results ADD COLUMN search_strictness_used      VARCHAR(20) NOT NULL DEFAULT 'NONE';
ALTER TABLE search_results ADD COLUMN result_set_relevance_score  REAL;
ALTER TABLE search_results ADD COLUMN category_contamination_flag BOOLEAN DEFAULT FALSE;
ALTER TABLE search_results ADD COLUMN ghost_market_flag           BOOLEAN DEFAULT FALSE;
ALTER TABLE search_results ADD COLUMN sponsored_gig_count         INTEGER DEFAULT 0;
ALTER TABLE search_results ADD COLUMN organic_gig_count           INTEGER;
ALTER TABLE search_results ADD COLUMN pages_collected             INTEGER DEFAULT 1;
CREATE INDEX IF NOT EXISTS idx_sr_strictness    ON search_results(search_strictness_used);
CREATE INDEX IF NOT EXISTS idx_sr_ghost_market  ON search_results(ghost_market_flag) WHERE ghost_market_flag = TRUE;
CREATE INDEX IF NOT EXISTS idx_sr_ghost_keyword ON search_results(keyword_id, ghost_market_flag);

-- M4: KeywordScore extension
ALTER TABLE keyword_scores ADD COLUMN relevance_qualifier     REAL DEFAULT 1.0;
ALTER TABLE keyword_scores ADD COLUMN trc_reliability_score   REAL;
ALTER TABLE keyword_scores ADD COLUMN qualified_trc           REAL;
ALTER TABLE keyword_scores ADD COLUMN sponsored_gigs_excluded INTEGER DEFAULT 0;
ALTER TABLE keyword_scores ADD COLUMN zombie_gigs_excluded    INTEGER DEFAULT 0;
ALTER TABLE keyword_scores ADD COLUMN clean_gig_count         INTEGER;

-- M5: Keywords extension
ALTER TABLE keywords ADD COLUMN discovery_needs_recollection BOOLEAN DEFAULT FALSE;
ALTER TABLE keywords ADD COLUMN pre_validation_data          JSON;
ALTER TABLE keywords ADD COLUMN specificity_confidence       REAL;
CREATE INDEX IF NOT EXISTS idx_kw_needs_recollection ON keywords(discovery_needs_recollection) WHERE discovery_needs_recollection = TRUE;

-- M6: DiscoveryOutcome extension
ALTER TABLE discovery_outcomes ADD COLUMN is_invalid            BOOLEAN DEFAULT FALSE;
ALTER TABLE discovery_outcomes ADD COLUMN is_contaminated       BOOLEAN DEFAULT FALSE;
ALTER TABLE discovery_outcomes ADD COLUMN invalid_reason        VARCHAR;
ALTER TABLE discovery_outcomes ADD COLUMN relevance_score       REAL;
ALTER TABLE discovery_outcomes ADD COLUMN pre_validation_passed BOOLEAN;
CREATE INDEX IF NOT EXISTS idx_do_is_invalid      ON discovery_outcomes(is_invalid)      WHERE is_invalid      = TRUE;
CREATE INDEX IF NOT EXISTS idx_do_is_contaminated ON discovery_outcomes(is_contaminated) WHERE is_contaminated = TRUE;

-- M-ext: ExternalSignal extension
ALTER TABLE external_signals ADD COLUMN fiverr_relevance_qualifier REAL;
ALTER TABLE external_signals ADD COLUMN signal_quality_score       REAL;
```

---

## 4. BACKWARD-COMPATIBILITY CONTRACT

| Column | NULL Behavior | Consuming Code Guard |
|---|---|---|
| `gigs.is_sponsored` | NULL → treat as organic (include) | `.isnot(True)` |
| `gigs.is_zombie` | NULL → non-zombie (include) | `.isnot(True)` |
| `gigs.relevance_flag` | NULL → include | `is not False` |
| RSV row absent | No deduction, no filter, no block | `if rsv is None: pass` |
| `search_strictness_used` | NULL/NONE → legacy; no retroactive deduction | `if used == 'NONE': deduct` (forward only) |
| Trends qualifier absent | Default 0.65 | `or 0.65` |

**Net effect:** M1–M6 applied with consuming reads disabled → **byte-identical scores** to pre-migration baseline (golden-run diff AC-U3).

---

## 5. ROLLBACK PROCEDURE

1. **Forward-safe pause:** disable consuming reads via config toggles. Schema stays; behavior reverts.
2. **Full rollback:** drop new indexes → `DROP COLUMN` added columns (or restore from pre-migration snapshot) → `DROP TABLE result_set_validations`. Reverse order: M-ext → M6 → M1.
3. **Always snapshot first:** copy live DB before M1.

---

## 6. MIGRATION VERIFICATION CHECKLIST

- [ ] Snapshot of live DB taken and stored
- [ ] M1–M6 (+M-ext) applied in order on snapshot; all succeed
- [ ] Re-run M1–M6 on migrated snapshot → no-ops (idempotency verified)
- [ ] Schema-parity test: every SQLAlchemy column has matching DB column and vice versa
- [ ] Golden-run diff: scores identical to baseline with consuming reads disabled (AC-U3)
- [ ] Storage delta measured < 1 MB/run
- [ ] Rollback rehearsed on snapshot; DB returns to baseline
- [ ] `base.py` registers `ResultSetValidation`; `Keyword.result_set_validations` relationship resolves

---

*Cross-references: `02_ARCHITECTURE_IMPACT.md` §5 (data objects), `epics/R8_SCHEMA_EXTENSIONS_MIGRATIONS.md` (implementation stories/tasks)*
