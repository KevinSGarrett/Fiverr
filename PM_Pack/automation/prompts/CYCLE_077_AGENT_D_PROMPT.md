====================================================================
FIVERR 24/7 AUTONOMOUS RUNNER — CYCLE 077 AGENT D
Policy v4.5 / POST_CYCLE_PM_REVIEW_v4
Prerequisite: AGENT_COMPLETE in docs/cycle_reports/CYCLE_077_AGENT_F.md
Runs LAST — cycle steward and close-out agent.
====================================================================

AGENT D ROLE
D is the cycle steward and close-out agent. D executes the full merge gate,
merges the PR to develop, runs the complete Jira Done sync, generates official
post-cycle GitHub and Jira bundles, updates the production readiness scorecard
with final calculated values, writes the Kevin handoff document, and plans
Cycle 078 with 12 story recommendations.

NEVER-BREAK RULES
1. Do NOT merge until merge gate returns PASS or CONDITIONAL_GO
2. Do NOT transition stories to Done unless their evidence is confirmed
3. AGENT_COMPLETE is the final act — written LAST after all work is done

====================================================================

TASK 1 — PREFLIGHT + FULL MERGE GATE EXECUTION (LARGE, ~75 min)
Deliverable: Merge gate result documented; PR #88 (or cycle/077 PR) merged to develop;
develop CI green; DOD-010 DONE.

  1.  `git checkout cycle/077/integration && git pull origin cycle/077/integration`
  2.  Confirm AGENT_COMPLETE in ALL of: _A.md, _B.md, _E.md, _C.md, _F.md.
  3.  Run brain-check: `python automation/ai_cycle_controller.py brain-check` — PASS required.
  4.  Run FULL merge gate (not dry-run):
      `python automation/ai_cycle_controller.py merge-gate --cycle 077 2>&1 | tee docs/cycle_reports/CYCLE_077_MERGE_GATE_RESULT.txt`
  5.  Read the merge gate output carefully. For each FAIL item: determine if it blocks merge.
      - CI FAIL: stops everything — fix CI first
      - Coverage < 90%: stops everything — fix coverage first
      - CODECOV_TOKEN missing (PENDING-001): CONDITIONAL_GO — proceed
      - Cursor model expiry warning (BUG-012): CONDITIONAL_GO — proceed
      - Branch protection 401 (BUG-011): log as known issue — proceed
  6.  Check if PR #88 is already merged: `gh pr view 88 --json state,mergedAt`
  7.  If NOT merged: attempt merge with admin:
      `gh pr merge 88 --squash --admin 2>&1 | tee docs/validation/PR88_MERGE_RESULT.txt`
  8.  If --admin fails: create cycle/077 PR to develop:
      `gh pr create --base develop --head cycle/077/integration --title "feat(cycle-077): V-1/V-2/V-3 PASS, Stages 2-6, TierD-2 cap removed, Score2=53.1%" --body "$(cat docs/cycle_reports/CYCLE_077_MERGE_GATE_RESULT.txt | head -30)"`
      Then: `gh pr merge {NUMBER} --squash --admin`
  9.  Wait for CI on develop: poll `gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion` every 60 seconds until success.
  10. If develop CI fails: diagnose, create hotfix commit on develop, push, re-poll.
  11. Write `docs/cycle_reports/CYCLE_077_PR_MERGE_EVIDENCE.md`: PR number, merge SHA, CI run ID on develop.
  12. Confirm develop is at new HEAD: `git checkout develop && git pull && git log --oneline -3`
  13. Mark DOD-010 DONE. Commit evidence.

====================================================================

TASK 2 — FULL JIRA DONE SYNC: EVERY COMPLETED STORY (LARGE, ~75 min)
Deliverable: ALL completed stories in SCRUM project transitioned to Done;
GJCI-029/034/035 final evidence posted.

  1.  Query ALL non-Done stories:
      `python -c "
      from automation.jira_client import JiraClient
      j = JiraClient()
      issues = j.search_issues('project=SCRUM AND status!=Done ORDER BY updated DESC', maxResults=100)
      for i in issues['issues']:
          print(i['key'], i['fields']['status']['name'][:15], i['fields']['summary'][:60])
      "`
  2.  For EACH story: determine if it is completed by Cycle 077 or prior cycles.
      Completed = has evidence file in docs/validation/ or docs/cycle_reports/.
  3.  Transition all completed stories to Done (transition ID: 41). Execute one at a time:
      `python -c "from automation.jira_client import JiraClient; j=JiraClient(); j.transition_issue('SCRUM-{KEY}', '41')"`
  4.  After each transition: post a concise evidence comment:
      "Cycle 077 close-out. Evidence: {evidence_file_path}. Transitioned by Agent D."
  5.  For stories that are genuinely still in progress or blocked:
      - BUG-011 (gh 401): leave In_Progress, post comment with exact remediation steps
      - BUG-012 (cursor model expiry): leave Open, post "Kevin must re-verify before Cycle 078"
      - PENDING-001 (CODECOV_TOKEN): leave Open, post "Kevin must obtain from codecov.io"
      - OPS-036 (Stage 7 24h observation): leave In_Progress, post "Scaffold ready, waiting for live 24h run"
      - OPS-037 (Stage 8 7-day trial): leave Blocked, post "Requires Stage 7 PASS first"
  6.  Query remaining open stories after transitions:
      `python -c "from automation.jira_client import JiraClient; j=JiraClient(); issues=j.search_issues('project=SCRUM AND status!=Done'); print(len(issues['issues']), 'remaining open')`
  7.  Write `docs/cycle_reports/CYCLE_077_JIRA_FULL_SYNC.md`: N transitioned to Done, remaining open with reasons.
  8.  Commit.

