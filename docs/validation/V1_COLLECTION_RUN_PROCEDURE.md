# V-1 Live Collection Run Procedure

## When to Run
Run V-1 collection when ALL of the following are true:
- Current branch is clean (git status: nothing to commit)
- scrapfly.enabled = False in config (verify before run)
- Cycle-specific evidence path is set (not the default data/ path)
- Explicit PM authorization for this cycle

## Low-Volume Run Parameters (MANDATORY)
- keywords: 1-5 max (start with 1 for first run)
- Use keyword from golden anchor set (reference: data/cycle037_live.db)
- Do NOT run more than 5 keywords without PM authorization

## Run Command
`python run.py collect-live --niche-id <niche_id> --budget-credits 500 --database-url "sqlite:///data/live_pilot_<niche_id>.db" --log-path "data/live_pilot_log.jsonl" --evidence-path "data/cycle_reports/cycle_<cycle>_live_validation_evidence.json"`

## Evidence Capture
After a successful run, call:
`automation.live_validation_writer.write_v1_evidence(status="PASS", ...)`

Write the payload archive to `data/evidence/v1_payload_<date>.json`.
Add `data/evidence/` to `.gitignore` (do not commit raw Fiverr data).

## V-1 Pass Criteria
- At least 1 keyword collection completes without error
- At least 1 gig record returned and parseable
- Payload archive file exists and is non-empty
- live_validation_evidence.json shows v1_status=PASS

## V-2 Unlock Condition
V-2 is unlocked once V-1 PASS evidence exists in live_validation_evidence.json
