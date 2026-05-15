# Label Taxonomy
# Fiverr Research System — Complete Label System

---

## Label Categories

All labels follow the format: `{category}:{value}`

---

## 1. Type Labels (Required on every PR and Issue)

| Label | Color (Hex) | Description |
|---|---|---|
| `type:feature` | `#1D76DB` | New functionality |
| `type:fix` | `#D73A4A` | Bug fix |
| `type:refactor` | `#E4E669` | Code restructuring |
| `type:test` | `#0E8A16` | Test additions/changes only |
| `type:docs` | `#0075CA` | Documentation only |
| `type:chore` | `#D4C5F9` | Dependencies, config, CI |
| `type:style` | `#FEF2C0` | Formatting, lint fixes |
| `type:perf` | `#F9D0C4` | Performance improvement |
| `type:release` | `#5319E7` | Release PR |
| `type:hotfix` | `#B60205` | Emergency production fix |
| `type:spike` | `#C2E0C6` | Research/exploration |

---

## 2. Priority Labels (Required on every PR and Issue)

| Label | Color (Hex) | Description | Response Time |
|---|---|---|---|
| `priority:P1-critical` | `#B60205` | Blocks all work, production broken | Immediate |
| `priority:P2-high` | `#D93F0B` | Blocks current epic progress | Same day |
| `priority:P3-medium` | `#FBCA04` | Important but not blocking | Within 2 days |
| `priority:P4-low` | `#0E8A16` | Nice to have, can wait | When convenient |

### Priority Assignment Guide
| Scenario | Priority |
|---|---|
| Production crash, data corruption, security vulnerability | P1 |
| Story that blocks other stories in the same epic | P2 |
| Normal story/task implementation | P3 |
| Documentation, minor refactor, nice-to-have improvement | P4 |

---

## 3. Scope Labels (Required on every PR)

| Label | Color (Hex) | Description |
|---|---|---|
| `scope:epic01-foundation` | `#C5DEF5` | Config, models, CLI, LLM client |
| `scope:epic02-collection` | `#BFD4F2` | Playwright, workflows, pacing |
| `scope:epic03-analysis` | `#B4C7E7` | Clustering, quality, competitor |
| `scope:epic04-scoring` | `#A8B8D8` | 11 score calculators, tags |
| `scope:epic05-recommendations` | `#9CABC9` | 14 LLM tasks, context, output |
| `scope:epic06-pricing` | `#8F9EBA` | KDE, entry pricing, ladder |
| `scope:epic07-discovery` | `#8391AB` | Hypothesis modes, feedback |
| `scope:epic08-playbook` | `#77849C` | Visual analysis, playbook gen |
| `scope:epic09-dashboard` | `#6B778D` | Streamlit, components, pages |
| `scope:epic10-integration` | `#5F6A7E` | Pipeline, testing, launch |
| `scope:ci-cd` | `#EDEDED` | GitHub Actions, workflows |
| `scope:deps` | `#EDEDED` | Dependency management |
| `scope:docs` | `#EDEDED` | Documentation |

---

## 4. Risk Labels (Required on every PR)

| Label | Color (Hex) | Description |
|---|---|---|
| `risk:critical` | `#B60205` | Schema migration, orchestrator core, security |
| `risk:high` | `#D93F0B` | New workflow, scoring formula, LLM prompt |
| `risk:medium` | `#FBCA04` | New feature within established patterns |
| `risk:low` | `#0E8A16` | Tests, docs, config, minor fixes |

See RISK_TIERS.md for detailed risk assessment criteria.

---

## 5. Size Labels (Auto-applied by CI)

| Label | Color (Hex) | Lines Changed |
|---|---|---|
| `size:XS` | `#EDEDED` | 1-10 |
| `size:S` | `#C2E0C6` | 11-50 |
| `size:M` | `#FEF2C0` | 51-200 |
| `size:L` | `#F9D0C4` | 201-500 |
| `size:XL` | `#E99695` | 501-1000 |
| `size:XXL` | `#B60205` | 1000+ |

