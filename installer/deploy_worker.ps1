###############################################################################
# deploy_worker.ps1
# 
# Gelistirici (development) deploy scripti.
# 
# Kurulu XHive uygulamasinda worker'i yeniden build etmeden gunceller:
#   1. Calisiyorsa worker process'ini durdurur
#   2. Kaynak .py dosyalarini installed worker dizinine kopyalar
#   3. (Opsiyonel) Worker'i tekrar baslatir
#
# KULLANIM:
#   .\deploy_worker.ps1                  # deploy et, worker'i yeniden baslat
#   .\deploy_worker.ps1 -NoRestart       # deploy et, worker'i baslatma
#   .\deploy_worker.ps1 -DryRun          # ne kopyalanacagini goster (kopyalama)
#
###############################################################################

param(
    [switch]$NoRestart,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

$sourceWorker = Join-Path $PSScriptRoot "..\apps\worker"
$destWorker   = Join-Path $env:LOCALAPPDATA "XHive\worker"

# --- Renk yardimcilari ---
function Info($msg)    { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Ok($msg)      { Write-Host "[ OK ] $msg" -ForegroundColor Green }
function Warn($msg)    { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Err($msg)     { Write-Host "[ERR ] $msg" -ForegroundColor Red }

# --- Kaynak dizin kontrolu ---
if (-not (Test-Path $sourceWorker)) {
    Err "Kaynak worker dizini bulunamadi: $sourceWorker"
    exit 1
}
if (-not (Test-Path $destWorker)) {
    Err "Hedef worker dizini bulunamadi: $destWorker"
    Err "XHive kurulu degil veya farkli bir dizinde."
    exit 1
}

Info "Kaynak : $sourceWorker"
Info "Hedef  : $destWorker"
if ($DryRun) { Warn "--- DRY RUN MODU - Hicbir dosya kopyalanmayacak ---" }

# --- Kopyalanacak alt dizinler ---
$subDirs = @('', 'app', 'intel', 'approval', 'posting', 'scheduling', 'tools')

# --- Kopyalanmayacak desenler ---
$excludePatterns = @('test_*', 'debug_*', 'quick_*', 'simple_*', 'verify_*', '*.backup', '*.pyc')

$totalCopied = 0

foreach ($sub in $subDirs) {
    if ($sub -eq '') {
        $srcDir  = $sourceWorker
        $dstDir  = $destWorker
    } else {
        $srcDir  = Join-Path $sourceWorker $sub
        $dstDir  = Join-Path $destWorker   $sub
    }

    if (-not (Test-Path $srcDir)) { continue }
    if (-not (Test-Path $dstDir) -and -not $DryRun) {
        New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    }

    $pyFiles = Get-ChildItem -Path $srcDir -Filter "*.py" -File

    foreach ($file in $pyFiles) {
        $skip = $false
        foreach ($pat in $excludePatterns) {
            if ($file.Name -like $pat) { $skip = $true; break }
        }
        if ($skip) { continue }

        $destFile = Join-Path $dstDir $file.Name

        # Sadece degismisse kopyala
        $needsCopy = $true
        if (Test-Path $destFile) {
            $srcHash  = (Get-FileHash $file.FullName  -Algorithm MD5).Hash
            $dstHash  = (Get-FileHash $destFile -Algorithm MD5).Hash
            if ($srcHash -eq $dstHash) { $needsCopy = $false }
        }

        if ($needsCopy) {
            $relPath = if ($sub) { "$sub\$($file.Name)" } else { $file.Name }
            if ($DryRun) {
                Info "  [KOPYALANACAK] $relPath"
            } else {
                Copy-Item $file.FullName -Destination $destFile -Force
                Info "  Kopyalandi: $relPath"
            }
            $totalCopied++
        }
    }

    # tools/ icin .ps1 dosyalarini da kopyala
    if ($sub -eq 'tools') {
        $ps1Files = Get-ChildItem -Path $srcDir -Filter "*.ps1" -File
        foreach ($file in $ps1Files) {
            $destFile = Join-Path $dstDir $file.Name
            $needsCopy = $true
            if (Test-Path $destFile) {
                $srcHash = (Get-FileHash $file.FullName -Algorithm MD5).Hash
                $dstHash = (Get-FileHash $destFile -Algorithm MD5).Hash
                if ($srcHash -eq $dstHash) { $needsCopy = $false }
            }
            if ($needsCopy) {
                if ($DryRun) {
                    Info "  [KOPYALANACAK] tools\$($file.Name)"
                } else {
                    Copy-Item $file.FullName -Destination $destFile -Force
                    Info "  Kopyalandi: tools\$($file.Name)"
                }
                $totalCopied++
            }
        }
    }
}

if ($DryRun) {
    Ok "Dry-run tamamlandi. $totalCopied dosya kopyalanirdi."
    exit 0
}

if ($totalCopied -eq 0) {
    Ok "Her sey guncel. Kopyalanacak degisiklik yok."
} else {
    Ok "$totalCopied dosya kopyalandi."
}

# --- Worker'i yeniden baslat ---
if ($NoRestart) {
    Warn "Worker yeniden baslatilmadi (-NoRestart). Degisiklikler bir sonraki basisinda gecerli olur."
} else {
    Info "XHive worker yeniden baslatiliyor..."

    # Python worker process'i bul ve kapat
    $workerProcs = Get-Process -Name "python*" -ErrorAction SilentlyContinue | 
        Where-Object { $_.CommandLine -match "x_daemon|uvicorn|main:app" }

    if ($workerProcs) {
        $workerProcs | Stop-Process -Force
        Start-Sleep -Seconds 2
        Ok "Worker durduruldu ($($workerProcs.Count) process)."
    } else {
        Warn "Calisir durumda worker process bulunamadi (XHive uygulamasi uzerinden yeniden baslatabilirsiniz)."
    }
}
