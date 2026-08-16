$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Client = Join-Path $Root 'client'
. (Join-Path $PSScriptRoot 'find-godot.ps1')
$Godot = Find-BreGodot
if (-not $Godot) { throw 'Godot 4.7.1 was not found in PATH, Downloads, or common install folders.' }
$GodotVersion = (& $Godot --version 2>&1 | Select-Object -First 1).ToString().Trim()
if ($GodotVersion -notmatch '^4\.7\.1') { throw "Bré Thiar v0.7.1 is pinned to Godot 4.7.1; found $GodotVersion." }
& $Godot --editor --path $Client
if ($LASTEXITCODE -ne 0) { throw "Godot editor exited with code $LASTEXITCODE." }
