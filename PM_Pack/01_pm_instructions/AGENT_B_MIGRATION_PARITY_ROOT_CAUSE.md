# RECURRING AGENT B MIGRATION GAP — ROOT CAUSE ANALYSIS & PERMANENT FIX
# Document: PM_Pack/01_pm_instructions/AGENT_B_MIGRATION_PARITY_ROOT_CAUSE.md
# Author: PM (post-C055 review) | Date: 2026-06-01
# Status: RESOLVED — §11 added to AGENT_EXECUTION_STRATEGY.md; protocols added to B and C prompt templates

---

## 1. THE SYMPTOM (what happened in C055 and why it matters)

Cycle 055 was BLOCKED at G7 (migration footprint) after Agent D ran PRAGMA table_info on
data/cycle037_live.db and found that src/models/discovery_outcome.py now defines four ORM
Mapped[] columns that do not exist in any migration file:

  run_id        VARCHAR(64)    — added by C055 Agent B to DiscoveryOutcome
  niche_id      VARCHAR(128)   — added by C055 Agent B to DiscoveryOutcome
  keyword_text  VARCHAR(256)   — added by C055 Agent B to DiscoveryOutcome
  created_at    DATETIME       — added by C055 Agent B to DiscoveryOutcome

The existing migration_06_discovery_outcomes_srdi_columns.py only provisions:
  id, is_invalid, is_contaminated, relevance_score, contamination_reason

On any DB that was migrated before C055 (i.e., all production + CI + golden DBs), a SQLAlchemy
flush() on a DiscoveryOutcome row that touches run_id, niche_id, or keyword_text would raise
OperationalError: table discovery_outcomes has no column named run_id.

Agent B explicitly wrote in HANDOFF_B: "Migration added: No (existing R8 columns populated)."
That statement was factually wrong for the four new columns, but Agent B believed it because
the runtime write paths B focused on only read/write is_invalid, is_contaminated, relevance_score,
and contamination_reason — the four NEW model fields were present as ORM columns but not yet
exercised in any runtime write path that B tested.

Agent C repeated the same mistake: "Footprint assessment: clean (no new migration introduced;
existing additive R8 columns are reused and populated)." Agent C checked that the columns used
in _record_outcome() existed in the migration. C did NOT cross-check all Mapped[] columns in the
modified model file against the actual DB schema via PRAGMA.

Agent D caught it at G7 via PRAGMA table_info — the correct safety net. But the block forced
a costly remediation cycle (Agent B fix + D re-gate) that should have been caught before push.

---

## 2. ROOT CAUSE ANALYSIS (why it happens repeatedly)

### Root cause A — Agent B's "migration checklist" is wrong-directional.
B checks: "Are the columns I'm writing to at runtime covered by an existing migration?"
B should check: "Does every Mapped[] column in every modified model file have a migration ADD COLUMN?"

These are different. B's check passes when runtime paths only write to pre-existing columns
even though new model fields were added. B's model-first check would catch ALL unmigrated columns
regardless of whether a runtime path exercises them today.

### Root cause B — Agent C's migration footprint check is also wrong-directional.
C checks: "Did git diff show any new migration file? No → footprint is clean."
C should check: "For every src/models/*.py file in the diff, run PRAGMA table_info on the CI DB
and compare against all ORM Mapped[] columns. Any ORM column absent from the DB = MIGRATION GAP → NO-GO."

C's current check cannot detect a model that gained new Mapped[] columns without a new migration
file. The absence of a new migration file is not evidence of footprint cleanliness — it is
evidence only that no new migration was written, which is exactly the problem.

### Root cause C — No automated enforcement.
There is no test that fails when an ORM Mapped[] column is not present in the DB schema.
SQLAlchemy's test infrastructure (in-memory SQLite created from ORM metadata) will always have
all columns because metadata creation uses the Python class definitions. Only the incremental
migration path (the production/CI path) exposes the gap. This gap is structural and must be
caught procedurally by B and C.

### Why it is RECURRING:
- The strategy doc had no explicit MODEL-MIGRATION PARITY RULE.
- Agent B prompts listed migration footprint as "add a migration if schema changes" but did
  not require the per-column enumeration pass.
- Agent C prompts listed "verify migration footprint" as "confirm no new migration file if
  no schema changes needed" — inverting the logic.
- Both failure modes produce passing CI / passing tests / passing Agent C GO verdict,
  because tests run on fresh ORM-metadata-created DBs. Only Agent D's PRAGMA probe or
  runtime on a migrated DB reveals the gap.

---

## 3. THE FIX (what was changed)

