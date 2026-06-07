$sha = (git log origin/develop --oneline -1).Split()[0]
$base = "C:\Fiverr\Fiverr\PM_Pack\03_cursor_agent_system\"
Get-ChildItem $base -Filter "CYCLE_069*.md" | ForEach-Object {
    $c = Get-Content $_.FullName -Raw
    Set-Content $_.FullName ($c -replace "\[C069_SQUASH_SHA\]", $sha)
}
Select-String "\[C069_SQUASH_SHA\]" ($base + "CYCLE_069*.md") 2>$null