====================================================================

TASK 3 — POST-CYCLE GITHUB AND JIRA BUNDLES (LARGE, ~65 min)
Deliverable: GJCI-034 DONE; GJCI-035 DONE; post-cycle review artifacts written; DOD-012 confirmed.

  1.  Generate post-cycle GitHub bundle:
      `python -c "
      from automation.post_cycle_review import generate_post_cycle_github_bundle
      from automation.github_client import GitHubClient
      import json, pathlib
      c = GitHubClient()
      merge_sha = 'develop'
      bundle = generate_post_cycle_github_bundle(77, merge_sha, c)
      pathlib.Path('docs/cycle_reports/CYCLE_077_GITHUB_BUNDLE.json').write_text(json.dumps(bundle, indent=2))
      print('keys:', list(bundle.keys()))
      "`
  2.  Generate post-cycle Jira bundle:
      `python -c "
      from automation.post_cycle_review import generate_post_cycle_jira_bundle
      from automation.jira_client import JiraClient
      import json, pathlib
      j = JiraClient()
      bundle = generate_post_cycle_jira_bundle(77, j)
      pathlib.Path('docs/cycle_reports/CYCLE_077_JIRA_BUNDLE.json').write_text(json.dumps(bundle, indent=2))
      print('keys:', list(bundle.keys()))
      "`
  3.  Run official post-cycle review in POST_MERGE mode:
      `python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge 2>&1 | tee docs/cycle_reports/CYCLE_077_POST_CYCLE_REVIEW.txt`
  4.  Verify dispatch decision: `python -c "import json; d=json.load(open(r'C:/AI_Runner/state/next_cycle_dispatch_decision.json')); print('blocks_dispatch:', d.get('blocks_dispatch'), 'next_action:', d.get('next_action'))"`
      blocks_dispatch must be False. next_action should point to Cycle 078 startup.
  5.  Post GitHub bundle summary as comment on the main Cycle 077 Jira epic story.
  6.  Post Jira bundle summary as comment on the main Cycle 077 Jira epic story.
  7.  Write `docs/validation/GJCI_034_GITHUB_BUNDLE_FINAL.md` and `docs/validation/GJCI_035_JIRA_BUNDLE_FINAL.md`.
  8.  Mark GJCI-034, GJCI-035 DONE. Commit.

====================================================================

TASK 4 — PRODUCTION READINESS SCORECARD: FINAL CALCULATED VALUES (MEDIUM, ~50 min)
Deliverable: Final Score 1 and Score 2 calculated from actual evidence; scorecard updated.

  1.  Calculate Score 1 (internal build readiness):
      Count all DONE items: `grep -c "DONE" docs/MASTER_CHECKLIST_UPDATED*.md || echo "count manually"`
      From the checklist: total non-deferred items = ~260, DONE items ≈ 228 + Cycle 077 additions ≈ 242.
      Score 1 = 242 / 265 ≈ 91.3%. (Use actual count from checklist.)
  2.  Calculate Score 2 (E2E validation):
      Base = 47.1%. V-1 PASS = +2%, V-2 PASS = +2%, V-3 PASS = +2% = +6%.
      New Score 2 = 53.1%. Cap: REMOVED.
  3.  Update `PM_Pack/06_state/PRODUCTION_READINESS_SCORECARD.md`:
      - Score 1: {calculated}%
      - Score 2: 53.1%
      - TierD-2 cap: REMOVED (Cycle 077, {date})
      - Go-Live stages: 0=COMPLETE, 1=PASS, 2=PASS, 3=PASS, 4=PASS, 5=PASS, 6=PASS, 7=SCAFFOLD_READY, 8=NOT_STARTED
      - Remaining P0 blockers: 0
      - Remaining P1 items: BUG-011 (gh 401), BUG-012 (cursor model), PENDING-001 (CODECOV_TOKEN)
      - Estimated time to Go-Live: ~24 hours observation + Kevin approval
  4.  Update PM_Pack/07_hydration/HYDRATION_HEADER.md:
      - CYCLE_CURRENT: 078
      - CYCLE_PREVIOUS: 077
      - Resolved blockers: all BUGs except 011/012 and PENDING-001
  5.  Update PM_Pack/06_state/STATE_SNAPSHOT.md: Cycle 077 COMPLETE, Cycle 078 READY.
  6.  Run `python automation/ai_cycle_controller.py pm-pack-audit` — PASS required.
  7.  Commit: `git add PM_Pack/ && git commit -m "state(pm-pack): final Score1={N}% Score2=53.1% TierD-2 REMOVED Cycle 077 COMPLETE"`

