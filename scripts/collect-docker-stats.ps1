<#
.SYNOPSIS
  Grava `docker stats` (cerca de 1 amostra/s por contêiner) em CSV e um resumo com média e pico.
  Para ao fim de -DurationSec, quando -StopFile existir ou com Ctrl+C.

.EXAMPLE
  .\collect-docker-stats.ps1 -Label c2-vu5 -DurationSec 130
#>
[CmdletBinding()]
param(
    [string]$Label = "run",
    [string[]]$Containers = @("tcc-app", "tcc-qdrant"),
    [string]$OutDir = ".\output\stats",
    [int]$DurationSec = 0,
    [string]$StopFile = ""
)

$ErrorActionPreference = "Stop"
$inv = [System.Globalization.CultureInfo]::InvariantCulture

# Aceita "a,b" vindo de -File (chega como um único argumento)
$Containers = @($Containers | ForEach-Object { $_ -split "," } | Where-Object { $_ })

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$stamp   = Get-Date -Format "yyyyMMdd-HHmmss"
$csvPath = Join-Path $OutDir "$Label-$stamp.csv"
$sumPath = Join-Path $OutDir "$Label-$stamp-summary.csv"

function ConvertTo-MiB([string]$text) {
    $m = [regex]::Match($text.Trim(), '^([\d\.]+)\s*([KMGT]?i?B)$')
    if (-not $m.Success) { return $null }
    $v = [double]::Parse($m.Groups[1].Value, $inv)
    switch ($m.Groups[2].Value) {
        "B"   { return $v / 1MB }
        "KiB" { return $v / 1024 }
        "MiB" { return $v }
        "GiB" { return $v * 1024 }
        "TiB" { return $v * 1024 * 1024 }
        "kB"  { return $v * 1000 / 1MB }
        "KB"  { return $v * 1000 / 1MB }
        "MB"  { return $v * 1000000 / 1MB }
        "GB"  { return $v * 1000000000 / 1MB }
        default { return $null }
    }
}

# Todos os contêineres precisam estar rodando
foreach ($c in $Containers) {
    try { $running = docker inspect -f "{{.State.Running}}" $c 2>$null } catch { $running = $null }
    if ($running -ne "true") { throw "Contêiner '$c' não está em execução. Suba o ambiente com: docker compose up -d" }
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "docker"
$psi.Arguments = 'stats --format "{{.Name}};{{.CPUPerc}};{{.MemUsage}};{{.MemPerc}}" ' + ($Containers -join " ")
$psi.RedirectStandardOutput = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)

$writer = New-Object System.IO.StreamWriter($csvPath, $false, (New-Object System.Text.UTF8Encoding($false)))
$writer.WriteLine("timestamp_utc,elapsed_s,container,cpu_pct,mem_mib,mem_limit_mib,mem_pct")
$t0 = [DateTime]::UtcNow
$samples = 0
Write-Host "Coletando docker stats de [$($Containers -join ', ')] -> $csvPath"

try {
    while ($true) {
        $line = $proc.StandardOutput.ReadLine()
        if ($null -eq $line) { break }

        # `docker stats` emite sequências ANSI de limpar tela mesmo com saída redirecionada
        $clean = ($line -replace '\x1b\[[0-9;?]*[A-Za-z]', "").Trim()
        if ($clean) {
            $p = $clean -split ";"
            if ($p.Count -ge 4 -and $Containers -contains $p[0]) {
                $mem = $p[2] -split "\s*/\s*"
                $used  = ConvertTo-MiB $mem[0]
                $limit = if ($mem.Count -gt 1) { ConvertTo-MiB $mem[1] } else { $null }
                $cpu = $p[1].Trim().TrimEnd("%")
                $memPct = $p[3].Trim().TrimEnd("%")
                if ($null -ne $used -and $cpu -match '^[\d\.]+$') {
                    $now = [DateTime]::UtcNow
                    $writer.WriteLine(("{0},{1},{2},{3},{4},{5},{6}" -f
                        $now.ToString("o", $inv),
                        ($now - $t0).TotalSeconds.ToString("F1", $inv),
                        $p[0],
                        ([double]::Parse($cpu, $inv)).ToString("F2", $inv),
                        $used.ToString("F2", $inv),
                        $(if ($null -ne $limit) { $limit.ToString("F2", $inv) } else { "" }),
                        $(if ($memPct -match '^[\d\.]+$') { ([double]::Parse($memPct, $inv)).ToString("F2", $inv) } else { "" })))
                    $writer.Flush()
                    $samples++
                }
            }
        }

        if ($DurationSec -gt 0 -and ([DateTime]::UtcNow - $t0).TotalSeconds -ge $DurationSec) { break }
        if ($StopFile -and (Test-Path $StopFile)) { break }
    }
}
finally {
    if (-not $proc.HasExited) { $proc.Kill() }
    $writer.Close()

    if ($samples -gt 0) {
        $rows = Import-Csv $csvPath
        $summary = foreach ($g in ($rows | Group-Object container)) {
            $cpu = $g.Group | ForEach-Object { [double]::Parse($_.cpu_pct, $inv) }
            $mem = $g.Group | ForEach-Object { [double]::Parse($_.mem_mib, $inv) }
            [pscustomobject]@{
                container    = $g.Name
                samples      = $g.Count
                cpu_avg_pct  = ($cpu | Measure-Object -Average).Average.ToString("F2", $inv)
                cpu_peak_pct = ($cpu | Measure-Object -Maximum).Maximum.ToString("F2", $inv)
                mem_avg_mib  = ($mem | Measure-Object -Average).Average.ToString("F2", $inv)
                mem_peak_mib = ($mem | Measure-Object -Maximum).Maximum.ToString("F2", $inv)
            }
        }
        $summary | Export-Csv -Path $sumPath -NoTypeInformation -Encoding UTF8
        Write-Host "`nResumo ($sumPath):"
        $summary | Format-Table -AutoSize | Out-String | Write-Host
    } else {
        Write-Warning "Nenhuma amostra coletada."
    }
}