### 3.1 Strategy doc — new §11 MODEL-MIGRATION PARITY RULE (added 2026-06-01)
See AGENT_EXECUTION_STRATEGY.md §11 for the authoritative binding rule. Summary:
  - For every src/models/*.py file modified in a cycle, Agent B MUST produce a
    MODEL-MIGRATION PARITY TABLE before committing: enumerate every Mapped[] column,
    identify which migration adds it (or confirm original table creation), and for
    any gap immediately write a migration.
  - Agent C MUST run the PRAGMA cross-check: for every modified model file, run
    PRAGMA table_info(<tablename>) on a migrated DB (the CI DB or golden DB), list
    the columns, compare with ORM Mapped[], and treat any gap as NO-GO immediately.
  - This rule is BLOCKING at both Agent B (pre-commit) and Agent C (pre-verdict).

### 3.2 C055 remediation
migration_10_discovery_outcome_context_cols.py adds (idempotent ALTER TABLE):
  - run_id VARCHAR(64)
  - niche_id VARCHAR(128)
  - keyword_text VARCHAR(256)
  - created_at DATETIME DEFAULT (CURRENT_TIMESTAMP)
Registered in run_srdi_r8_migrations.py after migration_09.
Codex thread on PR #64 resolved with migration commit SHA.

### 3.3 C056 prompts (all 6 agents)
All C056 Agent B and C prompts now carry the §11 parity protocol verbatim (per §8.4.2
mandatory content-block manifest). The new protocol is not advisory — it is a pre-commit
gate for B and a pre-verdict gate for C.

### 3.4 C056 Agent B — catch-up parity audit
C056 Agent B MUST run the MODEL-MIGRATION PARITY AUDIT on ALL model files modified
across C050-C055 (discovery_outcome, keyword_score, keyword, gig, search_result,
external_signal, result_set_validation, market, competitor_profile) as a one-time
retroactive compliance check. Any gaps found → new migration, same session.

---

## 4. DETECTION PROTOCOL (§11 verbatim — reference for prompt authors)

### Agent B — pre-commit mandatory step (BLOCKING)
For every file F in (git diff --name-only develop..HEAD -- src/models/):
  1. Open F and list EVERY Mapped[X] column field (name + type).
  2. For each field, identify which migration file contains:
       ALTER TABLE <table> ADD COLUMN <field_name>
     or the original CREATE TABLE statement if it was part of table creation.
  3. Build the parity table:
       | Column | Type | Migration that adds it | Present in mig? |
       |--------|------|------------------------|-----------------|
  4. For any row where Present=NO: write a new migration immediately using the
     idempotent _add_column() pattern from existing migrations (see migration_06 or
     migration_09 as templates). Register it in run_srdi_r8_migrations.py after the
     highest-numbered existing migration. Run apply() against data/foundation_gate_ci.db.
     Confirm PRAGMA table_info shows the column. Add to commit. DO NOT commit without
     the migration.
  5. Add the completed parity table to the HANDOFF_B / AGENT_B report.

### Agent C — mandatory PRAGMA cross-check (GO/NO-GO, BLOCKING)
For every file F in (git diff --name-only develop..HEAD -- src/models/):
  1. Run: py -3.12 -c "from sqlalchemy import create_engine, inspect; e=create_engine('sqlite:///data/foundation_gate_ci.db'); print([c['name'] for c in inspect(e).get_columns('<tablename>')])"
  2. Run: grep -n "Mapped\[" src/models/<modelfile>.py | grep "mapped_column"
  3. Compare. Every ORM field must appear in the PRAGMA output.
  4. ANY gap = IMMEDIATE NO-GO — do not proceed to GO verdict. Route the fix to Agent B.
  5. Record the cross-check output in AGENT_C report under "Model-migration parity cross-check".

---

## 5. LESSONS FOR FUTURE CYCLES

a) "Tests pass" does NOT mean "schema is correct for incremental migration path."
   Tests use ORM-metadata-created DBs that always have all columns. Never substitute
   a passing test suite for a PRAGMA verification against a migrated DB.

b) "No new migration file" does NOT mean "no schema change."
   It means no one wrote a migration. Those are very different facts.

c) The presence of new Mapped[] columns in a model file IS a schema change,
   regardless of whether any runtime path currently writes to those columns.
   A column that exists only in the ORM but not in the DB is a time-bomb
   that will fail the first time any path flushes a row that includes it.

d) Agent D's G7 PRAGMA probe is the last line of defense, not the first.
   Catches are expensive (block + remediation cycle). Prevention at B and C
   is always cheaper.
