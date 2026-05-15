# TASK BACKLOG — All Tasks with Status Tracking
# Updated: Cycle 001 (2026-05-13)
# Source: ref/todo/EPIC_01 through EPIC_10

---

## Status Key
- BL = Backlog (not started)
- TD = To Do (assigned to cycle)
- IP = In Progress (agent working)
- IR = In Review (PM reviewing)
- DN = Done (completed and verified)
- BK = Blocked (waiting on dependency)

---

## Epic 01: Foundation & Infrastructure (65 tasks)

| ID | Task | Status | Agent | Cycle |
|---|---|---|---|---|
| 1.1.1 | Create project directory structure | IP | A/B/D | 001 |
| 1.1.2 | Create pyproject.toml | IP | A | 001 |
| 1.1.3 | Create requirements.txt | IP | A | 001 |
| 1.1.4 | Create .env.example | IP | A | 001 |
| 1.1.5 | Create .gitignore | IP | A | 001 |
| 1.1.6 | Install Playwright browsers | IP | B | 001 |
| 1.1.7 | Create README.md | IP | D | 001 |
| 1.2.1 | Create config.yaml master template | IP | A | 001 |
| 1.2.2 | Create ConfigLoader class | IP | A | 001 |
| 1.2.3 | Create NicheConfig Pydantic model | IP | A | 001 |
| 1.2.4 | Create ScoringProfileConfig model | IP | A | 001 |
| 1.2.5 | Create CollectionConfig model | IP | A | 001 |
| 1.2.6 | Create DiscoveryConfig model | IP | A | 001 |
| 1.2.7 | Create config validation tests | IP | A | 001 |
| 1.3.1 | Create database engine setup | IP | A | 001 |
| 1.3.2 | Create Base model | IP | A | 001 |
| 1.3.3 | Create NicheConfig model | IP | A | 001 |
| 1.3.4 | Create Keyword model | BL | — | — |
| 1.3.5 | Create SearchResult model | BL | — | — |
| 1.3.6 | Create Gig model | BL | — | — |
| 1.3.7 | Create Seller model | BL | — | — |
| 1.3.8 | Create KeywordGigAssociation model | BL | — | — |
| 1.3.9 | Create ExternalSignal model | BL | — | — |
| 1.3.10 | Create KeywordScore model | BL | — | — |
| 1.3.11 | Create OpportunityRanking model | BL | — | — |
| 1.3.12 | Create Recommendation model | BL | — | — |
| 1.3.13 | Create ClusterAnalysis model | BL | — | — |
| 1.3.14 | Create CompetitorAnalysis model | BL | — | — |
| 1.3.15 | Create GigQualityScore model | BL | — | — |
| 1.3.16 | Create SellerScore model | BL | — | — |
| 1.3.17 | Create LLMUsageLog model | BL | — | — |
| 1.3.18 | Create LLMCache model | BL | — | — |
| 1.3.19 | Create RunLog model | BL | — | — |
| 1.3.20 | Create Job model | BL | — | — |
| 1.3.21 | Create Alert model | BL | — | — |
| 1.3.22 | Create PriceAnalysis model | BL | — | — |
| 1.3.23 | Create NichePriceAnalysis model | BL | — | — |
| 1.3.24 | Create DiscoveryOutcome model | BL | — | — |
| 1.3.25 | Create DiscoveryCycleLog model | BL | — | — |
| 1.3.26 | Create GigVisualAnalysis model | BL | — | — |
| 1.3.27 | Create AutoPromotionLog model | BL | — | — |
| 1.3.28 | Create Order model | BL | — | — |
| 1.3.29 | Create database migration script | BL | — | — |
| 1.3.30 | Create model unit tests | BL | — | — |
| 1.4.1 | Create run.py CLI | BL | — | — |
| 1.4.2 | Create init-db command | BL | — | — |
| 1.4.3 | Create export command | BL | — | — |
| 1.4.4 | Create dashboard command | BL | — | — |
| 1.5.1 | Create logging configuration | IP | C | 001 |
| 1.5.2 | Create structured logger | IP | C | 001 |
| 1.5.3 | Create log rotation setup | IP | C | 001 |
| 1.5.4 | Create performance logger | IP | C | 001 |
| 1.5.5 | Create logging tests | IP | C | 001 |
| 1.6.1 | Create hash utilities | IP | D | 001 |
| 1.6.2 | Create date utilities | IP | D | 001 |
| 1.6.3 | Create text utilities | IP | D | 001 |
| 1.6.4 | Create math utilities | BL | — | — |
| 1.6.5 | Create file utilities | BL | — | — |
| 1.6.6 | Create validation utilities | BL | — | — |
| 1.6.7 | Create utility tests | BL | — | — |
| 1.7.1 | Create conftest.py with fixtures | BL | — | — |
| 1.7.2 | Create test database factory | BL | — | — |
| 1.7.3 | Create mock data generators | BL | — | — |
| 1.7.4 | Create test configuration | BL | — | — |
| 1.7.5 | Create CI test runner config | BL | — | — |

---

## Epics 02-10: See ref/todo/EPIC_02 through EPIC_10 for full task details
## The PM will expand each epic's task list as it becomes the active focus

### Epic 02: Collection Engine — 99 tasks (16 stories)
### Epic 03: Analysis Engine — 49 tasks (8 stories)
### Epic 04: Scoring System — 48 tasks (13 stories)
### Epic 05: Recommendations — 41 tasks (9 stories)
### Epic 06: Pricing Engine — 41 tasks (8 stories)
### Epic 07: Discovery Engine — 40 tasks (9 stories)
### Epic 08: Playbook — 38 tasks (7 stories)
### Epic 09: Dashboard & Reporting — 105 tasks (16 stories)
### Epic 10: Integration & Testing — 74 tasks (12 stories)

---

## Total: 601 tasks across 10 epics


---

## Cycle 003 Active Scope Addendum

| Item | Jira | Agent | Cycle 003 Status |
|---|---|---|---|
| PR #1 review/merge and branch truth | SCRUM-246 | A | Assigned |
| Foundation gate command | SCRUM-137 | A | Assigned |
| ORM registry/table count reconciliation | SCRUM-136 | A | Assigned |
| Config hardening | SCRUM-135 | A | Assigned |
| Collection session manager | SCRUM-141 | B | Assigned |
| Collection selector registry | SCRUM-142 | B | Assigned |
| Keyword expansion | SCRUM-147 | B | Assigned |
| Search planning | SCRUM-148 | B | Assigned |
| Queue/checkpoint integration | SCRUM-144/SCRUM-145 | B | Assigned |
| Collection dry-run orchestrator | SCRUM-154 | B | Assigned |
| Analysis contracts | SCRUM-157/SCRUM-158/SCRUM-159 | C | Assigned |
| Keyword features/clustering | SCRUM-157 | C | Assigned |
| Gig quality | SCRUM-158 | C | Assigned |
| Competitor profile/seller strength | SCRUM-159/SCRUM-160 | C | Assigned |
| Analysis dry-run orchestrator | SCRUM-164 | C | Assigned |
| Dashboard/report/export/docs/steward | SCRUM-246 + future Epic 09 | D | Assigned |
