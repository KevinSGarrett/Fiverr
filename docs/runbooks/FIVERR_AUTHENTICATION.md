# Fiverr Authentication Runbook

## Prerequisites

- Python environment is installed and active.
- Project dependencies are installed.
- `python run.py --help` works from repo root.

## First-Time Login

1. Run:
   - `python run.py relogin`
2. A headed browser window opens to `https://www.fiverr.com/login`.
3. Log in normally with your Fiverr credentials.
4. Complete any 2FA or CAPTCHA challenges.
5. Wait until Fiverr home/dashboard is fully visible.
6. Return to terminal and press Enter only after login is complete.

## What Happens Next

- The session is saved to `data/sessions/fiverr_session.json`.
- Session file directories are created automatically if missing.
- File permissions are set with `chmod 600` on supported platforms.

## Verify Session Before Collection

Run:

- `python run.py session-check`

Expected healthy behavior:

- Command executes without crashing.
- Output clearly reports session state (`VALID` or `EXPIRED`).

If validation fails:

- Run `python run.py relogin` again.

## Public Data vs Authenticated Session

Most Fiverr data used by this pipeline is publicly accessible. Login is a fallback for rate-limit reduction and any authenticated-only content.

- Public-first stages: W3 search results, W4 gig detail, W5 seller profile, W8 autocomplete.
- Session file (`data/sessions/fiverr_session.json`) is still recommended as a safety net.

## Before Your First Collection Run

After running relogin and verifying `session-check` is healthy, run one low-depth collection test to validate selectors:

- `python run.py collect-only`

Monitor the output. Expect some selectors to fail on first run. Document which CSS selectors produced `SelectorError` or empty results so they can be patched in `src/collection/fiverr_selectors.py`.

## How Often to Re-Login

- Fiverr sessions typically expire every 7-14 days.
- Re-run `python run.py relogin` whenever `session-check` reports expired/invalid.

## Security Notes

- `data/sessions/` is gitignored and must never be committed.
- Session files contain authentication state and should be treated like credentials.

## Troubleshooting

- If `session-check` reports missing session file, run `python run.py relogin`.
- If `session-check` reports expired/invalid session, run `python run.py relogin` again.
- Never commit `data/sessions/fiverr_session.json` to git.
