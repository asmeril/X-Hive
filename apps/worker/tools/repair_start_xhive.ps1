$ErrorActionPreference = 'Stop'

$workerDir = Join-Path $env:LOCALAPPDATA 'XHive\worker'
$venvPython = Join-Path $workerDir '.venv\Scripts\python.exe'
$desktopExe = 'C:\Program Files (x86)\XHive\x-hive-desktop.exe'
$healthUrl = 'http://127.0.0.1:8765/health'

Write-Host "[INFO] XHive hızlı onarım başlatılıyor..." -ForegroundColor Cyan

if (-not (Test-Path $workerDir)) {
    Write-Host "[HATA] Worker klasörü bulunamadı: $workerDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $venvPython)) {
    Write-Host "[HATA] Python venv bulunamadı: $venvPython" -ForegroundColor Red
    Write-Host "[INFO] Uygulamayı bir kez setup ile yeniden kurun (venv otomatik kurulur)." -ForegroundColor Yellow
    exit 1
}

# 1) UI'ı kapat
Get-Process -Name 'x-hive-desktop', 'XHive' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

# 2) app.main çalışan tüm python süreçlerini kapat
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -match '-m app.main' } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {}
    }

Start-Sleep -Seconds 1

# 3) Backend'i ayağa kaldır
$stdoutLog = Join-Path $workerDir 'backend_stdout.log'
$stderrLog = Join-Path $workerDir 'backend_stderr.log'

Write-Host "[INFO] Backend başlatılıyor..." -ForegroundColor DarkCyan
Start-Process -FilePath $venvPython `
    -ArgumentList '-m app.main' `
    -WorkingDirectory $workerDir `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog

# 4) Health kontrolü (max ~20sn)
$ok = $false
for ($i = 0; $i -lt 20; $i++) {
    try {
        $r = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 1000
}

if (-not $ok) {
    Write-Host "[HATA] Backend ayağa kalkmadı. Son log:" -ForegroundColor Red
    if (Test-Path $stderrLog) {
        Get-Content $stderrLog -Tail 40
    }
    exit 1
}

Write-Host "[OK] Backend hazır (8765)." -ForegroundColor Green

# 5) UI aç
if (Test-Path $desktopExe) {
    Start-Process $desktopExe
    Write-Host "[OK] XHive masaüstü açıldı." -ForegroundColor Green
} else {
    Write-Host "[UYARI] Desktop exe bulunamadı: $desktopExe" -ForegroundColor Yellow
    Write-Host "[INFO] Backend çalışıyor; UI'ı manuel açabilirsiniz." -ForegroundColor Yellow
}

Write-Host "[TAMAM] Hızlı onarım bitti." -ForegroundColor Cyan
