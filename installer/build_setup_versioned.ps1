$ErrorActionPreference = 'Stop'

$installerDir = "C:\XHive\X-Hive\installer"
$issPath = Join-Path $installerDir "xhive_setup.iss"
$versionFile = Join-Path $installerDir "version.txt"
$isccPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if (-not (Test-Path $isccPath)) {
    Write-Host "[HATA] ISCC bulunamadı: $isccPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $issPath)) {
    Write-Host "[HATA] ISS dosyası bulunamadı: $issPath" -ForegroundColor Red
    exit 1
}

function Parse-Version([string]$versionText) {
    $trimmed = $versionText.Trim()
    if ($trimmed -notmatch '^\d+\.\d+\.\d+$') {
        throw "Geçersiz versiyon formatı: $trimmed (beklenen: x.y.z)"
    }

    $parts = $trimmed.Split('.')
    return [PSCustomObject]@{
        Major = [int]$parts[0]
        Minor = [int]$parts[1]
        Patch = [int]$parts[2]
    }
}

function Increment-Version([int]$major, [int]$minor, [int]$patch) {
    $patch += 1

    if ($patch -gt 9) {
        $patch = 0
        $minor += 1
    }

    if ($minor -gt 9) {
        $minor = 0
        $major += 1
    }

    return "$major.$minor.$patch"
}

if (Test-Path $versionFile) {
    $currentVersion = (Get-Content $versionFile -Raw).Trim()
} else {
    $currentVersion = "1.0.0"
}

$parsed = Parse-Version $currentVersion
$newVersion = Increment-Version -major $parsed.Major -minor $parsed.Minor -patch $parsed.Patch

Write-Host "[INFO] Aday versiyon: $currentVersion -> $newVersion" -ForegroundColor Cyan
Write-Host "[INFO] Setup derleniyor... (AV kilidine karşı otomatik tekrar denenecek)" -ForegroundColor Yellow

$maxAttempts = 4
$attempt = 0
$buildSucceeded = $false

Push-Location $installerDir
try {
    while (-not $buildSucceeded -and $attempt -lt $maxAttempts) {
        $attempt += 1
        Write-Host "[INFO] Derleme denemesi $attempt/$maxAttempts" -ForegroundColor DarkCyan

        & $isccPath "/DMyAppVersion=$newVersion" "$issPath"
        $exitCode = $LASTEXITCODE

        if ($exitCode -eq 0) {
            $buildSucceeded = $true
            break
        }

        if ($attempt -lt $maxAttempts) {
            $sleepSec = 5 * $attempt
            Write-Host "[UYARI] ISCC hata kodu: $exitCode. $sleepSec sn sonra tekrar denenecek..." -ForegroundColor Yellow
            Start-Sleep -Seconds $sleepSec
        } else {
            throw "ISCC hata kodu: $exitCode"
        }
    }
} finally {
    Pop-Location
}

Set-Content -Path $versionFile -Value $newVersion -Encoding ascii
Write-Host "[OK] Derleme tamamlandı ve versiyon kalıcılaştırıldı: $newVersion" -ForegroundColor Green
Write-Host "[OK] Output: C:\XHive\X-Hive\installer\output" -ForegroundColor Green
Write-Host "[INFO] Temiz kurulum (eski sürümü kaldır + yeniyi kur): .\\install_latest_clean.ps1" -ForegroundColor Cyan