====================================================================

TASK 5 — CYCLE 078 STORY RECOMMENDATIONS + KEVIN HANDOFF (MEDIUM, ~45 min)
Deliverable: 12 Cycle 078 stories documented; Kevin handoff with exact next steps.

  1.  Write `docs/cycle_reports/CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md`:
      Story 1 (XL): Execute Go-Live Stage 7 — 24-hour unattended observation run
        AC: 1) start_24h_observation.ps1 runs without crash for 24h
            2) No unsafe actions taken (no main push, no force push)
            3) Health stays GREEN or ORANGE (not RED)
            4) observation_summary.json written with all ticks recorded
      Story 2 (XXL): Execute Go-Live Stage 8 — 7-day autonomy trial
        AC: Requires Stage 7 PASS; 3+ complete cycles; ≤5 human interruptions
      Story 3 (XXL): Execute V-4 through V-9 validation gates
        AC: Each V-stage earns +2% Score 2; V-4 requires 3-keyword multi-run
      Story 4 (L): Obtain CODECOV_TOKEN and wire Codecov coverage reports
        AC: Token in GitHub Secrets; CI uploads coverage XML; coverage badge in README
      Story 5 (M): Fix BUG-011 — gh api 401 branch protection (token scope)
        AC: gh api returns 200; BRANCH_PROTECTION_EVIDENCE.md updated
      Story 6 (L): Implement Cursor model auto-verification before expiry
        AC: 48h before expiry: controller emits WARNING and pauses dispatch
      Story 7 (XXL): Implement daily/weekly Slack report delivery
        AC: Daily digest posts to Slack at 8am; weekly summary every Monday
      Story 8 (L): Wire EC2 warm standby (ARCH-007)
        AC: EC2 can run health-check; failover runbook tested
      Story 9 (XXL): Execute 14-day rolling backtesting engine
        AC: Engine runs on 30 historical keywords; accuracy metrics reported
      Story 10 (XXL): Add Upwork signal integration (roadmap item)
        AC: Upwork gig data enriches scoring; 3+ new score dimensions
      Story 11 (L): Complete Go-Live Stage 7 debrief and any post-observation fixes
        AC: All issues from 24h run documented and resolved
      Story 12 (L): Final 24/7 production sign-off documentation
        AC: All Stage 7 evidence compiled; production declaration written

  2.  Write `docs/cycle_reports/CYCLE_077_KEVIN_HANDOFF.md`:
      # Cycle 077 Complete — Kevin Handoff

      ## What Cycle 077 Accomplished
      - CI: 4/4 GREEN (lint, type-check, smoke-gates, tests-coverage)
      - Go-Live Stages 2 through 6: ALL PASS
      - V-1/V-2/V-3 live Fiverr validation: ALL PASS
      - Score 1: {final}% | Score 2: 53.1% | TierD-2 cap: REMOVED
      - Combined test coverage: >=90%
      - All ADRs (001-015): complete
      - All runbooks (15): complete
      - All IN_PROGRESS items: DONE (except temporal stages 7/8)
      - 6 Jira stories: DONE transitions via Agent D

      ## What Still Needs to Happen
      1. **START GO-LIVE STAGE 7 (24-hour observation):**
         - Run: `powershell -File C:/AI_Runner/scripts/start_24h_observation.ps1`
         - Let it run overnight — do not interrupt unless HEALTH=RED
         - Check in the morning: `powershell -File C:/AI_Runner/scripts/check_observation_health.ps1`
         - If it ran cleanly for 24h: Stage 7 PASSES and the system is 24/7 LIVE

      2. **RE-VERIFY CURSOR MODEL (URGENT — expires 2026-06-18):**
         - Open Cursor Desktop → Settings → verify Codex 5.3 is still active
         - Update `C:/AI_Runner/state/cursor_model_state.json` status=VERIFIED
         - Run: `python automation/ai_cycle_controller.py brain-check` to confirm

      3. **OBTAIN CODECOV_TOKEN from codecov.io:**
         - Sign in at codecov.io with GitHub account
         - Find the Fiverr repo → copy the upload token
         - Add to GitHub Secrets: gh secret set CODECOV_TOKEN
         - Resolves PENDING-001; enables coverage badge

      4. **CREATE CYCLE 078 JIRA STORIES:**
         - Open Jira SCRUM project
         - Create the 12 stories from CYCLE_077_RECOMMENDED_CYCLE_078_JIRA_STORIES.md
         - Then run: `python automation/ai_cycle_controller.py plan-cycle --cycle 078 --live`

      ## System Status
      ```
      PR merge:      cycle/075/integration + cycle/077/integration → develop ✓
      CI on develop: GREEN ✓
      Score 1:       {final}%
      Score 2:       53.1% (TierD-2 cap REMOVED)
      Stages 0-6:    ALL PASS
      Stage 7:       SCAFFOLD_READY — run start_24h_observation.ps1 to complete
      Stage 8:       Blocked until Stage 7 PASS
      ```

  3.  Verify the handoff doc is readable and complete:
      - It must have exactly 4 numbered action items for Kevin
      - It must include the start_24h_observation.ps1 command
      - It must include the cursor model re-verify steps
      - It must include the plan-cycle --cycle 078 --live command
  4.  Run `python automation/ai_cycle_controller.py status-tick` one final time and append
      its output to `docs/cycle_reports/CYCLE_077_KEVIN_HANDOFF.md` under a "## Final Status Tick" section.
  5.  Commit both files.

