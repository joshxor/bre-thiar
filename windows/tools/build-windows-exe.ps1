$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'find-godot.ps1')

$Godot = Find-BreGodot
if (-not $Godot) {
    throw 'Godot was not found. Install/extract Godot 4.7.1 for Windows and try again.'
}

$Version = (& $Godot --version 2>&1 | Select-Object -First 1).ToString().Trim()
if ($Version -notmatch '^4\.7\.1') {
    throw "Bré Thiar v0.7.1 is pinned to Godot 4.7.1. Found: $Version"
}

Write-Host "Godot: $Godot ($Version)" -ForegroundColor Cyan
Write-Host 'Running Bré Thiar validation before export...' -ForegroundColor Cyan
& (Join-Path $Root 'VALIDATE_WINDOWS.bat')
if ($LASTEXITCODE -ne 0) { throw "Validation failed with exit code $LASTEXITCODE." }

$Build = Join-Path $Root 'build'
$Dist = Join-Path $Build 'dist'
if (Test-Path $Build) { Remove-Item $Build -Recurse -Force }
New-Item -ItemType Directory -Path $Dist -Force | Out-Null

$Exe = Join-Path $Dist 'BreThiar.exe'
Write-Host 'Exporting Windows release...' -ForegroundColor Cyan
& $Godot --headless --path (Join-Path $Root 'client') --export-release 'Windows Desktop' $Exe
if ($LASTEXITCODE -ne 0) { throw "Godot export failed with exit code $LASTEXITCODE." }
if (-not (Test-Path $Exe)) { throw 'Godot reported success but BreThiar.exe was not created.' }

$Hash = Get-FileHash -Algorithm SHA256 -Path $Exe
$HashLine = "$($Hash.Hash.ToLower())  BreThiar.exe"
Set-Content -Path (Join-Path $Dist 'BreThiar.exe.sha256') -Value $HashLine -Encoding ascii
@'
BRÉ THIAR WINDOWS v0.7.1

Run BreThiar.exe.

For the current development build, the authoritative server is normally launched
with RUN_WINDOWS_DEV.bat from the source package. A public production server is
not bundled into this client build yet.

Controls
  WASD / Arrow keys  Move
  E / Space           Interact
  1 / F / J           Assail
  2                    Focus
  3                    Path skill
  4                    Yew Draught
  Enter                Local chat
  C / I                Character / Chronicle / Inventory
'@ | Set-Content -Path (Join-Path $Dist 'README.txt') -Encoding utf8

$Zip = Join-Path $Build 'BreThiar-Windows-v0.7.1.zip'
Compress-Archive -Path (Join-Path $Dist '*') -DestinationPath $Zip -CompressionLevel Optimal -Force
$ZipHash = Get-FileHash -Algorithm SHA256 -Path $Zip
Set-Content -Path "$Zip.sha256" -Value "$($ZipHash.Hash.ToLower())  $(Split-Path $Zip -Leaf)" -Encoding ascii

Write-Host ''
Write-Host 'WINDOWS EXPORT COMPLETE' -ForegroundColor Green
Write-Host "EXE: $Exe"
Write-Host "ZIP: $Zip"
Write-Host "ZIP SHA-256: $($ZipHash.Hash.ToLower())"
