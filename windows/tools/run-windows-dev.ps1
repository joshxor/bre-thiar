$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Client = Join-Path $Root 'client'
$Server = Join-Path $Root 'server'
. (Join-Path $PSScriptRoot 'find-godot.ps1')

$Node = Get-Command node.exe -ErrorAction SilentlyContinue
if (-not $Node) { $Node = Get-Command node -ErrorAction SilentlyContinue }
if (-not $Node) {
    throw 'Node.js 22+ was not found. Install Node.js before running the authoritative local server.'
}
$major = [int]((& $Node.Source --version).TrimStart('v').Split('.')[0])
if ($major -lt 22) { throw "Node.js 22+ is required; found $(& $Node.Source --version)." }

$Godot = Find-BreGodot
if (-not $Godot) {
    throw 'Godot 4.7.1 was not found in PATH, Downloads, or common install folders.'
}
$GodotVersion = (& $Godot --version 2>&1 | Select-Object -First 1).ToString().Trim()
if ($GodotVersion -notmatch '^4\.7\.1') { throw "Bré Thiar v0.7.1 is pinned to Godot 4.7.1; found $GodotVersion." }

Write-Host '=== Bré Thiar Windows Native Dev ===' -ForegroundColor Cyan
Write-Host "Godot: $Godot"
Write-Host "Node:  $($Node.Source)"

# Let the server choose an unused localhost port. This prevents Bré Thiar from
# colliding with another local project that happens to use the old dev port.
Remove-Item Env:PORT -ErrorAction SilentlyContinue
$env:HOST = '127.0.0.1'
$env:OPEN_BROWSER = '0'
$env:BRE_LOCAL_DEV = '1'

$ServerLog = Join-Path $Server 'server-dev.log'
$ServerErr = Join-Path $Server 'server-dev-error.log'
Remove-Item $ServerLog,$ServerErr -Force -ErrorAction SilentlyContinue
$serverProc = Start-Process -FilePath $Node.Source -ArgumentList 'server.mjs' -WorkingDirectory $Server -WindowStyle Minimized -RedirectStandardOutput $ServerLog -RedirectStandardError $ServerErr -PassThru
try {
    $port = $null
    for ($i=0; $i -lt 80; $i++) {
        $serverProc.Refresh()
        if ($serverProc.HasExited) {
            $err = if (Test-Path $ServerErr) { (Get-Content $ServerErr -Tail 40) -join "`n" } else { 'No server error log.' }
            throw "Authoritative server exited before becoming ready.`n$err"
        }
        if (Test-Path $ServerLog) {
            $text = (Get-Content $ServerLog -Raw -ErrorAction SilentlyContinue)
            if ($text -match 'running at http://127\.0\.0\.1:(\d+)') {
                $port = [int]$Matches[1]
                break
            }
        }
        Start-Sleep -Milliseconds 100
    }
    if (-not $port) {
        $tail = if (Test-Path $ServerLog) { (Get-Content $ServerLog -Tail 40) -join "`n" } else { 'No server log.' }
        throw "Authoritative server did not report its selected port.`n$tail"
    }

    $base = "http://127.0.0.1:$port"
    $healthy = $false
    for ($i=0; $i -lt 30; $i++) {
        try {
            $status = Invoke-RestMethod -Uri "$base/api/status" -TimeoutSec 1
            if ($status.ok -and $status.name -eq 'Bré Thiar Authoritative Server') { $healthy = $true; break }
        } catch {}
        Start-Sleep -Milliseconds 100
    }
    if (-not $healthy) { throw "Authoritative server did not become healthy at $base." }

    $env:BRE_SERVER_HTTP = $base
    $env:BRE_SERVER_WS = "ws://127.0.0.1:$port/ws"
    Write-Host "Authoritative server: READY on port $port" -ForegroundColor Green
    Write-Host 'Launching native Godot client...' -ForegroundColor Green
    & $Godot --path $Client
    if ($LASTEXITCODE -ne 0) { throw "Godot exited with code $LASTEXITCODE." }
}
finally {
    if ($serverProc -and -not $serverProc.HasExited) {
        Stop-Process -Id $serverProc.Id -Force -ErrorAction SilentlyContinue
    }
    Remove-Item Env:BRE_LOCAL_DEV -ErrorAction SilentlyContinue
    Remove-Item Env:BRE_SERVER_HTTP -ErrorAction SilentlyContinue
    Remove-Item Env:BRE_SERVER_WS -ErrorAction SilentlyContinue
}
