# CYCLE 052 -- AGENT D REPORT (FINAL ALL-PASS CLOSEOUT)

Date: 2026-05-30
Agent: D (Merge Gate / Governance Steward)

## Final Verdict

ALL CYCLE 052 TASKS ARE COMPLETE.

- Merge gate passed after blocker loops were resolved by owning agents.
- PR #61 was squash-merged to `develop`.
- Post-merge verification completed: local/origin/API HEAD aligned.
- Codex unresolved review threads are zero pre-merge and post-merge.
- Jira closure completed with transition id `41` for control, B, E, and SCRUM-598..604.
- Cycle 053 prep notes are finalized with post-merge base SHA.

## Key Final IDs

- Base: `12c3866`
- PR: `#61`
- Merge commit: `c2468f526cbce9aa21d1c9262ebd80526ab1a808`
- MergedAt: `2026-05-30T23:47:18Z`

## Completion Table (Final)

| # | Criterion | Met |
| --- | --- | --- |
| 1 | merge-base == 12c3866; six reports present; PR identified | YES |
| 2 | E zone clean (report-only) | YES |
| 3 | F zone clean (tests+report; no weakening) | YES |
| 4 | C zone clean (report-only) | YES |
| 5 | ALL in-range src commits attributed to Agent B | YES |
| 6 | config diff relevance-only; scrapfly false; reddit intact; no secrets | YES |
| 7 | --cov=src aggregate total + each new module >= 90% | YES |
| 8 | codecov/patch >= 90% on PR | YES |
| 9 | all 18 regressions + new-seller + C051 guards pass | YES |
| 10 | Section 7 == 18 (v1.3; REG-15/16 reserved) | YES |
| 11 | golden-run parity OFF == legacy anchors | YES |
| 12 | kw=110 CONDITIONAL_GO ON; drift <= 2 | YES |
| 13 | migration_07 apply/idempotent/rollback confirmed | YES |
| 14 | gh pr checks all green | YES |
| 15 | merge-gate ALL-PASS documented | YES |
| 16 | squash-merged; branch deleted; HEAD confirmed | YES |
| 17 | Codex unresolved == 0 pre and post merge | YES |
| 18 | Jira transitioned with DoD verification | YES |
| 19 | CYCLE_052_PREP_NOTES.md finalized for Cycle 053 | YES |
| 20 | D file-zone respected (report + prep notes only) | YES |

## Self-Audit

- merge-base and branch preflight verified: YES
- zone checks E/F/C verified: YES
- attribution all-commits-per-file scan verified: YES
- config gate + secret scan verified: YES
- aggregate coverage + patch coverage verified: YES
- regressions and C051 guard tests verified: YES
- parity and kw=110 safety verified: YES
- CI and Codex pre/post verified: YES
- merge and branch deletion verified: YES
- Jira DoD-verified Done transitions completed: YES

---

## Evidence: PR checks snapshot
```text
Dependency Audit	pass	16s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933319/job/78685507884	
Lint, Typecheck, Tests, and Gates	pass	9m2s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697931924/job/78685504237	
Lint, Typecheck, Tests, and Gates	pass	9m17s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933321/job/78685507808	
Secret Scan	pass	3s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933319/job/78685507882	
Validate PR	pass	6s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933326/job/78685507831	
codecov/patch	pass	1s	https://app.codecov.io/gh/KevinSGarrett/Fiverr/pull/61	
codecov/project	pass	4s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697931924/job/78685938745	
codecov/project	pass	6s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933321/job/78685955494	

## Evidence: Codex query snapshot
`json
{"data":{"repository":{"pullRequest":{"reviewThreads":{"totalCount":2,"nodes":[{"isResolved":true,"isOutdated":false,"comments":{"nodes":[{"author":{"login":"chatgpt-codex-connector"},"body":"**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Pass relevance config into orchestrated gig detail runs**\n\nWhen Stage 4 is run through the collection pipeline, the new `config` parameter is never supplied by the handler in `src/collection/orchestrator.py:332-344`, so `_relevance_config(None)` is used and `enable_zombie_filter` always defaults on. In deployments that set `relevance.enable_zombie_filter: false` for legacy parity or validation, orchestrated gig-detail collection still computes and persists zombie flags, making the toggle ineffective for the normal pipeline path.\n\nUseful? React with =���-�/ =���.","path":"src/collection/workflows/gig_detail.py"}]}},{"isResolved":true,"isOutdated":false,"comments":{"nodes":[{"author":{"login":"chatgpt-codex-connector"},"body":"**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Exclude sponsored gigs from profitability inputs**\n\nThis new R3 filtering only removes zombies before calculating profitability, but it does not honor `enable_sponsored_exclusion` the way the competition and feasibility calculators do. With the default config (`enable_sponsored_exclusion: true`), a sponsored top-card that has premium prices/extras remains in `top_gigs` and can still skew `avg_starting_price_top10`, premium, delivery, and extras profitability signals, so paid placements continue to contaminate Score 5.\n\nUseful? React with =���-�/ =���.","path":"src/scoring/profitability.py"}]}}]}}}}}
Dependency Audit	pass	16s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933319/job/78685507884	
Lint, Typecheck, Tests, and Gates	pass	9m2s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697931924/job/78685504237	
Lint, Typecheck, Tests, and Gates	pass	9m17s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933321/job/78685507808	
Secret Scan	pass	3s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933319/job/78685507882	
Validate PR	pass	6s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933326/job/78685507831	
codecov/patch	pass	1s	https://app.codecov.io/gh/KevinSGarrett/Fiverr/pull/61	
codecov/project	pass	4s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697931924/job/78685938745	
codecov/project	pass	6s	https://github.com/KevinSGarrett/Fiverr/actions/runs/26697933321/job/78685955494	

```

## Evidence: PR metadata
```json
{"baseRefName":"develop","headRefName":"cycle/052/integration","mergeCommit":{"oid":"c2468f526cbce9aa21d1c9262ebd80526ab1a808"},"mergedAt":"2026-05-30T23:47:18Z","state":"MERGED","title":"docs(cycle-052): finalize r3 integration gate v2","url":"https://github.com/KevinSGarrett/Fiverr/pull/61"}

```

## Evidence: Codex query snapshot
```json
{"data":{"repository":{"pullRequest":{"reviewThreads":{"totalCount":2,"nodes":[{"isResolved":true,"isOutdated":false,"comments":{"nodes":[{"author":{"login":"chatgpt-codex-connector"},"body":"**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Pass relevance config into orchestrated gig detail runs**\n\nWhen Stage 4 is run through the collection pipeline, the new `config` parameter is never supplied by the handler in `src/collection/orchestrator.py:332-344`, so `_relevance_config(None)` is used and `enable_zombie_filter` always defaults on. In deployments that set `relevance.enable_zombie_filter: false` for legacy parity or validation, orchestrated gig-detail collection still computes and persists zombie flags, making the toggle ineffective for the normal pipeline path.\n\nUseful? React with =���-�/ =���.","path":"src/collection/workflows/gig_detail.py"}]}},{"isResolved":true,"isOutdated":false,"comments":{"nodes":[{"author":{"login":"chatgpt-codex-connector"},"body":"**<sub><sub>![P2 Badge](https://img.shields.io/badge/P2-yellow?style=flat)</sub></sub>  Exclude sponsored gigs from profitability inputs**\n\nThis new R3 filtering only removes zombies before calculating profitability, but it does not honor `enable_sponsored_exclusion` the way the competition and feasibility calculators do. With the default config (`enable_sponsored_exclusion: true`), a sponsored top-card that has premium prices/extras remains in `top_gigs` and can still skew `avg_starting_price_top10`, premium, delivery, and extras profitability signals, so paid placements continue to contaminate Score 5.\n\nUseful? React with =���-�/ =���.","path":"src/scoring/profitability.py"}]}}]}}}}}

