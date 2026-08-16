function Find-BreGodot {
    $commands = @('godot.exe','godot4.exe','godot')
    foreach ($name in $commands) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    $candidates = @(
        "$env:USERPROFILE\Downloads",
        "$env:LOCALAPPDATA\Programs\Godot",
        "$env:ProgramFiles\Godot",
        "${env:ProgramFiles(x86)}\Godot"
    ) | Where-Object { $_ -and (Test-Path $_) }
    foreach ($folder in $candidates) {
        $hit = Get-ChildItem -Path $folder -Filter 'Godot*.exe' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch 'console' } |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}
