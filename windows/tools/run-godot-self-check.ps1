$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Client = Join-Path $Root 'client'
. (Join-Path $PSScriptRoot 'find-godot.ps1')
$Godot = Find-BreGodot
if (-not $Godot) {
    Write-Host 'Godot not found; skipping engine-level headless validation.' -ForegroundColor Yellow
    exit 0
}
Write-Host "Godot engine validation: $Godot" -ForegroundColor Cyan
& $Godot --headless --path $Client --script 'res://tests/headless_world_self_check.gd'
if ($LASTEXITCODE -ne 0) { throw "Godot world self-check failed with exit code $LASTEXITCODE." }