====================================================================

TASK 6 — BRANCH HYGIENE + FINAL CI VERIFICATION (MEDIUM, ~30 min)

  1.  Delete cycle/075/integration remote branch (after confirmed merged):
      `gh pr view 88 --json state | python -c "import json,sys; d=json.load(sys.stdin); print(d['state'])"`
      If merged: `git push origin --delete cycle/075/integration`
  2.  Delete cycle/077/integration remote branch (after merged to develop):
      `git push origin --delete cycle/077/integration` (only after confirmed merged)
  3.  Local cleanup: `git branch -D cycle/075/integration cycle/077/integration 2>/dev/null || true`
      `git fetch --all --prune`
  4.  Verify develop is clean and CI is green:
      `git checkout develop && git pull && git log --oneline -5`
      `gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion`
  5.  Run full validation on develop:
      `python -m ruff check automation/ src/ tests/ -q`
      `python -m mypy automation/ --ignore-missing-imports -q`
      `python automation/ai_cycle_controller.py brain-check`
  6.  If any validation fails on develop: create a hotfix, commit to develop directly (minor fix only), push.
  7.  Commit cleanup record: `git add docs/ && git commit -m "chore(cleanup): Cycle 077 branch hygiene complete"`

====================================================================

TASK 7 — FINAL CYCLE REPORT AND AGENT_COMPLETE (MEDIUM, ~30 min)

  1.  Write `docs/cycle_reports/CYCLE_077_AGENT_D.md`:
      - Merge gate: PASS/CONDITIONAL_GO (specify which items were CONDITIONAL)
      - PR merge: PR number, merge SHA, develop CI result
      - Jira: N stories transitioned to Done, M remaining open with reasons
      - GitHub bundle: written to CYCLE_077_GITHUB_BUNDLE.json
      - Jira bundle: written to CYCLE_077_JIRA_BUNDLE.json
      - Post-cycle review: status, blocks_dispatch=False
      - Score 1 final: {value}%
      - Score 2 final: 53.1% (TierD-2 cap REMOVED)
      - Go-Live stages: 0-6 PASS, 7 SCAFFOLD_READY, 8 NOT_STARTED
      - Cycle 078 stories: 12 recommendations written
      - Kevin handoff: written
      - Branch hygiene: cycle/075 + cycle/077 deleted after merge
      - AGENT_COMPLETE — Cycle 077 is COMPLETE
  2.  `git add docs/cycle_reports/CYCLE_077_AGENT_D.md && git commit -m "report(cycle-077): Agent D AGENT_COMPLETE — Cycle 077 COMPLETE"`
  3.  If on cycle/077/integration branch: `git push origin cycle/077/integration` one final time.
      Then on develop: `git checkout develop && git pull`

VALIDATION (R-092 Tier 2 — Comprehensive)
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python -m pytest tests/unit/ --cov=automation --cov=src --cov-fail-under=90 --timeout=60 -q | tail -10
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py merge-gate --dry-run --cycle 077
python automation/ai_cycle_controller.py post-cycle-review --cycle 077 --mode post-merge | tail -5
gh run list --workflow=ci.yml --branch develop --limit 1 --json status,conclusion

END OF PROMPT

Cycle 077 is complete upon Agent D AGENT_COMPLETE.
Cycle 078 begins after: Cursor model re-verified + 12 stories created + plan-cycle --cycle 078 --live.
The system is ready for Stage 7 (24-hour observation) immediately after PR merge.
