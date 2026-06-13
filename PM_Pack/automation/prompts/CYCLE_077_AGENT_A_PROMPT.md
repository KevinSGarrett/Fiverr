====================================================================
FIVERR 24/7 AUTONOMOUS RUNNER — CYCLE 077 AGENT A
Policy v4.5 / POST_CYCLE_PM_REVIEW_v4
PR #88: https://github.com/KevinSGarrett/Fiverr/pull/88
HEAD: 7da9f1b on cycle/075/integration — CI 4/4 GREEN
====================================================================

AGENT A ROLE
A is the setup, state, and infrastructure agent. A builds the Cycle 077
branch, completes all Stage 1 requirements, configures the Slack webhook,
confirms all OPS scheduled tasks are live in production, writes ADR-014/015,
and completes all IN_PROGRESS OPS/MODEL items that do not require live
multi-cycle operation. A does NOT write src/ code. A authorizes B+E only
after the mandatory 55-task floor is verified across all 6 agents.

NEVER-BREAK RULES
1. data/cycle037_live.db mtime must stay == 1780553759 — NEVER modify
2. No src/ code changes — A's scope is automation/, PM_Pack/, docs/, config
3. SMALL tasks (< 15 min) do NOT count toward the 55-task floor
4. END OF PROMPT marker is required; AGENT_COMPLETE in cycle report is required

STARTING STATE
Score 1 = 67.3% | Score 2 = 47.1% | TierD-2 cap ACTIVE
Tests: 5,935 | Coverage: 92.58% | CI: 4/4 GREEN on HEAD 7da9f1b
PR #88 requires admin merge (branch protection policy)
Jira cloud: eae77257-a572-4e19-b746-8b184ba2d01f | Done transition: 41

====================================================================

TASK 1 — PR GATE, BRANCH SETUP, STAGE 1 VERIFICATION (LARGE, ~60 min)
Deliverable: cycle/077/integration created from develop; Stage 1 (OPS-030)
DONE; DOD-007 prompt generation validated; all preflight PASS.

  1.  Verify PR #88 is merged: `gh pr view 88 --json state,mergedAt`.
      If NOT merged (requires admin): document in CYCLE_077_AGENT_A.md
      that branch is from develop HEAD, not from merged PR, and note
      PR #88 admin merge is still pending. Proceed regardless.
  2.  `git checkout develop && git pull origin develop`
      `git log --oneline -5` — confirm Cycle 076 commits are present
  3.  `git checkout -b cycle/077/integration`
      `git push -u origin cycle/077/integration`
  4.  Run `python automation/ai_cycle_controller.py brain-check`
      Must output BRAIN CHECK PASS. If FAIL: diagnose and fix before continuing.
  5.  Run `python automation/ai_cycle_controller.py pm-pack-audit`
      Must output PASS. If FAIL: diagnose and fix before continuing.
  6.  Run Stage 1 live: `python automation/ai_cycle_controller.py plan-cycle --cycle 077 --live`
      This requires >=14 non-Done Jira stories. If fewer exist, query the board:
      `python -c "from automation.jira_client import JiraClient; j=JiraClient(); r=j.search_issues('project=SCRUM AND status!=Done'); print(len(r["issues"]), 'non-Done stories')"`
      If <14 stories: create the missing stories from CYCLE_076_RECOMMENDED_CYCLE_077_JIRA_STORIES.md
      using `python -c "from automation.jira_client import JiraClient; j=JiraClient(); j.create_issue(...)"`.
  7.  Run `python automation/ai_cycle_controller.py validate-prompts --cycle 077`
      Must report PASS for all 6 agents. If any agent fails the 55-task floor
      or missing END OF PROMPT: update the prompt file and re-validate.
  8.  Record OPS-030 DONE: write `docs/validation/OPS_030_STAGE1_EVIDENCE.md`
      containing: plan-cycle output, validate-prompts output, timestamp, PASS.
  9.  Record DOD-007 DONE: write `docs/validation/DOD_007_PROMPT_VALIDATION_EVIDENCE.md`
      containing: validate-prompts full output, 6-agent task counts, PASS.
  10. MANDATORY TASK FLOOR VERIFICATION — before authorizing B+E, count tasks:
      `python -c "
      import re, pathlib
      base = pathlib.Path('C:/Fiverr/Fiverr/PM_Pack/automation/prompts/')
      for ag in ['A','B','E','C','F','D']:
          p = base / f'CYCLE_077_AGENT_{ag}_PROMPT.md'
          text = p.read_text(encoding='utf-8')
          n = len(re.findall(r'^\s{2,}\d+\.', text, re.MULTILINE))
          status = 'PASS' if n >= 55 else f'FAIL ({n} < 55)'
          print(f'Agent {ag}: {n} tasks -> {status}')
      "`
      ALL agents must show >= 55. If any fails: expand that prompt before proceeding.
  11. Commit: `git add docs/validation/ PM_Pack/ && git commit -m "feat(stage1): OPS-030 Stage 1 PASS, DOD-007 validated"`

