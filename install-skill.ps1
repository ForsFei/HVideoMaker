$ErrorActionPreference = "Stop"
$skillHome = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $env:USERPROFILE ".codex\skills" }
$target = Join-Path $skillHome "hnova-video"
$source = Join-Path $PSScriptRoot "skills\hnova-video"
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -LiteralPath (Join-Path $source "SKILL.md") -Destination $target -Force
Copy-Item -LiteralPath (Join-Path $source "agents") -Destination $target -Recurse -Force
Write-Output "Skill installed: $target"