---

## 6. Status Labels (Applied during PR lifecycle)

| Label | Color (Hex) | Description |
|---|---|---|
| `status:in-progress` | `#FBCA04` | Actively being worked on |
| `status:review-needed` | `#0075CA` | Ready for human review |
| `status:changes-requested` | `#D93F0B` | Review found issues |
| `status:approved` | `#0E8A16` | Approved for merge |
| `status:blocked` | `#B60205` | Blocked by dependency |
| `status:on-hold` | `#EDEDED` | Paused intentionally |
| `status:stale` | `#D4C5F9` | No activity for 3+ days |

---

## 7. Agent Labels (Applied to track which agent owns the work)

| Label | Color (Hex) | Description |
|---|---|---|
| `agent:1-infrastructure` | `#1D76DB` | Agent 1 — Foundation, CI, config |
| `agent:2-collection` | `#0E8A16` | Agent 2 — Collection engine |
| `agent:3-analysis` | `#D93F0B` | Agent 3 — Analysis, scoring, recommendations |
| `agent:4-dashboard` | `#5319E7` | Agent 4 — Dashboard, playbook, UX |
| `agent:pm-chatgpt` | `#EDEDED` | ChatGPT PM — issue creation, coordination |

---

## 8. Override Labels (Rare — requires justification)

| Label | Color (Hex) | Description |
|---|---|---|
| `override:emergency` | `#B60205` | Bypass branch protection (must be re-enabled after) |
| `override:large-pr` | `#D93F0B` | Allow XXL PR with justification |
| `override:skip-tests` | `#D93F0B` | Skip test requirement (CI-only changes) |

---

## 9. Issue-Only Labels

| Label | Color (Hex) | Description |
|---|---|---|
| `issue:bug` | `#D73A4A` | Bug report |
| `issue:enhancement` | `#A2EEEF` | Feature request |
| `issue:task` | `#0075CA` | Implementation task |
| `issue:epic` | `#5319E7` | Epic tracker |
| `issue:spike` | `#C2E0C6` | Research/investigation |
| `issue:duplicate` | `#CFD3D7` | Duplicate issue |
| `issue:wontfix` | `#FFFFFF` | Declined |
| `issue:good-first-task` | `#7057FF` | Simple task for onboarding |

---

## Label Creation Script

To create all labels programmatically:

