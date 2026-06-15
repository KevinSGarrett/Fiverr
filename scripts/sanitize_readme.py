"""
Sanitize a repo export before sharing with agents/Claude/Cursor.
NEVER export the raw working directory. Always run this first.

Usage: python scripts/sanitize_repo_export.ps1
Or call from PowerShell: .\scripts\sanitize_repo_export.ps1 -OutputZip export.zip
"""
# This is a Python helper — the actual script is sanitize_repo_export.ps1
