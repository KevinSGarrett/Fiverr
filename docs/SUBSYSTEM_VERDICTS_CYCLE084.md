# Subsystem Verdicts — Cycle 084 Remediation
Generated: 2026-06-18  
Basis: Full audit + phases 1-5 + ICV implementation

---

## SUB-1: Orchestration / State Machine (`ai_cycle_controller.py`)
**Verdict: REPAIRED ✅**

All critical defects addressed:
- **C1** (run-scoped ownership): `pre_dispatch_sha` captured before dispatch; `_get_changed_files` diffs only this-run changes
- **C2** (exit-code truthfulness): non-COMPLETE lifecycles exit non-zero; C2.2 cross-checks `run_record.json`
- **C3** (completion gate): AC verification + ICV verify-repair loop after each agent
- **C4** (blocking review): `blocks_dispatch` now fails on ruff/pytest/ci/coverage/PR/GH-health/ICV-blocked
- **C7** (global lock): `C:/AI_Runner/locks/tick.lock` prevents concurrent tick execution
- **C1.2**: git stash before each agent dispatch
- **M-TICK-1**: `POST_CYCLE_FAIL` explicit handler in tick state machine
- **M-STATUS-1**: `current_status.md` regenerated on every tick
- **OBS-1..15**: Full observability layer (stage context manager, heartbeat, run summary, provider budget)

---

## SUB-2: PM / Prompt Generation
**Verdict: REPAIRED ✅**

- **C5**: PM context no longer truncated to 8000 chars; full Jira descriptions included
- **C6**: Wave, target stories, spec/DOD/TODO paths all derived dynamically from live Jira + config
- **H6**: Strongest available subscription model used (reads `autonomous_runner.yml`)
- **PQ-2**: Per-agent isolation — partial success on single-agent failure
- **PQ-3/4**: Subscription probe gates PM generation; Claude PM None → autopilot pause
- **PQ-6/7**: Code-block ratio + anti-paste uniqueness gates
- **PQ-12**: Empty PM context sections emit warnings
- **PQ-13/14**: Request artifacts saved per agent; provenance stamp in every prompt header

---

## SUB-3: Cursor Dispatch (`cursor_adapter.py`)
**Verdict: REPAIRED ✅**

- **H3**: `--print --force --trust` flags always passed to Cursor
- **H4**: Sub-5-minute runs treated as failed dispatch (not success)
- **OBS-6**: HeartbeatThread monitors Cursor runs; stall alert at 300s
- **C1.2**: Working tree stashed before each dispatch

---

## SUB-4: Post-Agent Lifecycle (`run_agent_lifecycle.py`)
**Verdict: REPAIRED ✅**

- **C1**: Ownership scoped to this-run files via `pre_dispatch_sha` diff
- **C1.4**: Ownership map loaded from `agent_lanes.yml` dynamically
- **H5**: Contract loaded and `validation_commands` executed
- **ICV**: `verify_and_repair_agent()` called after each lifecycle for completion verification

---

## SUB-5: Post-Cycle Review
**Verdict: REPAIRED ✅**

- **C4.1-C4.6**: `blocks_dispatch` fires on all hard-red facts
- **H8.1/H8.3**: Coverage floor 80% as single source of truth (config-driven)
- **C4.6**: ICV blocked agents propagated to `PostCycleFacts.icv_blocked_agents`

---

## SUB-6: Repair (`repair_loop.py` → ICV)
**Verdict: SUPERSEDED ✅**

`repair_loop.py` (targeted VALIDATION_FAILED only, 3-attempt cap) is superseded by the ICV layer which:
- Triggers on ANY incompleteness (not just validation)
- Derives checklist from contract + Jira AC/DoD (not error strings)
- Has loop-governance intelligence (monotonic progress, budget, wall-clock)
- Never exceeds agent ownership lanes
- Records every attempt in `run_dir/icv/ledger_<agent>.json`

---

## SUB-8: State Management
**Verdict: REPAIRED ✅**

- **M-STATE-1**: `write_controller_state` uses read-merge-write (no clobber)
- **M-STATE-2**: `.gitignore` entries exclude runtime artifacts from repo dirtiness check
- **M-STATE-3**: `CycleAuthority.reconcile()` is the single authoritative cycle source; called before pause-check
- **MS2.1/MS2.2**: All run artifacts write to `C:/AI_Runner/` outside the repo

---

## SUB-9: GitHub / Merge
**Verdict: PARTIALLY REPAIRED ⚠️**

- PR detection and CI status in `collect_facts` is functional
- `codex_review_gate.py` blocks merge until review threads resolved
- **MM1.1/MM1.2**: Merge automation remains a manual step (merge-gate retry pattern investigated; decision: keep manual merge to preserve human oversight on main/develop)
- Outstanding: investigate PR #88/#93-100 repeated gate failures (tracked MM1.2)

---

## SUB-10: Jira
**Verdict: REPAIRED ✅**

- **H1**: `_normalise_issue` null-priority crash fixed
- Live Jira data used for all context building (no hardcoded story lists)
- ICV reads Jira AC for checklist items

---

## SUB-11: Infrastructure / Scheduling
**Verdict: REPAIRED ✅**

- **C7.3**: Global tick.lock prevents concurrent execution
- **C7.4**: Parallel controller deprecated; single authoritative checkout
- **LIVE-6**: Both schedulers active — resolved by tick.lock preventing simultaneous ticks

---

## SUB-12: Testing
**Verdict: REPAIRED ✅**

- 164 tests passing across 9 test suites
- ICV package: 29 tests (test_icv.py)
- Observability: 28 tests (test_observability.py)
- Phase 1 regressions: 16 tests (test_phase1_fixes.py)
- Blocking review + OBS: 35 tests (test_blocking_review.py)
- Prompt quality: 21 tests (test_prompt_quality.py)
- Dispatch integration: 3 tests (test_dispatch_integration.py)
- Dead `--ignore` entries removed from CI (MT2.1/MT2.2)