====================================================================

TASK 2 — PM_PACK FULL STATE UPDATE FOR CYCLE 077 (LARGE, ~60 min)
Deliverable: All 9 PM_Pack state docs updated; HYDRATION_HEADER authoritative;
STATE-001 through STATE-016 all current for Cycle 077.

  1.  `PM_Pack/07_hydration/HYDRATION_HEADER.md` — set CYCLE_CURRENT: 077,
      CYCLE_PREVIOUS: 076, CYCLE_NEXT: 078. Clear resolved blockers
      (BUG-001 through BUG-010, BUG-013 through BUG-021). Keep BUG-011/012/PENDING-001.
  2.  `PM_Pack/06_state/STATE_SNAPSHOT.md` — cycle=077, branch=cycle/077/integration,
      status=IN_PROGRESS, score1=67.3%, score2=47.1%, TierD-2=ACTIVE.
  3.  `PM_Pack/06_state/CURRENT_STATE_CANONICAL.md` — full update with Cycle 077 context.
  4.  `PM_Pack/06_state/PRODUCTION_READINESS_SCORECARD.md` — cycle=077, scores unchanged
      until V-1 completes; Go-Live stages: 1=PASS, 2-8=PENDING.
  5.  `PM_Pack/06_state/TIERD2_TRACKER.json` — cycle_current=077, v1_status=PENDING.
  6.  `PM_Pack/06_state/BLOCKERS.md` — resolved vs open accurately reflected.
  7.  `PM_Pack/06_state/CYCLE_CONTROL.md` — Cycle 077 started with all 6 agents ready.
  8.  `PM_Pack/06_state/AGENT_ROSTER_STATUS.md` — all 6 agents READY for Cycle 077.
  9.  `PM_Pack/06_state/EPIC_STATUS_TRACKER.md` — Runner Epic matrix updated with
      Cycle 076 completions; Wave status current.
  10. `PM_Pack/10_cycle_log/CYCLE_077_LOG.md` — cycle log with 9 required sections.
  11. `PM_Pack/10_cycle_log/CYCLE_076_LOG.md` — verify it exists and is complete.
  12. Run `python automation/ai_cycle_controller.py compile-policy` — must succeed.
  13. Run `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS.
  14. Commit: `git add PM_Pack/ && git commit -m "state(pm-pack): full Cycle 077 state update, all 9 docs current"`

====================================================================

TASK 3 — SLACK WEBHOOK CONFIG + OPS NOTIFICATION DESTINATIONS (LARGE, ~55 min)
Deliverable: OPS-010 DONE; Slack webhook configured and test message delivered;
OPS-022 (daily report) and OPS-023 (weekly report) production runs executed.

  1.  Read `C:/AI_Runner/config/claude_adapter.yaml` — check for slack_webhook_url field.
  2.  Read `automation/notification_router.py` — identify where webhook URL is loaded.
  3.  Check if Slack webhook URL is already in `C:/AI_Runner/secrets/runner.env`:
      `python -c "import os; from dotenv import load_dotenv; load_dotenv(r'C:/AI_Runner/secrets/runner.env'); print('SLACK_WEBHOOK_URL:', bool(os.environ.get('SLACK_WEBHOOK_URL')))"`
  4.  If webhook URL exists: send a test notification:
      `python -c "from automation.notification_router import send_notification; send_notification('TEST', 'Cycle 077 Agent A: notification router online', severity='INFO')"`
      Capture the HTTP response. If 200: OPS-010 notification delivery CONFIRMED.
  5.  If webhook URL NOT in runner.env: write placeholder config with instruction stub:
      - Add `SLACK_WEBHOOK_URL=PENDING_CONFIGURATION` to runner.env documentation
      - Write `docs/runbooks/SLACK_WEBHOOK_SETUP.md` with exact setup steps
      - Mark OPS-010 as NEEDS_WEBHOOK_URL with clear evidence of what's missing
  6.  Run daily report: `python automation/ai_cycle_controller.py daily-report 2>&1 | tee docs/validation/OPS_022_DAILY_REPORT_C077.txt`
      Verify it covers: cycle status, model verification age, score summary, open blockers.
  7.  Inspect the daily report output — confirm MODEL-014 evidence (model section present).
      Write `docs/validation/MODEL_014_DAILY_REPORT_MODEL_SECTION.md` with the captured output.
  8.  Run weekly report: `python automation/ai_cycle_controller.py weekly-report 2>&1 | tee docs/validation/OPS_023_WEEKLY_REPORT_C077.txt`
      Verify it covers: interruption count, repair count, cycles completed, drift incidents.
  9.  Mark OPS-022 and OPS-023 DONE in their evidence files.
  10. Commit all evidence: `git add docs/validation/ C:/AI_Runner/config/ && git commit -m "feat(ops): OPS-010 notifications, OPS-022/023 production report runs"`

====================================================================

TASK 4 — OPS SCHEDULED TASKS PRODUCTION CONFIRMATION (LARGE, ~50 min)
Deliverable: OPS-004, OPS-008, OPS-009 DONE with live production evidence;
watchdog confirmed; daily snapshot confirmed; weekly maintenance confirmed.

  1.  Check watchdog task: `schtasks /query /tn "FiverrWatchdog" /fo LIST /v 2>&1`
      or `Get-ScheduledTask -TaskName "FiverrWatchdog" -ErrorAction SilentlyContinue`.
      Capture status, last run time, next run time.
  2.  Trigger watchdog manually: `schtasks /run /tn "FiverrWatchdog"` — wait 10 seconds,
      check `C:/AI_Runner/logs/watchdog_*.log` for output. Verify it checked heartbeat.
  3.  Write `docs/validation/OPS_004_WATCHDOG_EVIDENCE.md` — task status, manual run output.
  4.  Check daily snapshot task: `Get-ScheduledTask -TaskName "FiverrDailySnapshot" -ErrorAction SilentlyContinue`
      or equivalent. Trigger it: `schtasks /run /tn "FiverrDailySnapshot"`.
      Check that `C:/AI_Runner/backups/snapshot_*.json` (or similar) was written.
  5.  Write `docs/validation/OPS_008_DAILY_SNAPSHOT_EVIDENCE.md`.
  6.  Check weekly maintenance task: `Get-ScheduledTask -TaskName "FiverrWeeklyMaintenance" -ErrorAction SilentlyContinue`
      Trigger it. Verify it runs `git fetch --all --prune` and writes a maintenance log.
  7.  Write `docs/validation/OPS_009_WEEKLY_MAINTENANCE_EVIDENCE.md`.
  8.  Run status-tick to confirm overall health: `python automation/ai_cycle_controller.py status-tick`
      Health must be GREEN or ORANGE (not RED). If RED: diagnose and fix.
  9.  Write `docs/validation/OPS_030_HEALTHCHECK_EVIDENCE.md` with status-tick output.
  10. Commit: `git add docs/validation/ && git commit -m "feat(ops): OPS-004/008/009 scheduled tasks confirmed live in production"`

====================================================================

TASK 5 — ADR-014, ADR-015, REMAINING DOCUMENTATION (MEDIUM, ~40 min)
Deliverable: ADR-014, ADR-015 written; DOD-002 (master checklist) updated in-repo;
SEC-010 (branch protection scope) investigated; ENV-026 (runner service) evidenced.

  1.  Write `docs/architecture/ADR_014_CROSS_PLATFORM_REPO_ROOT.md`:
      Title, Context (18 modules hardcoded C:/Fiverr/Fiverr), Decision (Path(__file__).parent.parent),
      Consequences (CI works on Linux/Windows), Status ACCEPTED, implementing commits listed.
  2.  Write `docs/architecture/ADR_015_SIX_AGENT_AUTONOMOUS_RUNNER_CYCLE_MODEL.md`:
      Title, Context (single-agent cycles hit limits), Decision (A→B+E→C→F→D fixed order
      with AGENT_COMPLETE handoff contracts), Consequences, Status ACCEPTED since Cycle 070.
  3.  Update `docs/MASTER_CHECKLIST_UPDATED_2026-06-12-POST-C076.md` with Cycle 077 status:
      add rows for BUG-013 through BUG-021 as DONE; update IN_PROGRESS items resolved this task.
  4.  Investigate SEC-010/BUG-011: `gh api /repos/KevinSGarrett/Fiverr/branches/develop/protection`
      Capture exact HTTP status and error. Write `docs/governance/BUG_011_BRANCH_PROTECTION_STATUS.md`
      with the result and exact token scope that would be needed to resolve it.
  5.  Check runner service: `Get-Service -Name "actions.runner.*" | Select-Object Name,Status`
      Write `docs/validation/ENV_026_RUNNER_SERVICE_EVIDENCE.md` with output + timestamp.
  6.  Check BRAIN_REGISTRY has >= 44 entries (BRAIN-002 still valid):
      `python -c "import yaml; r=yaml.safe_load(open('PM_Pack/automation/BRAIN_REGISTRY.yml')); n=sum(len(v) for v in r.get('load_order',{}).values()); print(n, 'entries')"`
  7.  Verify all 15 runbooks exist and are >= 200 words each:
      `python -c "import pathlib; [print(p.name, p.stat().st_size) for p in sorted(pathlib.Path('docs/runbooks').glob('*.md'))]"`
  8.  Write `docs/validation/DOD_002_MASTER_CHECKLIST_CURRENT.md` confirming checklist updated.
  9.  Commit: `git add docs/ && git commit -m "docs(adrs): ADR-014/015, SEC-010 investigation, ENV-026, DOD-002 updated"`

====================================================================

TASK 6 — JIRA: CYCLE 076 DONE TRANSITIONS + MODEL/BRAIN EVIDENCE COMMENTS (LARGE, ~55 min)
Deliverable: All Cycle 076-completed stories transitioned to Done; MODEL and BRAIN
IN_PROGRESS items evidenced in Jira; DOD-011 Jira sync confirmed working.

  1.  Load Jira credentials: `python -c "import os; from dotenv import load_dotenv; load_dotenv(r'C:/AI_Runner/secrets/runner.env'); print('JIRA_API_TOKEN:', 'SET' if os.environ.get('JIRA_API_TOKEN') else 'MISSING')"`
  2.  If token missing: diagnose why the Cycle 076 Agent B fix is not loading. Check
      `automation/config_loader.py` and `automation/jira_client.py` for the load path.
      Fix any remaining issue and verify with `python -c "from automation.jira_client import JiraClient; j=JiraClient(); print('OK:', j.myself())"`.
  3.  Query all non-Done stories: `python -c "from automation.jira_client import JiraClient; j=JiraClient(); issues=j.search_issues('project=SCRUM AND status!=Done ORDER BY updated DESC'); [print(i['key'], i['fields']['status']['name'][:15], i['fields']['summary'][:50]) for i in issues['issues'][:30]]"`
  4.  Transition to Done all stories confirmed completed by Cycle 076 agents (BUG-001 through
      BUG-010 epics, coverage fixes, ADR-011/012/013, CI fixes). Use transition ID 41.
  5.  Post evidence comment on each transitioned story citing the agent report and evidence file.
  6.  Transition "Merge cycle/075/integration PR" story to In_Review (PR #88 exists, CI green).
  7.  Post comment on GJCI-029 story: "PR #88 CI is 4/4 GREEN. Awaiting admin merge. Full DoD
      check will run in Agent D after merge. Evidence: CI run 27450643719."
  8.  Post comment on GJCI-030 story: "Bug ticket creation logic is implemented in jira_client.py.
      Will trigger on first real CI failure in Cycle 077. No current failures to report."
  9.  Write `docs/cycle_reports/CYCLE_077_AGENT_A_JIRA_SYNC.md` — list all transitions, responses.
  10. Mark DOD-011 as DONE: Jira client works, token loads, transitions execute, comments posted.
      Write `docs/validation/DOD_011_JIRA_SYNC_EVIDENCE.md` with the above proof.
  11. Commit: `git add docs/ && git commit -m "feat(jira): Cycle 076 Done transitions, DOD-011 Jira sync confirmed"`

====================================================================

TASK 7 — MODEL DRIFT SIMULATION + MODEL GATE PRODUCTION CONFIRMATION (MEDIUM, ~40 min)
Deliverable: MODEL-013 drift detection proven; DOD-004 model gate evidence updated;
MODEL-008 (Claude model verification) evidenced from post-cycle-review dry run.

  1.  Run model gate check: `python automation/ai_cycle_controller.py run-agent --cycle 077 --agent A --dry-run 2>&1 | head -20`
      Capture any MODEL_GATE output. The gate should show CURSOR_MODEL_GATE: PASS or warn if
      model is within 48h of expiry.
  2.  Write `docs/validation/DOD_004_MODEL_GATE_EVIDENCE.md` — model gate output, cursor_model_state.json
      contents, claude_model_state.json contents, expiry date check.
  3.  Simulate a model drift event: temporarily write a test state file:
      `python -c "import json, pathlib; f=pathlib.Path(r'C:/AI_Runner/state/test_drift_state.json'); f.write_text(json.dumps({'model': 'wrong-model', 'status': 'DRIFT_TEST'}))"`
  4.  Run drift detector: `python -c "from automation.drift_detector import DriftDetector; d=DriftDetector(); result=d.check_drift(r'C:/AI_Runner/state/test_drift_state.json'); print(result)"`
      Verify drift is detected correctly.
  5.  Clean up test state file. Write `docs/validation/MODEL_013_DRIFT_DETECTION_EVIDENCE.md`.
  6.  Run post-cycle-review dry run to produce Claude model verification artifact:
      `python automation/ai_cycle_controller.py post-cycle-review --cycle 076 --mode advisory 2>&1 | tee docs/validation/MODEL_008_CLAUDE_REVIEW_DRY_RUN.txt`
      The output should show claude_model_status being checked. Write MODEL-008 evidence.
  7.  Mark MODEL-013 and MODEL-008 DONE with evidence.
  8.  Commit: `git add docs/validation/ && git commit -m "feat(model): MODEL-013 drift sim, MODEL-008 Claude verification, DOD-004 model gate evidence"`

====================================================================

TASK 8 — FINAL COMMIT, PUSH, CYCLE REPORT (MEDIUM, ~30 min)
Deliverable: All commits pushed; CYCLE_077_AGENT_A.md written; B+E authorized.

  1.  Run full validation suite:
      `python -m ruff check automation/ src/ tests/ -q` — must be 0 errors
      `python -m mypy automation/ --ignore-missing-imports -q` — must be 0 errors
      `python automation/ai_cycle_controller.py brain-check` — must PASS
      `python automation/ai_cycle_controller.py pm-pack-audit` — must PASS
  2.  `git status` — must show clean working tree.
  3.  `git push origin cycle/077/integration`
  4.  Write `docs/cycle_reports/CYCLE_077_AGENT_A.md` with these sections:
      - Branch: cycle/077/integration from develop (or note if PR #88 not yet merged)
      - Stage 1 (OPS-030): DONE — plan-cycle --live PASS, validate-prompts PASS
      - DOD-007: DONE — 55+ task floor verified all 6 agents
      - PM_Pack: all 9 state docs updated
      - ADRs: ADR-014 and ADR-015 written (total ADRs = 15)
      - Slack/OPS-010: [CONFIGURED/NEEDS_WEBHOOK_URL]
      - OPS-022/023: daily/weekly reports run in production — DONE
      - OPS-004/008/009: scheduled tasks confirmed live — DONE
      - MODEL-013: drift detection simulation — DONE
      - MODEL-008: Claude model verification evidence — DONE
      - DOD-004: model gate evidence — DONE
      - DOD-011: Jira sync confirmed — DONE
      - SEC-010/BUG-011: status documented
      - Jira: N stories transitioned to Done
      - Ruff: PASS | Mypy: PASS | brain-check: PASS | pm-pack-audit: PASS
      - AGENT_COMPLETE
  5.  `git add docs/cycle_reports/CYCLE_077_AGENT_A.md && git commit -m "report(cycle-077): Agent A AGENT_COMPLETE" && git push origin cycle/077/integration`

VALIDATION (R-092 Tier 1)
python -m ruff check automation/ src/ tests/ -q
python -m mypy automation/ --ignore-missing-imports -q
python automation/ai_cycle_controller.py brain-check
python automation/ai_cycle_controller.py pm-pack-audit
python automation/ai_cycle_controller.py validate-prompts --cycle 077
gh run list --workflow=ci.yml --limit 1 --json status,conclusion

END OF PROMPT

Agent B and Agent E may start after AGENT_COMPLETE is in CYCLE_077_AGENT_A.md.
