<#
.SYNOPSIS
  Executa um nível de carga: roda o k6 com a coleta de docker stats em paralelo.

.EXAMPLE
  .\scripts\run-level.ps1 -Label c2-vu5 -K6Script .\k6\ticket-load.js `
      -K6Args @("--env","CONFIG=c2","--env","VUS=5","--env","DURATION=2m")
#>
param(
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][string]$K6Script,
    [string[]]$K6Args = @(),
    [string]$OutDir = ".\output\stats",
    [string[]]$Containers = @("tcc-app", "tcc-qdrant")
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$stop = Join-Path $env:TEMP ("tcc-stop-{0}-{1}.flag" -f $Label, $PID)
# No PS 5.1, Remove-Item falha com TEMP em formato curto (8.3) mesmo com -ErrorAction
function Remove-StopFlag([string]$Path) { try { [System.IO.File]::Delete($Path) } catch { } }
Remove-StopFlag $stop

$collectorScript = Join-Path $PSScriptRoot "collect-docker-stats.ps1"
$collector = Start-Process powershell -PassThru -WindowStyle Hidden -ArgumentList @(
    "-NoProfile", "-ExecutionPolicy", "Bypass",
    "-File", "`"$collectorScript`"",
    "-Label", $Label,
    "-OutDir", "`"$OutDir`"",
    "-StopFile", "`"$stop`"",
    "-Containers", ($Containers -join ",")
)

$k6Start = [DateTime]::UtcNow
$k6Exit = -1
try {
    Start-Sleep -Seconds 3
    $k6Start = [DateTime]::UtcNow
    & k6 run @K6Args $K6Script
    $k6Exit = $LASTEXITCODE
}
finally {
    $k6End = [DateTime]::UtcNow
    try { [System.IO.File]::WriteAllText($stop, "stop") } catch { }
    [void]$collector.WaitForExit(20000)
    if (-not $collector.HasExited) { $collector.Kill() }

    [pscustomobject]@{
        label        = $Label
        k6_start_utc = $k6Start.ToString("o")
        k6_end_utc   = $k6End.ToString("o")
        k6_exit_code = $k6Exit
    } | ConvertTo-Json | Set-Content -Path (Join-Path $OutDir "$Label-window.json") -Encoding UTF8
    Write-Host "Janela do k6 registrada em $OutDir\$Label-window.json (use-a para recortar o CSV de stats)."
    Remove-StopFlag $stop
}