```bash
# Install GitHub CLI: https://cli.github.com
# Then run this script from the repo root:

# Type labels
gh label create "type:feature" --color "1D76DB" --description "New functionality"
gh label create "type:fix" --color "D73A4A" --description "Bug fix"
gh label create "type:refactor" --color "E4E669" --description "Code restructuring"
gh label create "type:test" --color "0E8A16" --description "Test additions/changes"
gh label create "type:docs" --color "0075CA" --description "Documentation only"
gh label create "type:chore" --color "D4C5F9" --description "Dependencies, config, CI"
gh label create "type:style" --color "FEF2C0" --description "Formatting, lint fixes"
gh label create "type:perf" --color "F9D0C4" --description "Performance improvement"
gh label create "type:release" --color "5319E7" --description "Release PR"
gh label create "type:hotfix" --color "B60205" --description "Emergency production fix"
gh label create "type:spike" --color "C2E0C6" --description "Research/exploration"

# Priority labels
gh label create "priority:P1-critical" --color "B60205" --description "Blocks all work"
gh label create "priority:P2-high" --color "D93F0B" --description "Blocks epic progress"
gh label create "priority:P3-medium" --color "FBCA04" --description "Normal priority"
gh label create "priority:P4-low" --color "0E8A16" --description "Nice to have"

# Scope labels
gh label create "scope:epic01-foundation" --color "C5DEF5" --description "Config, models, CLI"
gh label create "scope:epic02-collection" --color "BFD4F2" --description "Playwright, workflows"
gh label create "scope:epic03-analysis" --color "B4C7E7" --description "Clustering, quality"
gh label create "scope:epic04-scoring" --color "A8B8D8" --description "Score calculators"
gh label create "scope:epic05-recommendations" --color "9CABC9" --description "LLM tasks, output"
gh label create "scope:epic06-pricing" --color "8F9EBA" --description "Pricing engine"
gh label create "scope:epic07-discovery" --color "8391AB" --description "Discovery engine"
gh label create "scope:epic08-playbook" --color "77849C" --description "Visual, playbook"
gh label create "scope:epic09-dashboard" --color "6B778D" --description "Streamlit, UX"
gh label create "scope:epic10-integration" --color "5F6A7E" --description "Testing, launch"
gh label create "scope:ci-cd" --color "EDEDED" --description "GitHub Actions"
gh label create "scope:deps" --color "EDEDED" --description "Dependencies"
gh label create "scope:docs" --color "EDEDED" --description "Documentation"

# Risk labels
gh label create "risk:critical" --color "B60205" --description "Schema, orchestrator, security"
gh label create "risk:high" --color "D93F0B" --description "New workflow, formula, prompt"
gh label create "risk:medium" --color "FBCA04" --description "New feature, established pattern"
gh label create "risk:low" --color "0E8A16" --description "Tests, docs, config"

# Size labels
gh label create "size:XS" --color "EDEDED" --description "1-10 lines"
gh label create "size:S" --color "C2E0C6" --description "11-50 lines"
gh label create "size:M" --color "FEF2C0" --description "51-200 lines"
gh label create "size:L" --color "F9D0C4" --description "201-500 lines"
gh label create "size:XL" --color "E99695" --description "501-1000 lines"
gh label create "size:XXL" --color "B60205" --description "1000+ lines - must split"

# Status labels
gh label create "status:in-progress" --color "FBCA04" --description "Actively being worked"
gh label create "status:review-needed" --color "0075CA" --description "Ready for review"
gh label create "status:changes-requested" --color "D93F0B" --description "Issues found"
gh label create "status:approved" --color "0E8A16" --description "Ready to merge"
gh label create "status:blocked" --color "B60205" --description "Blocked by dependency"
gh label create "status:on-hold" --color "EDEDED" --description "Paused"
gh label create "status:stale" --color "D4C5F9" --description "No activity 3+ days"

# Agent labels
gh label create "agent:1-infrastructure" --color "1D76DB" --description "Agent 1"
gh label create "agent:2-collection" --color "0E8A16" --description "Agent 2"
gh label create "agent:3-analysis" --color "D93F0B" --description "Agent 3"
gh label create "agent:4-dashboard" --color "5319E7" --description "Agent 4"
gh label create "agent:pm-chatgpt" --color "EDEDED" --description "ChatGPT PM"

# Override labels
gh label create "override:emergency" --color "B60205" --description "Bypass protection"
gh label create "override:large-pr" --color "D93F0B" --description "Allow XXL PR"
gh label create "override:skip-tests" --color "D93F0B" --description "Skip test requirement"

# Issue labels
gh label create "issue:bug" --color "D73A4A" --description "Bug report"
gh label create "issue:enhancement" --color "A2EEEF" --description "Feature request"
gh label create "issue:task" --color "0075CA" --description "Implementation task"
gh label create "issue:epic" --color "5319E7" --description "Epic tracker"
gh label create "issue:spike" --color "C2E0C6" --description "Research"
gh label create "issue:duplicate" --color "CFD3D7" --description "Duplicate"
gh label create "issue:wontfix" --color "FFFFFF" --description "Declined"
gh label create "issue:good-first-task" --color "7057FF" --description "Simple onboarding task"

echo "All labels created successfully!"
```

---

## Total Label Count: 52 labels across 9 categories
