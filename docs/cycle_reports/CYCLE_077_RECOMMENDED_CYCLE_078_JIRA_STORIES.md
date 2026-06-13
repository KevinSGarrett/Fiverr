# CYCLE 077 -> CYCLE 078 Recommended Jira Stories

1. **Story 1 (XL): Execute Go-Live Stage 7 — 24-hour unattended observation run**
   - AC:
     - `start_24h_observation.ps1` runs for 24h without crash.
     - No unsafe actions (no direct `main` push, no force-push).
     - Health remains GREEN or ORANGE (not RED).
     - Observation summary JSON includes all expected ticks.

2. **Story 2 (XXL): Execute Go-Live Stage 8 — 7-day autonomy trial**
   - AC:
     - Stage 7 PASS prerequisite.
     - At least 3 complete cycles in trial window.
     - At most 5 human interruptions.

3. **Story 3 (XXL): Execute V-4 through V-9 validation gates**
   - AC:
     - Each V-stage produces +2% Score 2 credit on verified PASS.
     - V-4 includes 3-keyword multi-run evidence.

4. **Story 4 (L): Obtain `CODECOV_TOKEN` and wire coverage uploads**
   - AC:
     - Token present in GitHub Secrets.
     - CI uploads coverage XML.
     - Coverage badge appears in README.

5. **Story 5 (M): Fix BUG-011 GitHub branch protection 401**
   - AC:
     - `gh api` branch protection calls return 200.
     - Branch protection evidence updated.

6. **Story 6 (L): Cursor model auto-verification before expiry**
   - AC:
     - 48h before expiry triggers warning and dispatch pause.
     - Re-verify flow documented and tested.

7. **Story 7 (XXL): Daily/weekly Slack report delivery**
   - AC:
     - Daily digest posts at configured time.
     - Weekly summary posts on Monday.

8. **Story 8 (L): EC2 warm standby (ARCH-007)**
   - AC:
     - EC2 health-check runnable.
     - Failover runbook validated.

9. **Story 9 (XXL): 14-day rolling backtesting engine**
   - AC:
     - Runs against 30 historical keywords.
     - Accuracy metrics and error bands reported.

10. **Story 10 (XXL): Upwork signal integration**
    - AC:
      - Upwork signals enrich scoring.
      - At least 3 new score dimensions integrated.

11. **Story 11 (L): Stage 7 debrief and post-observation fixes**
    - AC:
      - All Stage 7 findings documented.
      - Required fixes implemented and verified.

12. **Story 12 (L): Final 24/7 production sign-off pack**
    - AC:
      - Stage 7 evidence consolidated.
      - Production declaration document finalized.
