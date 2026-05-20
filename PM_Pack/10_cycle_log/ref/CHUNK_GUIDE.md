# CHUNK GUIDE — Token-Efficient Loading Recipes
# PURPOSE: Tell the PM exactly what to load for each task type
# RULE: Never load more than ~8,000 tokens of ref files per cycle

---

## Loading Budget Per Cycle

| Budget Item | Max Tokens | Notes |
|---|---|---|
| Hydration files | ~1,500 | HYDRATION_HEADER + STATE_SNAPSHOT |
| PM instruction files | ~2,000 | PROMPT_TEMPLATE + PM_REPLY_CHECKLIST |
| Reference files | ~8,000 | Spec files needed for current tasks |
| Total per cycle | ~11,500 | Fits in any context window |

---

## Loading Recipes by Task Type

### Recipe: "Generate prompts for Epic 01 (Foundation)"
Load these in order (~3,500 tokens):
1. ref/todo/EPIC_01_FOUNDATION.md — full file (133 lines, ~1,300 tokens)
2. ref/dod/DOD_EPIC_01.md — full file (171 lines, ~1,700 tokens)
3. ref/project_plan/02_architecture/CONFIG_SCHEMA.md — lines 1-50 only (~500 tokens)
DO NOT load: SCHEMA.md full (too big), load only the table section you need

### Recipe: "Generate prompts for Epic 02 (Collection)"
Load these (~4,000 tokens):
1. ref/todo/EPIC_02_COLLECTION.md — full file (231 lines, ~2,300 tokens)
2. ref/dod/DOD_EPIC_02.md — full file (144 lines, ~1,400 tokens)
3. ref/project_plan/04_collection/PACING_MODEL.md — first 100 lines only
DO NOT load: COLLECTION_WORKFLOWS.md full (666 lines), load only the stage you need

### Recipe: "Generate prompts for Epic 03 (Analysis)"
Load these (~3,000 tokens):
1. ref/todo/EPIC_03_ANALYSIS.md — full file (124 lines, ~1,200 tokens)
2. ref/dod/DOD_EPIC_03.md — full file (98 lines, ~1,000 tokens)
3. One spec file per task (e.g., LLM_PROMPT_TEMPLATES.md for LLM tasks)

### Recipe: "Generate prompts for Epic 04 (Scoring)"
Load these (~2,800 tokens):
1. ref/todo/EPIC_04_SCORING.md — full file (131 lines, ~1,300 tokens)
2. ref/dod/DOD_EPIC_04.md — full file (41 lines, ~400 tokens)
3. The specific score spec file for each task (DEMAND_SCORE.md, etc.)
NOTE: Each scoring spec is 150-250 lines — load only the one you're implementing

### Recipe: "Generate prompts for Epic 05 (Recommendations)"
1. ref/todo/EPIC_05_RECOMMENDATIONS.md (98 lines)
2. ref/dod/DOD_EPIC_05.md (133 lines)
3. ref/project_plan/06_analysis/RECOMMENDATION_ENGINE.md (first 200 lines)

### Recipe: "Generate prompts for Epic 06 (Pricing)"
1. ref/todo/EPIC_06_PRICING.md (108 lines)
2. ref/dod/DOD_EPIC_06.md (77 lines)
3. ref/project_plan/09_pricing/NEW_SELLER_PRICING_MODEL.md (first 200 lines)

### Recipe: "Generate prompts for Epic 07 (Discovery)"
1. ref/todo/EPIC_07_DISCOVERY.md (114 lines)
2. ref/dod/DOD_EPIC_07.md (78 lines)
3. ref/project_plan/10_discovery/DISCOVERY_ENGINE_ARCHITECTURE.md (first 200 lines)

### Recipe: "Generate prompts for Epic 08 (Playbook)"
1. ref/todo/EPIC_08_PLAYBOOK.md (98 lines)
2. ref/dod/DOD_EPIC_08.md (75 lines)
3. ref/project_plan/11_playbook/SELLER_SETUP_PLAYBOOK.md (first 200 lines)

### Recipe: "Generate prompts for Epic 09 (Dashboard)"
1. ref/todo/EPIC_09_DASHBOARD.md (228 lines)
2. ref/dod/DOD_EPIC_09.md (173 lines)
3. ref/project_plan/07_reporting/DASHBOARD_PLAN.md (first 200 lines)

### Recipe: "Generate prompts for Epic 10 (Integration)"
1. ref/todo/EPIC_10_INTEGRATION.md (169 lines)
2. ref/dod/DOD_EPIC_10.md (177 lines)

---

## Anti-Patterns (NEVER do these)

| Anti-Pattern | Why Bad | Do Instead |
|---|---|---|
| Load all 74 project_plan files | Would exhaust ~70,000 tokens | Load only files for current tasks |
| Load SCHEMA.md in full (1041 lines) | ~10,000 tokens for one file | Load only the table section needed |
| Load all 10 EPIC todo files | ~15,000 tokens | Load only the active epic |
| Load all 10 DOD files | ~12,000 tokens | Load only the DOD for active epic |
| Load "just in case" files | Wastes tokens | Use TOPIC_MAP to find exact file |
| Re-load files already in context | Double-counts tokens | Track what's loaded this cycle |

---

## Quick Reference: File to Load by Agent

| Agent | Always Load (for prompts) | Load On-Demand |
|---|---|---|
| Agent A | EPIC_01 todo + DOD_01 (or EPIC_10 + DOD_10) | CONFIG_SCHEMA, SCHEMA (specific tables) |
| Agent B | EPIC_02 todo + DOD_02 | COLLECTION_WORKFLOWS (specific stage), PLAYWRIGHT_SESSION_DESIGN |
| Agent C | Active epic todo + DOD | Specific scoring/analysis spec for current tasks |
| Agent D | EPIC_08/09 todo + DOD_08/09 | DASHBOARD_PLAN (specific page), DESIGN_SYSTEM |