```

## Evidence: develop API branch head
```json
{"name":"develop","commit":{"sha":"c2468f526cbce9aa21d1c9262ebd80526ab1a808","node_id":"C_kwDOSbqwNdoAKGMyNDY4ZjUyNmNiY2U5YWEyMWQxYzkyNjJlYmQ4MDUyNmFiMWE4MDg","commit":{"author":{"name":"KevinSGarrett","email":"garretttrainingsystems@gmail.com","date":"2026-05-30T23:47:18Z"},"committer":{"name":"GitHub","email":"noreply@github.com","date":"2026-05-30T23:47:18Z"},"message":"docs(cycle-052): finalize r3 integration gate v2 (#61)\n\n* docs(cycle-052): governance, jira map, and stage-1 handoffs\n\nCapture Agent A stage-1 setup for R3 with preflight evidence, schema/config decisions,\nJira control-story creation, and downstream B/E/C/F/D contracts while keeping scope in docs/governance only.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): governance + hydration + epic tracker + untrack coverage.xml\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E live sponsored/zombie signal validation\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E live validation addendum\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E final validation completion\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): update Agent E recorded SHA\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(schema): add R3 migration_07 and ORM mappings\n\nAdd migration_07 with idempotent apply and SQLite-safe rollback, register it in the R8 runner, and expose the new R3 columns on Gig and SearchResult models for persistence.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(collection): add R3 relevance and zombie detail wiring\n\nIntroduce relevance config loading, implement zombie detector logic, propagate sponsored signals from gig cards, parse review/date fields robustly, and wire Stage 4.5 persistence with safe toggle-off inert behavior.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(scoring): apply sponsored and zombie relevance filters\n\nFilter sponsored and zombie gigs across scoring calculators, add demand TRC sponsored-fraction adjustment with DL-209 no-stack seam, and include zombie concentration context in confidence handling.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(r3): add detector, stage-4.5, and scoring regression coverage\n\nAdd REG-17/18/19 and critical new-seller detector coverage, extend gig detail Stage 4.5 tests, and verify migration plus end-to-end scoring behavior for sponsored/zombie filtering.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): register REG-17/18/19 and finalize Agent B report\n\nUpdate Section 7 to the 18-name Cycle 052 regression pack and add the complete Agent B execution report with parity anchors, verification gates, and acceptance checklist evidence.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent B commit ledger\n\nUpdate the report commit list with the exact documentation commit SHA for the final Cycle 052 Agent B handoff record.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent C integration verification\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent C verification evidence\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): sync Agent C report SHA references\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent C handoff metadata\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(cycle-052): harden R3 branch coverage and permanence checks\n\nAdd targeted edge and guard tests across detector, gig detail, feasibility, profitability, migration, and integration parity paths to bring every R3 file to at least 90% file-scoped coverage without touching src/config.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(cycle-052): R3 coverage hardening + migration/parity tests\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent F strict closeout SHA\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): block merge gate on F lint failure\n\nRecord D-stage independent gate evidence, create PR #61, and halt merge/Jira closure due a failing Ruff import-order check in F-owned test scope; include Cycle-053 prep notes with fix-forward path.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(F): fix Ruff import order in feasibility extended test\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* fix(cycle-052): resolve Agent B codex integration findings\n\nPass the Stage 4 orchestrator config into gig detail workflow execution and apply sponsored exclusion in profitability scoring so relevance toggles are honored consistently across calculators.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n---------\n\nCo-authored-by: Cursor <cursoragent@cursor.com>","tree":{"sha":"6ae0e4b882bb990cb1256c486e5caf831f236e49","url":"https://api.github.com/repos/KevinSGarrett/Fiverr/git/trees/6ae0e4b882bb990cb1256c486e5caf831f236e49"},"url":"https://api.github.com/repos/KevinSGarrett/Fiverr/git/commits/c2468f526cbce9aa21d1c9262ebd80526ab1a808","comment_count":0,"verification":{"verified":true,"reason":"valid","signature":"-----BEGIN PGP SIGNATURE-----\n\nwsFcBAABCAAQBQJqG3cGCRC1aQ7uu5UhlAAAQPsQACuI/VcGaBoa7YNRCfbeLG/0\nlG3bblqeACG9gmzatxjPL3wC7HH7i6cCAXSsDgs8bpCd+QhUXDibO+KIp/XaL2/3\nz0o25RlhQR0KGIVmm4D/jsCsPuoX+y4yXG7WgI7IIjChzfTYBnqapv0r+p2K3vvi\nn5AHyqwZrUej5xe2axCSH9kg439fsJI7IF3s+cGgCSFga4SCCDdXCfnS3sywl+SF\nZTS0fLc+UjeJWdFcSB6cd0UwdN3xS28Nejx1Gl+fQWpG3jI2x8YHzAwJWLk01m0q\nC5vuvvOrgodYcy86YqOhmiJp7e+SNqKj0RVZ7Gz30KYz2RZhKU8TbFQKcuMrW+Tq\nzOsexbGc3x8FD51m5Qie0e2o2y9SEbj+6BH3jqcfiv0wP6Bro2l8aIrKhzzPLJxB\numxBCGX5JKKNROlkoiyjNpt6C+VWGmwRrw2LlYvrw8yXB64LM1StLOO61ugcs8k8\nZUb0J+wPA3nVHb7RjzZ/vG8KsjOXnqG2t2KqjCm/5Gyq8o0BO+wepB0MK3j12xvE\nXDfh0z93q+IRcikeapGdEi73LYLx/SMNChBh64wdje7twzHY460GC+nv/rs4CFBN\n08RhwNGBt6WgLTpdSb52oZ5/sib12sS6EFJryz0tO4V9wn7jsZGsMmy+KnILM+JX\nbwXFpDXbb6LDXE7Y7vLY\n=t6yu\n-----END PGP SIGNATURE-----\n","payload":"tree 6ae0e4b882bb990cb1256c486e5caf831f236e49\nparent 12c3866cfa3bbb698ea54f7465c1d3027aa8eaee\nauthor KevinSGarrett <garretttrainingsystems@gmail.com> 1780184838 -0500\ncommitter GitHub <noreply@github.com> 1780184838 -0500\n\ndocs(cycle-052): finalize r3 integration gate v2 (#61)\n\n* docs(cycle-052): governance, jira map, and stage-1 handoffs\n\nCapture Agent A stage-1 setup for R3 with preflight evidence, schema/config decisions,\nJira control-story creation, and downstream B/E/C/F/D contracts while keeping scope in docs/governance only.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): governance + hydration + epic tracker + untrack coverage.xml\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E live sponsored/zombie signal validation\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E live validation addendum\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent E final validation completion\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): update Agent E recorded SHA\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(schema): add R3 migration_07 and ORM mappings\n\nAdd migration_07 with idempotent apply and SQLite-safe rollback, register it in the R8 runner, and expose the new R3 columns on Gig and SearchResult models for persistence.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(collection): add R3 relevance and zombie detail wiring\n\nIntroduce relevance config loading, implement zombie detector logic, propagate sponsored signals from gig cards, parse review/date fields robustly, and wire Stage 4.5 persistence with safe toggle-off inert behavior.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* feat(scoring): apply sponsored and zombie relevance filters\n\nFilter sponsored and zombie gigs across scoring calculators, add demand TRC sponsored-fraction adjustment with DL-209 no-stack seam, and include zombie concentration context in confidence handling.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(r3): add detector, stage-4.5, and scoring regression coverage\n\nAdd REG-17/18/19 and critical new-seller detector coverage, extend gig detail Stage 4.5 tests, and verify migration plus end-to-end scoring behavior for sponsored/zombie filtering.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): register REG-17/18/19 and finalize Agent B report\n\nUpdate Section 7 to the 18-name Cycle 052 regression pack and add the complete Agent B execution report with parity anchors, verification gates, and acceptance checklist evidence.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent B commit ledger\n\nUpdate the report commit list with the exact documentation commit SHA for the final Cycle 052 Agent B handoff record.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): Agent C integration verification\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent C verification evidence\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): sync Agent C report SHA references\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent C handoff metadata\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(cycle-052): harden R3 branch coverage and permanence checks\n\nAdd targeted edge and guard tests across detector, gig detail, feasibility, profitability, migration, and integration parity paths to bring every R3 file to at least 90% file-scoped coverage without touching src/config.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(cycle-052): R3 coverage hardening + migration/parity tests\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): finalize Agent F strict closeout SHA\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* docs(cycle-052): block merge gate on F lint failure\n\nRecord D-stage independent gate evidence, create PR #61, and halt merge/Jira closure due a failing Ruff import-order check in F-owned test scope; include Cycle-053 prep notes with fix-forward path.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* test(F): fix Ruff import order in feasibility extended test\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n* fix(cycle-052): resolve Agent B codex integration findings\n\nPass the Stage 4 orchestrator config into gig detail workflow execution and apply sponsored exclusion in profitability scoring so relevance toggles are honored consistently across calculators.\n\nCo-authored-by: Cursor <cursoragent@cursor.com>\n\n---------\n\nCo-authored-by: Cursor <cursoragent@cursor.com>","verified_at":"2026-05-30T23:47:19Z"}},"url":"https://api.github.com/repos/KevinSGarrett/Fiverr/commits/c2468f526cbce9aa21d1c9262ebd80526ab1a808","html_url":"https://github.com/KevinSGarrett/Fiverr/commit/c2468f526cbce9aa21d1c9262ebd80526ab1a808","comments_url":"https://api.github.com/repos/KevinSGarrett/Fiverr/commits/c2468f526cbce9aa21d1c9262ebd80526ab1a808/comments","author":{"login":"KevinSGarrett","id":221021834,"node_id":"U_kgDODSyGig","avatar_url":"https://avatars.githubusercontent.com/u/221021834?v=4","gravatar_id":"","url":"https://api.github.com/users/KevinSGarrett","html_url":"https://github.com/KevinSGarrett","followers_url":"https://api.github.com/users/KevinSGarrett/followers","following_url":"https://api.github.com/users/KevinSGarrett/following{/other_user}","gists_url":"https://api.github.com/users/KevinSGarrett/gists{/gist_id}","starred_url":"https://api.github.com/users/KevinSGarrett/starred{/owner}{/repo}","subscriptions_url":"https://api.github.com/users/KevinSGarrett/subscriptions","organizations_url":"https://api.github.com/users/KevinSGarrett/orgs","repos_url":"https://api.github.com/users/KevinSGarrett/repos","events_url":"https://api.github.com/users/KevinSGarrett/events{/privacy}","received_events_url":"https://api.github.com/users/KevinSGarrett/received_events","type":"User","user_view_type":"public","site_admin":false},"committer":{"login":"web-flow","id":19864447,"node_id":"MDQ6VXNlcjE5ODY0NDQ3","avatar_url":"https://avatars.githubusercontent.com/u/19864447?v=4","gravatar_id":"","url":"https://api.github.com/users/web-flow","html_url":"https://github.com/web-flow","followers_url":"https://api.github.com/users/web-flow/followers","following_url":"https://api.github.com/users/web-flow/following{/other_user}","gists_url":"https://api.github.com/users/web-flow/gists{/gist_id}","starred_url":"https://api.github.com/users/web-flow/starred{/owner}{/repo}","subscriptions_url":"https://api.github.com/users/web-flow/subscriptions","organizations_url":"https://api.github.com/users/web-flow/orgs","repos_url":"https://api.github.com/users/web-flow/repos","events_url":"https://api.github.com/users/web-flow/events{/privacy}","received_events_url":"https://api.github.com/users/web-flow/received_events","type":"User","user_view_type":"public","site_admin":false},"parents":[{"sha":"12c3866cfa3bbb698ea54f7465c1d3027aa8eaee","url":"https://api.github.com/repos/KevinSGarrett/Fiverr/commits/12c3866cfa3bbb698ea54f7465c1d3027aa8eaee","html_url":"https://github.com/KevinSGarrett/Fiverr/commit/12c3866cfa3bbb698ea54f7465c1d3027aa8eaee"}]},"_links":{"self":"https://api.github.com/repos/KevinSGarrett/Fiverr/branches/develop","html":"https://github.com/KevinSGarrett/Fiverr/tree/develop"},"protected":false,"protection":{"enabled":false,"required_status_checks":{"enforcement_level":"off","contexts":[],"checks":[]}},"protection_url":"https://api.github.com/repos/KevinSGarrett/Fiverr/branches/develop/protection"}

