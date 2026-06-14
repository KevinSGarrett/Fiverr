# Evidence Export Policy — MANDATORY

All evidence ZIPs shared externally MUST be produced by:
`C:\AI_Runner\scripts\make_evidence_pack.ps1`

Raw directory ZIPs are PROHIBITED. They may contain:
- `C:\Fiverr\Fiverr\.env` (API keys)
- `C:\AI_Runner\secrets\runner.env` (runner secrets)
- `C:\actions-runner\.credentials` (GitHub runner identity)

Verify any ZIP before sharing:
`python automation/export_sanitizer_verify.py --zip evidence.zip`
