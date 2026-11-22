<#
.SYNOPSIS
  Executa os nove niveis do benchmark (c1, c2, c3 x 1, 5, 10 VUs) com run-level.ps1 e, ao final,
  gera as tabelas e graficos. Para no primeiro nivel com erro, salvo com -ContinueOnError.

.EXAMPLE
  .\scripts\rodar-benchmark.ps1
#>
[CmdletBinding()]
param(
    [string[]]$Configs = @("c1", "c2", "c3"),
    [int[]]$VusLevels = @(1, 5, 10),
    [string]$Duration = "2m",
    [int]$PauseSec = 15,
    [string]$BaseUrl = "http://localhost:8080",
    [string]$PriceIn = "0.15",        # string para evitar virgula decimal em pt-BR
    [string]$PriceOut = "0.60",
    [string]$PriceDate = "2026-10-19",
    [string[]]$Containers = @("tcc-app", "tcc-qdrant"),
    [switch]$Force,
    [switch]$Resume,          # pula niveis que ja tem resumo do k6
    [switch]$ContinueOnError
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$BaseUrl = $BaseUrl.TrimEnd("/")
$swTotal = [System.Diagnostics.Stopwatch]::StartNew()

function Stop-Bench([string]$Message) {
    Write-Host ""
    Write-Host "ERRO: $Message" -ForegroundColor Red
    exit 1
}
function Write-Section([string]$Text) {
    Write-Host ""
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host $Text -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
}
function Write-Ok([string]$Text) { Write-Host "  [OK] $Text" -ForegroundColor Green }

# Log completo (transcript)
$logDir = Join-Path $root "output\logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$logFile = Join-Path $logDir ("benchmark-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
$transcribing = $false
try { Start-Transcript -Path $logFile | Out-Null; $transcribing = $true } catch { }

try {
    # pre-checagem
    Write-Section "1/4  PRE-CHECAGEM"

    # k6
    if (-not (Get-Command k6 -ErrorAction SilentlyContinue)) {
        Stop-Bench "O comando 'k6' nao foi encontrado no PATH. Instale (winget install k6 --source winget) e abra um NOVO PowerShell."
    }
    $k6Ver = (& k6 version | Select-Object -First 1)
    Write-Ok "k6 disponivel: $k6Ver"

    # docker + conteineres
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Stop-Bench "O comando 'docker' nao foi encontrado no PATH."
    }
    foreach ($c in $Containers) {
        $prev = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try { $running = (& docker inspect -f "{{.State.Running}}" $c 2>$null) } catch { $running = $null }
        $ErrorActionPreference = $prev
        if ("$running".Trim() -ne "true") {
            Stop-Bench "Conteiner '$c' nao esta em execucao. Suba o ambiente com: docker compose up -d"
        }
        Write-Ok "conteiner em execucao: $c"
    }

    # API
    try {
        $info = Invoke-RestMethod -Uri "$BaseUrl/admin/info" -TimeoutSec 15 -Method Get
    } catch {
        Stop-Bench "GET $BaseUrl/admin/info falhou: $($_.Exception.Message)"
    }
    $infoTxt = ($info | ConvertTo-Json -Compress -Depth 4)
    if ($infoTxt.Length -gt 300) { $infoTxt = $infoTxt.Substring(0, 300) + "..." }
    Write-Ok "GET /admin/info respondeu: $infoTxt"

    # python + bibliotecas do gerador
    $py = $null
    foreach ($cand in @("python", "py")) {
        if (Get-Command $cand -ErrorAction SilentlyContinue) { $py = $cand; break }
    }
    if (-not $py) { Stop-Bench "Python nao encontrado no PATH (necessario para generate_article_assets.py)." }
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & $py -c "import pandas, numpy, matplotlib" 2>$null
    $pyCode = $LASTEXITCODE
    $ErrorActionPreference = $prev
    if ($pyCode -ne 0) {
        Stop-Bench "Faltam bibliotecas Python. Rode: $py -m pip install pandas numpy matplotlib"
    }
    Write-Ok "Python ($py) com pandas, numpy e matplotlib"

    # arquivos necessarios
    $required = @(
        "k6\ticket-load.js", "scripts\run-level.ps1", "scripts\collect-docker-stats.ps1",
        "scripts\generate_article_assets.py", "data\tickets-k6-20.json",
        "output\metrics\requests.csv", "results\eval-100"
    )
    foreach ($f in $required) {
        if (-not (Test-Path (Join-Path $root $f))) { Stop-Bench "Arquivo/pasta obrigatorio ausente: $f" }
    }
    Write-Ok "arquivos do projeto presentes"

    # rodada anterior?
    $statsDir = Join-Path $root "output\stats"
    New-Item -ItemType Directory -Force -Path $statsDir | Out-Null
    $old = @(Get-ChildItem -Path $statsDir -Filter "*-k6-*.json" -ErrorAction SilentlyContinue)
    if ($old.Count -gt 0 -and -not $Force -and -not $Resume) {
        Stop-Bench (("Ja existem {0} resumo(s) do k6 em output\stats (rodada anterior). Mova-os para outra pasta " -f $old.Count) +
            "(e lembre que requests.csv ja tem essas rodadas), use -Resume para retomar pulando os niveis concluidos, ou -Force.")
    }

    # backup do requests.csv
    Write-Section "2/4  BACKUP DE SEGURANCA"
    $req = Join-Path $root "output\metrics\requests.csv"
    $bak = Join-Path $root "output\metrics\requests-eval-100-backup.csv"
    if (Test-Path $bak) {
        Write-Host "  Backup ja existe e foi PRESERVADO (nao sobrescrito): $bak" -ForegroundColor Yellow
    } else {
        Copy-Item -Path $req -Destination $bak
        $nLines = (Get-Content $req | Measure-Object -Line).Lines
        Write-Ok ("backup criado: output\metrics\requests-eval-100-backup.csv ({0} linhas)" -f $nLines)
    }

    # niveis de carga
    $total = $Configs.Count * $VusLevels.Count
    Write-Section ("3/4  BATERIA k6: {0} niveis x {1} (estimativa: ~{2} min no total)" -f $total, $Duration, [int]($total * 3.5 + ($total - 1) * $PauseSec / 60))

    $results = @()
    $i = 0
    foreach ($cfg in $Configs) {
        foreach ($vus in $VusLevels) {
            $i++
            $label = "$cfg-vu$vus"
            Write-Host ""
            Write-Host ("[{0}/{1}] Iniciando nivel {2}  (CONFIG={3}, VUS={4}, DURATION={5})  -  {6}" -f $i, $total, $label, $cfg, $vus, $Duration, (Get-Date -Format "HH:mm:ss")) -ForegroundColor Yellow

            if ($Resume) {
                $done = @(Get-ChildItem -Path $statsDir -Filter "$label-k6-*.json" -ErrorAction SilentlyContinue)
                if ($done.Count -gt 0) {
                    Write-Host ("[{0}/{1}] Nivel {2} ja concluido ({3}) - PULANDO (-Resume)." -f $i, $total, $label, $done[0].Name) -ForegroundColor DarkYellow
                    $results += [pscustomobject]@{ Nivel = $label; Status = "OK (retomado)"; ExitK6 = 0; Minutos = 0 }
                    continue
                }
            }
            $winFile = Join-Path $statsDir "$label-window.json"
            Remove-Item $winFile -ErrorAction SilentlyContinue

            $levelErr = $null
            $sw = [System.Diagnostics.Stopwatch]::StartNew()
            try {
                & (Join-Path $root "scripts\run-level.ps1") -Label $label -K6Script ".\k6\ticket-load.js" -K6Args @(
                    "--env", "CONFIG=$cfg",
                    "--env", "VUS=$vus",
                    "--env", "DURATION=$Duration",
                    "--env", "LABEL=$label",
                    "--env", "BASE_URL=$BaseUrl"
                )
            } catch {
                $levelErr = $_.Exception.Message
            }
            $sw.Stop()

            # codigo de saida real do k6 (gravado por run-level.ps1)
            $exitCode = -1
            if (Test-Path $winFile) {
                try { $exitCode = [int]((Get-Content $winFile -Raw | ConvertFrom-Json).k6_exit_code) } catch { }
            }
            $ok = ($null -eq $levelErr) -and ($exitCode -eq 0)
            $results += [pscustomobject]@{ Nivel = $label; Status = $(if ($ok) { "OK" } else { "FALHOU" }); ExitK6 = $exitCode; Minutos = [math]::Round($sw.Elapsed.TotalMinutes, 1) }

            if ($ok) {
                Write-Host ("[{0}/{1}] Nivel {2} concluido em {3:N1} min." -f $i, $total, $label, $sw.Elapsed.TotalMinutes) -ForegroundColor Green
            } else {
                $msg = "Nivel $label falhou (k6 exit=$exitCode)"
                if ($levelErr) { $msg += ": $levelErr" }
                if ($ContinueOnError) {
                    Write-Host "[$i/$total] AVISO: $msg - seguindo (-ContinueOnError)." -ForegroundColor Red
                } else {
                    Stop-Bench "$msg. Bateria interrompida para nao gastar API. Corrija e retome com: .\scripts\rodar-benchmark.ps1 -Resume  (pula os niveis concluidos). Se o nivel que falhou ficou incompleto, mova seus arquivos de output\stats (e note que requests.csv ja tem as linhas dele com o mesmo run_id)."
                }
            }

            if ($i -lt $total) {
                Write-Host ("  Pausa de {0} s antes do proximo nivel..." -f $PauseSec) -ForegroundColor DarkGray
                Start-Sleep -Seconds $PauseSec
            }
        }
    }

    Write-Host ""
    Write-Host "Resumo da bateria:" -ForegroundColor Cyan
    $results | Format-Table -AutoSize | Out-String | Write-Host

    # tabelas e graficos
    Write-Section "4/4  GERACAO DOS ARTEFATOS DO ARTIGO"
    & $py "scripts\generate_article_assets.py" "--price-in" $PriceIn "--price-out" $PriceOut "--price-date" $PriceDate
    if ($LASTEXITCODE -ne 0) { Stop-Bench "generate_article_assets.py terminou com codigo $LASTEXITCODE." }

    $outDir = Join-Path $root "results\article"
    Write-Host ""
    Write-Host "Arquivos gerados em results\article:" -ForegroundColor Cyan
    Get-ChildItem $outDir | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize | Out-String | Write-Host

    $chk = Join-Path $outDir "checagens.txt"
    if (Test-Path $chk) {
        Write-Host "--- checagens.txt (LEIA ANTES DE USAR OS NUMEROS) ---" -ForegroundColor Yellow
        Get-Content $chk | Write-Host
    }

    $failed = @($results | Where-Object { $_.Status -like "FALHOU*" })
    Write-Host ""
    if ($failed.Count -gt 0) {
        Write-Host ("CONCLUIDO COM {0} NIVEL(IS) COM FALHA - confira o resumo acima." -f $failed.Count) -ForegroundColor Red
    } else {
        Write-Host ("BENCHMARK CONCLUIDO em {0:N1} min. Tabelas: results\article\tabelas.md" -f $swTotal.Elapsed.TotalMinutes) -ForegroundColor Green
    }
    Write-Host "Log completo: $logFile"
}
finally {
    if ($transcribing) { try { Stop-Transcript | Out-Null } catch { } }
}