```

## Evidence: Jira DoD source payload (pre-transition)
```json
{
  "issues": [
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11773",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11773",
      "key": "SCRUM-598",
      "fields": {
        "summary": "[SRDI] S2.24 Sponsored Flag Propagation — gig_cards → Gig.is_sponsored + SearchResult counts",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nPropagate the sponsored flag from `gig_cards` (already present in Stage 3 parse results) onto individual `Gig` records, and compute `sponsored_gig_count` / `organic_gig_count` aggregates on `SearchResult` every collection run. This is the data foundation for all sponsored-exclusion logic in scoring.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §1.1–§1.2 (Sponsored & Zombie Gig Filtering)\n* Related stories: S1.11 (Gig.is_sponsored column), S1.12 (SearchResult.sponsored_gig_count column)\n\n## Business Purpose\n\nSponsored gigs are paid placements — not organic competition. Without this flag, every scoring calculator treats paid results the same as earned rankings, inflating competition scores and misrepresenting the real market.\n\n## Acceptance Criteria\n\n* \\[ \\] `Gig.is_sponsored` field populated during Stage 4 gig upsert using `_get_sponsored_flag_for_gig(gig_url, search_result)` matcher\n* \\[ \\] `_get_sponsored_flag_for_gig` normalizes Fiverr URLs (strip query params, trailing slash) for robust matching via `_urls_match` helper\n* \\[ \\] `SearchResult.sponsored_gig_count` = `sum(c.sponsored_flag for c in gig_cards)` during Stage 3\n* \\[ \\] `SearchResult.organic_gig_count` = complement of sponsored count\n* \\[ \\] NULL `Gig.is_sponsored` treated as organic in all downstream queries (backward-compat)\n\n## Definition of Done\n\n* \\[ \\] `_get_sponsored_flag_for_gig(gig_url, search_result)` implemented, returns True/False/None\n* \\[ \\] `_urls_match(url_a, url_b)` URL normalization helper implemented\n* \\[ \\] `Gig.is_sponsored` populated in gig upsert during `gig_detail.py` Stage 4\n* \\[ \\] `SearchResult.sponsored_gig_count` / `organic_gig_count` populated in `fiverr_search.py` Stage 3 (coordinate with S2.20)\n* \\[ \\] Unit test: sponsored gig card correctly matched to Gig by normalized URL\n\n## Dependencies\n\n* S1.11 (SCRUM-585): `Gig.is_sponsored` column must exist in schema\n* S1.12 (SCRUM-586): `SearchResult.sponsored_gig_count` / `organic_gig_count` must exist\n\n## Testing Requirements\n\n* Unit: sponsored flag propagation from gig card → Gig record via URL matching\n* Unit: `_urls_match` handles query param variants and trailing slashes\n* Integration: `SearchResult.sponsored_gig_count` matches the actual number of sponsored cards in the search result\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, collection, sponsored-filtering, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11774",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11774",
      "key": "SCRUM-599",
      "fields": {
        "summary": "[SRDI] S2.25 Sponsored Exclusion in Competition/Feasibility + Organic TRC Adjustment in Demand",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nExtend the Stage 3 (search) and Stage 4 (scoring) pipelines to exclude sponsored gigs from competition and feasibility calculations, and apply an organic TRC adjustment to the demand calculator when the sponsored fraction exceeds 20%.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §2.1–§2.4 (Sponsored Exclusion in Scoring)\n\n## Business Purpose\n\nA keyword with 40% sponsored results has its TRC inflated by \\~40% and its competition top-10 polluted with paid placements. This story makes every scoring calculator sponsored-aware, so scores reflect real organic competition.\n\n## Acceptance Criteria\n\n* \\[ \\] `competition.py`: top-10 gig query adds `Gig.is_sponsored.isnot(True)` filter; logs `sponsored_gigs_excluded` count; warns when any excluded\n* \\[ \\] `feasibility.py`: level-ratio and review-candidate queries filter `is_sponsored is not True`\n* \\[ \\] `demand.py` `_compute_organic_trc_estimate(trc, sponsored_count, total_cards)`: tiered reduction — ≤10%→no change; ≤20%→×0.90; ≤35%→×0.80; else ×0.70\n* \\[ \\] Organic TRC adjustment wired into demand count component when sponsored fraction >20%\n* \\[ \\] REG-17: sponsored gigs never appear in competition top-10 — added to permanent regression pack\n* \\[ \\] REG-19: organic TRC adjusted when sponsored fraction >20% — added to permanent pack\n\n## Definition of Done\n\n* \\[ \\] `competition.py` and `feasibility.py` modified with sponsored-exclusion filters\n* \\[ \\] `_compute_organic_trc_estimate` implemented with 4-tier band logic\n* \\[ \\] Demand calculator uses organic TRC estimate as input when applicable\n* \\[ \\] All-filtered fallback: if ALL top-10 are sponsored → fall back to full set + warning log\n\n## Dependencies\n\n* S2.24 (SCRUM-598): `Gig.is_sponsored` must be populated before scoring uses it\n* S1.11 (SCRUM-585): Gig schema column\n\n## Testing Requirements\n\n* Unit: competition top-10 excludes sponsored gig — `test_sponsored_gig_filtering.py`\n* Unit: organic TRC bands (≤20%→×0.90, ≤35%→×0.80, else ×0.70) — verified for each band\n* Integration: end-to-end scoring run where 30% sponsored → competition excludes them + TRC adjusted\n* REG-17, REG-19 in permanent pack\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, sponsored-filtering, scoring, demand, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11775",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11775",
      "key": "SCRUM-600",
      "fields": {
        "summary": "[SRDI] S2.26 zombie_gig_detector.py — compute_zombie_score + is_zombie_gig + date parsers",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nBuild `src/analysis/zombie_gig_detector.py` — the module that scores gigs on 4 weighted zombie indicators and returns a `(zombie_score, signals)` tuple. Critical disambiguation: new sellers with low reviews are NOT zombies.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §3.1–§3.6 (Zombie Gig Detector Module)\n\n## Business Purpose\n\nZombie gigs (old accounts with few/no recent reviews and low activity) make competition look artificially weak. A keyword showing 10 competitors where 7 are zombies is actually a very accessible market — but only if we can identify them.\n\n## Acceptance Criteria\n\n* \\[ \\] `zombie_gig_detector.py` created at `src/analysis/zombie_gig_detector.py`\n* \\[ \\] Constants: `ZOMBIE_REVIEW_AGE_DAYS=365`, `_REVIEW_COUNT_THRESHOLD=10`, `_MIN_ACCOUNT_AGE_DAYS=180`, `_RESPONSE_RATE_THRESHOLD=30`\n* \\[ \\] `compute_zombie_score(gig, seller, *, reference_date)` returns `(float, dict)`: 4 signals — low reviews (×0.35), no recent review (×0.35), seller indicators (×0.15), empty queue (×0.15)\n* \\[ \\] `is_zombie_gig(gig, seller, threshold=0.50)` wraps score≥threshold check\n* \\[ \\] `_extract_last_review_date_from_snippets(gig)` parses `review_snippets` dates, returns max\n* \\[ \\] `_try_parse_date` + `_parse_member_since`: multi-format date parsers (\"Member since Jan 2022\"→datetime)\n* \\[ \\] **New-seller disambiguation**: `member_since` within last 180 days AND review_count < threshold → NOT zombie, even if other signals fire\n* \\[ \\] Missing fields (no `orders_in_queue`, no `response_rate`) → zero contribution for that signal, not a crash\n\n## Definition of Done\n\n* \\[ \\] All 4 signals implemented with correct weights summing to 1.0\n* \\[ \\] New-seller disambiguation test: \"Dec 2025 account, 2 reviews\" → zombie_score < 0.50\n* \\[ \\] Old account, no recent reviews, no queue, low response → zombie_score ≥ 0.50\n* \\[ \\] Missing fields tolerated gracefully\n* \\[ \\] Unit tests `test_zombie_gig_detector.py` (10 tests) pass\n\n## Dependencies\n\n* S1.11 (SCRUM-585): `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`, `Gig.last_reviewed_at` columns\n\n## Testing Requirements\n\n* `test_zombie_gig_detector.py` (10 cases): zero-review+old→zombie; recent-active→not; new-seller-Dec2025→not; old-no-advancement→zombie; snippet date extraction; date parser variants\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-detection, analysis, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11776",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11776",
      "key": "SCRUM-601",
      "fields": {
        "summary": "[SRDI] S2.27 Stage 4.5 Zombie Detection Wiring + last_reviewed_at Extraction",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nWire zombie detection into Stage 4 (after gig detail write), extract and store `last_reviewed_at` from review snippets, and implement the `enable_zombie_filter` config toggle.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §4.1–§4.4 (Stage 4.5 Zombie Detection Wiring)\n\n## Acceptance Criteria\n\n* \\[ \\] In `gig_detail.py`, after Gig upsert: call `compute_zombie_score(gig, seller)` → set `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`\n* \\[ \\] `Gig.last_reviewed_at` extracted from `review_snippets` via `_extract_last_review_date_from_snippets`\n* \\[ \\] Debug log: `logger.debug(f\"Zombie detected: {gig_url}, score={score:.2f}, signals={signals}\")`\n* \\[ \\] `enable_zombie_filter: bool = True` config toggle in `NicheConfig`; when False → skip detection, no `is_zombie` set\n\n## Definition of Done\n\n* \\[ \\] `gig_detail.py` modified: zombie detection called after gig write\n* \\[ \\] `last_reviewed_at` field populated from snippets\n* \\[ \\] Config toggle working: `enable_zombie_filter=False` skips all detection\n* \\[ \\] Integration test: zombie gig detected after full Stage 4 run\n\n## Dependencies\n\n* S2.26 (SCRUM-600): `zombie_gig_detector.py` must exist before wiring\n* S1.11 (SCRUM-585): `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`, `Gig.last_reviewed_at` columns\n\n## Testing Requirements\n\n* Integration: a known-zombie gig (old account, 0 recent reviews) is flagged after Stage 4\n* Unit: config toggle `enable_zombie_filter=False` skips detection\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-detection, stage-4, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11777",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11777",
      "key": "SCRUM-602",
      "fields": {
        "summary": "[SRDI] S2.28 Zombie Exclusion in Competition/Feasibility + Confidence Concentration Deduction",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nApply zombie exclusion filters in competition, feasibility, and confidence calculators. Zombie gigs must never set the review barrier used in feasibility, and a high zombie concentration earns a confidence deduction.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §5.1–§5.3 (Zombie Exclusion in Scoring)\n\n## Acceptance Criteria\n\n* \\[ \\] `competition.py`: query adds `Gig.is_zombie.isnot(True)` filter; logs `zombie_gigs_excluded` count; warns when zombies present\n* \\[ \\] `feasibility.py`: `organic_non_zombie_gigs` filter used for level ratio AND review barrier; fallback to full set with WARNING if <1 clean gig\n* \\[ \\] `confidence.py`: zombie concentration deduction — ≥50% zombies in result set → −0.10; ≥25% → −0.05 + warning\n* \\[ \\] REG-18: zombie gigs never appear as the `lowest_ranked_review_count_page1` reference — added to permanent regression pack\n\n## Definition of Done\n\n* \\[ \\] `competition.py`, `feasibility.py`, `confidence.py` all zombie-aware\n* \\[ \\] `organic_non_zombie_gigs` = `is_sponsored is not True AND is_zombie is not True AND relevance_flag is not False` (anticipates R4 clean-gig set)\n* \\[ \\] Fallback documented: <1 clean gig → use full set + WARNING\n\n## Dependencies\n\n* S2.27 (SCRUM-601): `Gig.is_zombie` must be populated\n\n## Testing Requirements\n\n* Unit: competition top-10 excludes zombie gig\n* Unit: feasibility review barrier uses organic non-zombie set\n* Unit: confidence deduction at ≥50% and ≥25% concentration\n* REG-18 in permanent pack\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-exclusion, scoring, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11778",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11778",
      "key": "SCRUM-603",
      "fields": {
        "summary": "[SRDI] S2.29 Pagination Normalization (TOP_N=10 cap) + Review Count \"10k+\" Parse Fix",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nFix the \"10k+\" review count abbreviation parse bug in `search_result_parser.py`, normalize all collection to a `TOP_N_FOR_SCORING=10` cap in `competition.py` and `feasibility.py`, and store `SearchResult.pages_collected`.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §6.1–§6.3 (Pagination Normalization — Issue #19 + Issue #8)\n\n## Acceptance Criteria\n\n* \\[ \\] `search_result_parser.py` review count parser: `\"10k+\"` → 10000; `\"2.5k\"` → 2500; `\"1,234\"` → 1234; plain integer → integer; `None` / empty → `None`\n* \\[ \\] `competition.py` and `feasibility.py` add `.limit(10)` (TOP_N_FOR_SCORING=10 constant) on gig query, regardless of how many pages were collected\n* \\[ \\] `SearchResult.pages_collected` stored during Stage 3 (1 or 2 depending on configured depth)\n\n## Definition of Done\n\n* \\[ \\] Review count parser handles all abbreviation variants without crashing\n* \\[ \\] Competition and feasibility always score exactly top-10 regardless of collection depth\n* \\[ \\] `pages_collected` populated on every SearchResult\n\n## Testing Requirements\n\n* Unit: \"10k+\" → 10000, \"2.5k\" → 2500, \"k+\" abbreviation variants\n* Unit: competition query `.limit(10)` applied — result set never exceeds 10 gigs\n* Unit: `pages_collected=2` stored when collecting 2 pages\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, pagination, review-parse, tier-0  \nPriority: High",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11779",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11779",
      "key": "SCRUM-604",
      "fields": {
        "summary": "[SRDI] S2.30 R3 Test Suite — test_sponsored + test_zombie (18 unit tests) + REG-17/18/19",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nBuild the complete test suite for R3 (Sponsored & Zombie): `test_sponsored_gig_filtering.py` (8 unit tests), `test_zombie_gig_detector.py` (10 unit tests), and add REG-17/REG-18/REG-19 to the permanent regression pack in `AGENT_EXECUTION_STRATEGY.md §7`.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §4.1, §4.2; WAVE_J §3.3\n\n## Acceptance Criteria\n\n* \\[ \\] `tests/unit/test_sponsored_gig_filtering.py` (8 tests): competition top-10 excludes sponsored; feasibility level-ratio excludes sponsored; TRC band ≤20%→×0.90; TRC band ≤35%→×0.80; TRC band >35%→×0.70; flag propagation from gig_card via URL match; `_urls_match` strip-query-params; all-sponsored fallback returns full set with warning\n* \\[ \\] `tests/unit/test_zombie_gig_detector.py` (10 tests): zero-review+old=zombie; recent-active=not-zombie; new-seller-Dec2025=not-zombie; old-no-advancement=zombie; score boundary at 0.50; snippet date extraction; `_parse_member_since` variants; missing fields=zero contribution; confidence concentration deduction tiers\n* \\[ \\] REG-17: `test_sponsored_never_in_competition_top_10` registered in permanent pack\n* \\[ \\] REG-18: `test_zombie_never_sets_feasibility_review_barrier` registered in permanent pack\n* \\[ \\] REG-19: `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20pct` registered in permanent pack\n\n## Definition of Done\n\n* \\[ \\] All 18 tests pass (`pytest tests/unit/test_sponsored_gig_filtering.py tests/unit/test_zombie_gig_detector.py`)\n* \\[ \\] REG-17/18/19 appended to `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md §7` permanent pack\n* \\[ \\] No existing tests broken\n\n## Dependencies\n\n* S2.24 through S2.29 must be complete before these tests can run\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, testing, regression-pack, tier-0  \nPriority: High",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12571",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12571",
      "key": "SCRUM-1002",
      "fields": {
        "summary": "Cycle 052: SRDI Tier-0 R3 Sponsored & Zombie Gig Filtering (6-Agent)",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10003",
          "id": "10003",
          "description": "Tasks track small, distinct pieces of work.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10318?size=medium",
          "name": "Task",
          "subtask": false,
          "avatarId": 10318,
          "entityId": "f7473311-d873-4ea2-8721-335d5a24bd07",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Cycle 052 control task for SRDI Tier-0 R3 implementation.\n\nMission:\n\n* Implement Sponsored & Zombie Gig Filtering (R3) with non-destructive toggles and legacy parity safety.\n\nDefinition of Done:\n\n* migration_07 added and validated (idempotent apply + reversible rollback path): gigs.zombie_score, gigs.zombie_signals, gigs.last_reviewed_at, search_results.pages_collected.\n* Sponsored flag propagation implemented from gig_cards -> gig.is_sponsored with robust URL matching.\n* parse_review_count fixed for 10k+, 2.5k, comma-formatted counts, plain integers, and None.\n* Stage 4.5 zombie wiring implemented with new-seller guard and last_reviewed_at extraction.\n* Sponsored and zombie exclusions active in competition, feasibility, demand, and profitability paths.\n* Confidence deductions wired for zombie concentration thresholds.\n* Pagination normalization enforced: top-10 organic cap and pages_collected persistence.\n* REG-17/18/19 added and passing; critical test_zombie_score_low_reviews_new_account passing.\n* Full suite remains >= 3500 and green.\n* kw=110 remains CONDITIONAL_GO; anchor drift <= 2 pts unless explicitly justified by R3 effect.\n* Relevance toggles shipped with defaults ON; golden-run parity proven with toggles OFF == legacy.\n\nHard gates:\n\n* codecov/patch >= 90.\n* GraphQL reviewThreads unresolved == 0 pre/post-resolve at merge gate.\n* One and only one --cov=src run in cycle (Agent D only).\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12572",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12572",
      "key": "SCRUM-1003",
      "fields": {
        "summary": "E02/E Cycle 052: live sponsored/zombie signal availability validation (9 niches)",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Agent E live validation story for Cycle 052 R3.\n\nDoD:\n\n* Validate sponsored_flag (or equivalent promoted marker) availability in gig_cards across all 9 niches.\n* Estimate sponsored fraction by niche and flag markup drift if signal disappears.\n* Validate zombie signal availability by niche: seller.member_since, last_reviewed_at parseability, response_rate, orders_in_queue.\n* Identify systematically missing signals and report NULL=include implications.\n* Recommend enable_sponsored_exclusion and enable_zombie_filter defaults based on observed signal quality.\n* Flag corrections/implementation risks to Agent B before integration verify.\n* Reconfirm DL-207 (R1 URL param shape lock) if live window permits.\n* Report-only commit: docs/cycle_reports/CYCLE_052_AGENT_E.md; no src/tests/config/data edits.\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12573",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12573",
      "key": "SCRUM-1004",
      "fields": {
        "summary": "E02/B Cycle 052: sponsored flag propagation + zombie_gig_detector + scoring exclusions + migration_07",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Agent B implementation story for Cycle 052 R3.\n\nDoD:\n\n* migration_07 added, registered, idempotent, and reversible (apply+rollback).\n* ORM model deltas include only required R3 additions: gigs.zombie_score, gigs.zombie_signals, gigs.last_reviewed_at, search_results.pages_collected.\n* \\_urls_match implemented (scheme/query/case/trailing-slash normalization).\n* \\_propagate_sponsored_flag implemented and SearchResult sponsored/organic counts populated.\n* parse_review_count fixed for k-suffix and comma/plain formats including 10k+.\n* zombie_gig_detector module added with new-seller guard FIRST and thresholded classification.\n* Stage 4.5 wiring implemented with \\_extract_last_review_date and toggle guard.\n* Scoring exclusions implemented in competition/feasibility/demand/profitability.\n* Confidence deductions implemented for zombie concentration thresholds.\n* Pagination hard-cap top_n=10 applied and pages_collected persisted.\n* relevance config block added exactly per contract (no unrelated config changes).\n* REG-17/REG-18/REG-19 added and passing.\n* test_zombie_score_low_reviews_new_account added and passing.\n* Full suite green, kw=110 remains CONDITIONAL_GO.\n* DL-209 seam present: R3 sponsored-fraction multiplier cannot stack with future R4.1 reliability multiplier.\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "priority": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/priority/3",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/priorities/medium_new.svg",
          "name": "Medium",
          "id": "3"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10000",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "To Do",
          "id": "10000",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    }
  ],
  "isLast": true
}
```

## Evidence: Jira status payload (post-transition verification)
```json
{
  "issues": [
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11773",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11773",
      "key": "SCRUM-598",
      "fields": {
        "summary": "[SRDI] S2.24 Sponsored Flag Propagation — gig_cards → Gig.is_sponsored + SearchResult counts",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nPropagate the sponsored flag from `gig_cards` (already present in Stage 3 parse results) onto individual `Gig` records, and compute `sponsored_gig_count` / `organic_gig_count` aggregates on `SearchResult` every collection run. This is the data foundation for all sponsored-exclusion logic in scoring.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §1.1–§1.2 (Sponsored & Zombie Gig Filtering)\n* Related stories: S1.11 (Gig.is_sponsored column), S1.12 (SearchResult.sponsored_gig_count column)\n\n## Business Purpose\n\nSponsored gigs are paid placements — not organic competition. Without this flag, every scoring calculator treats paid results the same as earned rankings, inflating competition scores and misrepresenting the real market.\n\n## Acceptance Criteria\n\n* \\[ \\] `Gig.is_sponsored` field populated during Stage 4 gig upsert using `_get_sponsored_flag_for_gig(gig_url, search_result)` matcher\n* \\[ \\] `_get_sponsored_flag_for_gig` normalizes Fiverr URLs (strip query params, trailing slash) for robust matching via `_urls_match` helper\n* \\[ \\] `SearchResult.sponsored_gig_count` = `sum(c.sponsored_flag for c in gig_cards)` during Stage 3\n* \\[ \\] `SearchResult.organic_gig_count` = complement of sponsored count\n* \\[ \\] NULL `Gig.is_sponsored` treated as organic in all downstream queries (backward-compat)\n\n## Definition of Done\n\n* \\[ \\] `_get_sponsored_flag_for_gig(gig_url, search_result)` implemented, returns True/False/None\n* \\[ \\] `_urls_match(url_a, url_b)` URL normalization helper implemented\n* \\[ \\] `Gig.is_sponsored` populated in gig upsert during `gig_detail.py` Stage 4\n* \\[ \\] `SearchResult.sponsored_gig_count` / `organic_gig_count` populated in `fiverr_search.py` Stage 3 (coordinate with S2.20)\n* \\[ \\] Unit test: sponsored gig card correctly matched to Gig by normalized URL\n\n## Dependencies\n\n* S1.11 (SCRUM-585): `Gig.is_sponsored` column must exist in schema\n* S1.12 (SCRUM-586): `SearchResult.sponsored_gig_count` / `organic_gig_count` must exist\n\n## Testing Requirements\n\n* Unit: sponsored flag propagation from gig card → Gig record via URL matching\n* Unit: `_urls_match` handles query param variants and trailing slashes\n* Integration: `SearchResult.sponsored_gig_count` matches the actual number of sponsored cards in the search result\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, collection, sponsored-filtering, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11774",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11774",
      "key": "SCRUM-599",
      "fields": {
        "summary": "[SRDI] S2.25 Sponsored Exclusion in Competition/Feasibility + Organic TRC Adjustment in Demand",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nExtend the Stage 3 (search) and Stage 4 (scoring) pipelines to exclude sponsored gigs from competition and feasibility calculations, and apply an organic TRC adjustment to the demand calculator when the sponsored fraction exceeds 20%.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §2.1–§2.4 (Sponsored Exclusion in Scoring)\n\n## Business Purpose\n\nA keyword with 40% sponsored results has its TRC inflated by \\~40% and its competition top-10 polluted with paid placements. This story makes every scoring calculator sponsored-aware, so scores reflect real organic competition.\n\n## Acceptance Criteria\n\n* \\[ \\] `competition.py`: top-10 gig query adds `Gig.is_sponsored.isnot(True)` filter; logs `sponsored_gigs_excluded` count; warns when any excluded\n* \\[ \\] `feasibility.py`: level-ratio and review-candidate queries filter `is_sponsored is not True`\n* \\[ \\] `demand.py` `_compute_organic_trc_estimate(trc, sponsored_count, total_cards)`: tiered reduction — ≤10%→no change; ≤20%→×0.90; ≤35%→×0.80; else ×0.70\n* \\[ \\] Organic TRC adjustment wired into demand count component when sponsored fraction >20%\n* \\[ \\] REG-17: sponsored gigs never appear in competition top-10 — added to permanent regression pack\n* \\[ \\] REG-19: organic TRC adjusted when sponsored fraction >20% — added to permanent pack\n\n## Definition of Done\n\n* \\[ \\] `competition.py` and `feasibility.py` modified with sponsored-exclusion filters\n* \\[ \\] `_compute_organic_trc_estimate` implemented with 4-tier band logic\n* \\[ \\] Demand calculator uses organic TRC estimate as input when applicable\n* \\[ \\] All-filtered fallback: if ALL top-10 are sponsored → fall back to full set + warning log\n\n## Dependencies\n\n* S2.24 (SCRUM-598): `Gig.is_sponsored` must be populated before scoring uses it\n* S1.11 (SCRUM-585): Gig schema column\n\n## Testing Requirements\n\n* Unit: competition top-10 excludes sponsored gig — `test_sponsored_gig_filtering.py`\n* Unit: organic TRC bands (≤20%→×0.90, ≤35%→×0.80, else ×0.70) — verified for each band\n* Integration: end-to-end scoring run where 30% sponsored → competition excludes them + TRC adjusted\n* REG-17, REG-19 in permanent pack\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, sponsored-filtering, scoring, demand, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11775",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11775",
      "key": "SCRUM-600",
      "fields": {
        "summary": "[SRDI] S2.26 zombie_gig_detector.py — compute_zombie_score + is_zombie_gig + date parsers",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nBuild `src/analysis/zombie_gig_detector.py` — the module that scores gigs on 4 weighted zombie indicators and returns a `(zombie_score, signals)` tuple. Critical disambiguation: new sellers with low reviews are NOT zombies.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §3.1–§3.6 (Zombie Gig Detector Module)\n\n## Business Purpose\n\nZombie gigs (old accounts with few/no recent reviews and low activity) make competition look artificially weak. A keyword showing 10 competitors where 7 are zombies is actually a very accessible market — but only if we can identify them.\n\n## Acceptance Criteria\n\n* \\[ \\] `zombie_gig_detector.py` created at `src/analysis/zombie_gig_detector.py`\n* \\[ \\] Constants: `ZOMBIE_REVIEW_AGE_DAYS=365`, `_REVIEW_COUNT_THRESHOLD=10`, `_MIN_ACCOUNT_AGE_DAYS=180`, `_RESPONSE_RATE_THRESHOLD=30`\n* \\[ \\] `compute_zombie_score(gig, seller, *, reference_date)` returns `(float, dict)`: 4 signals — low reviews (×0.35), no recent review (×0.35), seller indicators (×0.15), empty queue (×0.15)\n* \\[ \\] `is_zombie_gig(gig, seller, threshold=0.50)` wraps score≥threshold check\n* \\[ \\] `_extract_last_review_date_from_snippets(gig)` parses `review_snippets` dates, returns max\n* \\[ \\] `_try_parse_date` + `_parse_member_since`: multi-format date parsers (\"Member since Jan 2022\"→datetime)\n* \\[ \\] **New-seller disambiguation**: `member_since` within last 180 days AND review_count < threshold → NOT zombie, even if other signals fire\n* \\[ \\] Missing fields (no `orders_in_queue`, no `response_rate`) → zero contribution for that signal, not a crash\n\n## Definition of Done\n\n* \\[ \\] All 4 signals implemented with correct weights summing to 1.0\n* \\[ \\] New-seller disambiguation test: \"Dec 2025 account, 2 reviews\" → zombie_score < 0.50\n* \\[ \\] Old account, no recent reviews, no queue, low response → zombie_score ≥ 0.50\n* \\[ \\] Missing fields tolerated gracefully\n* \\[ \\] Unit tests `test_zombie_gig_detector.py` (10 tests) pass\n\n## Dependencies\n\n* S1.11 (SCRUM-585): `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`, `Gig.last_reviewed_at` columns\n\n## Testing Requirements\n\n* `test_zombie_gig_detector.py` (10 cases): zero-review+old→zombie; recent-active→not; new-seller-Dec2025→not; old-no-advancement→zombie; snippet date extraction; date parser variants\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-detection, analysis, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11776",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11776",
      "key": "SCRUM-601",
      "fields": {
        "summary": "[SRDI] S2.27 Stage 4.5 Zombie Detection Wiring + last_reviewed_at Extraction",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nWire zombie detection into Stage 4 (after gig detail write), extract and store `last_reviewed_at` from review snippets, and implement the `enable_zombie_filter` config toggle.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §4.1–§4.4 (Stage 4.5 Zombie Detection Wiring)\n\n## Acceptance Criteria\n\n* \\[ \\] In `gig_detail.py`, after Gig upsert: call `compute_zombie_score(gig, seller)` → set `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`\n* \\[ \\] `Gig.last_reviewed_at` extracted from `review_snippets` via `_extract_last_review_date_from_snippets`\n* \\[ \\] Debug log: `logger.debug(f\"Zombie detected: {gig_url}, score={score:.2f}, signals={signals}\")`\n* \\[ \\] `enable_zombie_filter: bool = True` config toggle in `NicheConfig`; when False → skip detection, no `is_zombie` set\n\n## Definition of Done\n\n* \\[ \\] `gig_detail.py` modified: zombie detection called after gig write\n* \\[ \\] `last_reviewed_at` field populated from snippets\n* \\[ \\] Config toggle working: `enable_zombie_filter=False` skips all detection\n* \\[ \\] Integration test: zombie gig detected after full Stage 4 run\n\n## Dependencies\n\n* S2.26 (SCRUM-600): `zombie_gig_detector.py` must exist before wiring\n* S1.11 (SCRUM-585): `Gig.is_zombie`, `Gig.zombie_score`, `Gig.zombie_signals`, `Gig.last_reviewed_at` columns\n\n## Testing Requirements\n\n* Integration: a known-zombie gig (old account, 0 recent reviews) is flagged after Stage 4\n* Unit: config toggle `enable_zombie_filter=False` skips detection\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-detection, stage-4, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11777",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11777",
      "key": "SCRUM-602",
      "fields": {
        "summary": "[SRDI] S2.28 Zombie Exclusion in Competition/Feasibility + Confidence Concentration Deduction",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nApply zombie exclusion filters in competition, feasibility, and confidence calculators. Zombie gigs must never set the review barrier used in feasibility, and a high zombie concentration earns a confidence deduction.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §5.1–§5.3 (Zombie Exclusion in Scoring)\n\n## Acceptance Criteria\n\n* \\[ \\] `competition.py`: query adds `Gig.is_zombie.isnot(True)` filter; logs `zombie_gigs_excluded` count; warns when zombies present\n* \\[ \\] `feasibility.py`: `organic_non_zombie_gigs` filter used for level ratio AND review barrier; fallback to full set with WARNING if <1 clean gig\n* \\[ \\] `confidence.py`: zombie concentration deduction — ≥50% zombies in result set → −0.10; ≥25% → −0.05 + warning\n* \\[ \\] REG-18: zombie gigs never appear as the `lowest_ranked_review_count_page1` reference — added to permanent regression pack\n\n## Definition of Done\n\n* \\[ \\] `competition.py`, `feasibility.py`, `confidence.py` all zombie-aware\n* \\[ \\] `organic_non_zombie_gigs` = `is_sponsored is not True AND is_zombie is not True AND relevance_flag is not False` (anticipates R4 clean-gig set)\n* \\[ \\] Fallback documented: <1 clean gig → use full set + WARNING\n\n## Dependencies\n\n* S2.27 (SCRUM-601): `Gig.is_zombie` must be populated\n\n## Testing Requirements\n\n* Unit: competition top-10 excludes zombie gig\n* Unit: feasibility review barrier uses organic non-zombie set\n* Unit: confidence deduction at ≥50% and ≥25% concentration\n* REG-18 in permanent pack\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, zombie-exclusion, scoring, tier-0  \nPriority: Highest",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11778",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11778",
      "key": "SCRUM-603",
      "fields": {
        "summary": "[SRDI] S2.29 Pagination Normalization (TOP_N=10 cap) + Review Count \"10k+\" Parse Fix",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nFix the \"10k+\" review count abbreviation parse bug in `search_result_parser.py`, normalize all collection to a `TOP_N_FOR_SCORING=10` cap in `competition.py` and `feasibility.py`, and store `SearchResult.pages_collected`.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §6.1–§6.3 (Pagination Normalization — Issue #19 + Issue #8)\n\n## Acceptance Criteria\n\n* \\[ \\] `search_result_parser.py` review count parser: `\"10k+\"` → 10000; `\"2.5k\"` → 2500; `\"1,234\"` → 1234; plain integer → integer; `None` / empty → `None`\n* \\[ \\] `competition.py` and `feasibility.py` add `.limit(10)` (TOP_N_FOR_SCORING=10 constant) on gig query, regardless of how many pages were collected\n* \\[ \\] `SearchResult.pages_collected` stored during Stage 3 (1 or 2 depending on configured depth)\n\n## Definition of Done\n\n* \\[ \\] Review count parser handles all abbreviation variants without crashing\n* \\[ \\] Competition and feasibility always score exactly top-10 regardless of collection depth\n* \\[ \\] `pages_collected` populated on every SearchResult\n\n## Testing Requirements\n\n* Unit: \"10k+\" → 10000, \"2.5k\" → 2500, \"k+\" abbreviation variants\n* Unit: competition query `.limit(10)` applied — result set never exceeds 10 gigs\n* Unit: `pages_collected=2` stored when collecting 2 pages\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, pagination, review-parse, tier-0  \nPriority: High",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "11779",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/11779",
      "key": "SCRUM-604",
      "fields": {
        "summary": "[SRDI] S2.30 R3 Test Suite — test_sponsored + test_zombie (18 unit tests) + REG-17/18/19",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "## Story\n\nBuild the complete test suite for R3 (Sponsored & Zombie): `test_sponsored_gig_filtering.py` (8 unit tests), `test_zombie_gig_detector.py` (10 unit tests), and add REG-17/REG-18/REG-19 to the permanent regression pack in `AGENT_EXECUTION_STRATEGY.md §7`.\n\n## Parent Epic\n\nSCRUM-17 — Epic 02: Collection Engine\n\n## Source\n\n* Bulletproof Initiative: WAVE_D §4.1, §4.2; WAVE_J §3.3\n\n## Acceptance Criteria\n\n* \\[ \\] `tests/unit/test_sponsored_gig_filtering.py` (8 tests): competition top-10 excludes sponsored; feasibility level-ratio excludes sponsored; TRC band ≤20%→×0.90; TRC band ≤35%→×0.80; TRC band >35%→×0.70; flag propagation from gig_card via URL match; `_urls_match` strip-query-params; all-sponsored fallback returns full set with warning\n* \\[ \\] `tests/unit/test_zombie_gig_detector.py` (10 tests): zero-review+old=zombie; recent-active=not-zombie; new-seller-Dec2025=not-zombie; old-no-advancement=zombie; score boundary at 0.50; snippet date extraction; `_parse_member_since` variants; missing fields=zero contribution; confidence concentration deduction tiers\n* \\[ \\] REG-17: `test_sponsored_never_in_competition_top_10` registered in permanent pack\n* \\[ \\] REG-18: `test_zombie_never_sets_feasibility_review_barrier` registered in permanent pack\n* \\[ \\] REG-19: `test_organic_trc_adjusted_when_sponsored_fraction_exceeds_20pct` registered in permanent pack\n\n## Definition of Done\n\n* \\[ \\] All 18 tests pass (`pytest tests/unit/test_sponsored_gig_filtering.py tests/unit/test_zombie_gig_detector.py`)\n* \\[ \\] REG-17/18/19 appended to `PM_Pack/ref/AGENT_EXECUTION_STRATEGY.md §7` permanent pack\n* \\[ \\] No existing tests broken\n\n## Dependencies\n\n* S2.24 through S2.29 must be complete before these tests can run\n\n## Suggested Metadata\n\nLabels: \\[SRDI\\], story, wave-D, testing, regression-pack, tier-0  \nPriority: High",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12571",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12571",
      "key": "SCRUM-1002",
      "fields": {
        "summary": "Cycle 052: SRDI Tier-0 R3 Sponsored & Zombie Gig Filtering (6-Agent)",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10003",
          "id": "10003",
          "description": "Tasks track small, distinct pieces of work.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10318?size=medium",
          "name": "Task",
          "subtask": false,
          "avatarId": 10318,
          "entityId": "f7473311-d873-4ea2-8721-335d5a24bd07",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Cycle 052 control task for SRDI Tier-0 R3 implementation.\n\nMission:\n\n* Implement Sponsored & Zombie Gig Filtering (R3) with non-destructive toggles and legacy parity safety.\n\nDefinition of Done:\n\n* migration_07 added and validated (idempotent apply + reversible rollback path): gigs.zombie_score, gigs.zombie_signals, gigs.last_reviewed_at, search_results.pages_collected.\n* Sponsored flag propagation implemented from gig_cards -> gig.is_sponsored with robust URL matching.\n* parse_review_count fixed for 10k+, 2.5k, comma-formatted counts, plain integers, and None.\n* Stage 4.5 zombie wiring implemented with new-seller guard and last_reviewed_at extraction.\n* Sponsored and zombie exclusions active in competition, feasibility, demand, and profitability paths.\n* Confidence deductions wired for zombie concentration thresholds.\n* Pagination normalization enforced: top-10 organic cap and pages_collected persistence.\n* REG-17/18/19 added and passing; critical test_zombie_score_low_reviews_new_account passing.\n* Full suite remains >= 3500 and green.\n* kw=110 remains CONDITIONAL_GO; anchor drift <= 2 pts unless explicitly justified by R3 effect.\n* Relevance toggles shipped with defaults ON; golden-run parity proven with toggles OFF == legacy.\n\nHard gates:\n\n* codecov/patch >= 90.\n* GraphQL reviewThreads unresolved == 0 pre/post-resolve at merge gate.\n* One and only one --cov=src run in cycle (Agent D only).\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12572",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12572",
      "key": "SCRUM-1003",
      "fields": {
        "summary": "E02/E Cycle 052: live sponsored/zombie signal availability validation (9 niches)",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Agent E live validation story for Cycle 052 R3.\n\nDoD:\n\n* Validate sponsored_flag (or equivalent promoted marker) availability in gig_cards across all 9 niches.\n* Estimate sponsored fraction by niche and flag markup drift if signal disappears.\n* Validate zombie signal availability by niche: seller.member_since, last_reviewed_at parseability, response_rate, orders_in_queue.\n* Identify systematically missing signals and report NULL=include implications.\n* Recommend enable_sponsored_exclusion and enable_zombie_filter defaults based on observed signal quality.\n* Flag corrections/implementation risks to Agent B before integration verify.\n* Reconfirm DL-207 (R1 URL param shape lock) if live window permits.\n* Report-only commit: docs/cycle_reports/CYCLE_052_AGENT_E.md; no src/tests/config/data edits.\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    },
    {
      "expand": "renderedFields,names,schema,operations,editmeta,changelog,versionedRepresentations",
      "id": "12573",
      "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issue/12573",
      "key": "SCRUM-1004",
      "fields": {
        "summary": "E02/B Cycle 052: sponsored flag propagation + zombie_gig_detector + scoring exclusions + migration_07",
        "issuetype": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/issuetype/10004",
          "id": "10004",
          "description": "Stories track functionality or features expressed as user goals.",
          "iconUrl": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/2/universal_avatar/view/type/issuetype/avatar/10315?size=medium",
          "name": "Story",
          "subtask": false,
          "avatarId": 10315,
          "entityId": "3faed6a6-639a-42f3-9316-cbefd6f21cad",
          "hierarchyLevel": 0
        },
        "project": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/project/10000",
          "id": "10000",
          "key": "SCRUM",
          "name": "Fiverr Research System",
          "projectTypeKey": "software",
          "simplified": true,
          "avatarUrls": {
            "48x48": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403",
            "24x24": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=small",
            "16x16": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=xsmall",
            "32x32": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/universal_avatar/view/type/project/avatar/10403?size=medium"
          }
        },
        "description": "Agent B implementation story for Cycle 052 R3.\n\nDoD:\n\n* migration_07 added, registered, idempotent, and reversible (apply+rollback).\n* ORM model deltas include only required R3 additions: gigs.zombie_score, gigs.zombie_signals, gigs.last_reviewed_at, search_results.pages_collected.\n* \\_urls_match implemented (scheme/query/case/trailing-slash normalization).\n* \\_propagate_sponsored_flag implemented and SearchResult sponsored/organic counts populated.\n* parse_review_count fixed for k-suffix and comma/plain formats including 10k+.\n* zombie_gig_detector module added with new-seller guard FIRST and thresholded classification.\n* Stage 4.5 wiring implemented with \\_extract_last_review_date and toggle guard.\n* Scoring exclusions implemented in competition/feasibility/demand/profitability.\n* Confidence deductions implemented for zombie concentration thresholds.\n* Pagination hard-cap top_n=10 applied and pages_collected persisted.\n* relevance config block added exactly per contract (no unrelated config changes).\n* REG-17/REG-18/REG-19 added and passing.\n* test_zombie_score_low_reviews_new_account added and passing.\n* Full suite green, kw=110 remains CONDITIONAL_GO.\n* DL-209 seam present: R3 sponsored-fraction multiplier cannot stack with future R4.1 reliability multiplier.\n\n",
        "assignee": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/user?accountId=63d5db4d28cddcc7076faad6",
          "accountId": "63d5db4d28cddcc7076faad6",
          "emailAddress": "kevinsgarrett@gmail.com",
          "avatarUrls": {
            "48x48": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "24x24": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "16x16": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png",
            "32x32": "https://secure.gravatar.com/avatar/2425bc96f2219f0d0af29521b577c06e?d=https%3A%2F%2Favatar-management--avatars.us-west-2.prod.public.atl-paas.net%2Finitials%2FGI-2.png"
          },
          "displayName": "GARRETT TRAINING SYSTEMS INC.",
          "active": true,
          "timeZone": "America/Chicago",
          "accountType": "atlassian"
        },
        "status": {
          "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/status/10003",
          "description": "",
          "iconUrl": "https://kevinsgarrett.atlassian.net/images/icons/statuses/generic.png",
          "name": "Done",
          "id": "10003",
          "statusCategory": {
            "self": "https://api.atlassian.com/ex/jira/eae77257-a572-4e19-b746-8b184ba2d01f/rest/api/3/statuscategory/3",
            "id": 3,
            "key": "done",
            "colorName": "green",
            "name": "Done"
          }
        }
      }
    }
  ],
  "isLast": true
}
```
