$ErrorActionPreference = 'Stop'

param(
    [string]$SetupPath,
    [switch]$Silent
)

$appName = 'XHive'
$installerDir = 'C:\XHive\X-Hive\installer\output'

function Get-LatestSetupPath {
    param([string]$dir)

    if (-not (Test-Path $dir)) {
        throw "Setup output klasörü bulunamadı: $dir"
    }

    $latest = Get-ChildItem -Path $dir -Filter 'XHive_Setup_*.exe' -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $latest) {
        throw "Kurulum dosyası bulunamadı: $dir\\XHive_Setup_*.exe"
    }

    return $latest.FullName
}

function Get-UninstallEntry {
    param([string]$targetAppName)

    $registryPaths = @(
        'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
        'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*'
    )

    $entries = foreach ($path in $registryPaths) {
        Get-ItemProperty -Path $path -ErrorAction SilentlyContinue |
            Where-Object {
                $_.DisplayName -and (
                    $_.DisplayName -eq $targetAppName -or
                    $_.DisplayName -like "$targetAppName*"
                )
            }
    }

    return $entries | Select-Object -First 1
}

function Get-UninstallExePath {
    param([string]$uninstallString)

    if (-not $uninstallString) {
        return $null
    }

    $trimmed = $uninstallString.Trim()

    if ($trimmed.StartsWith('"')) {
        $secondQuote = $trimmed.IndexOf('"', 1)
        if ($secondQuote -gt 1) {
            return $trimmed.Substring(1, $secondQuote - 1)
        }
    }

    $firstToken = ($trimmed -split '\s+')[0]
    return $firstToken.Trim('"')
}

Write-Host "[INFO] XHive temiz kurulum başlatılıyor..." -ForegroundColor Cyan

# Kullanımda olan süreçleri kapat (dosya kilidini önler)
Get-Process -Name 'x-hive-desktop', 'XHive' -ErrorAction SilentlyContinue |
    Stop-Process -Force -ErrorAction SilentlyContinue

$resolvedSetupPath = if ([string]::IsNullOrWhiteSpace($SetupPath)) {
    Get-LatestSetupPath -dir $installerDir
} else {
    $SetupPath
}

if (-not (Test-Path $resolvedSetupPath)) {
    throw "Setup dosyası bulunamadı: $resolvedSetupPath"
}

Write-Host "[INFO] Setup dosyası: $resolvedSetupPath" -ForegroundColor DarkCyan

$installed = Get-UninstallEntry -targetAppName $appName
if ($installed) {
    $displayVersion = if ($installed.DisplayVersion) { $installed.DisplayVersion } else { 'bilinmiyor' }
    Write-Host "[INFO] Kurulu sürüm bulundu: $($installed.DisplayName) $displayVersion" -ForegroundColor Yellow

    $uninstallExe = Get-UninstallExePath -uninstallString $installed.UninstallString
    if ($uninstallExe -and (Test-Path $uninstallExe)) {
        Write-Host "[INFO] Mevcut sürüm kaldırılıyor..." -ForegroundColor Yellow
        $uninstallArgs = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
        $u = Start-Process -FilePath $uninstallExe -ArgumentList $uninstallArgs -Wait -PassThru
        if ($u.ExitCode -ne 0) {
            throw "Uninstall başarısız. ExitCode: $($u.ExitCode)"
        }
        Write-Host "[OK] Mevcut sürüm kaldırıldı." -ForegroundColor Green
    } else {
        Write-Host "[UYARI] Uninstall komutu bulunamadı. Eski kurulum elle kaldırılmalı olabilir." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Kurulu XHive sürümü bulunamadı; direkt kurulum yapılacak." -ForegroundColor DarkGray
}

Write-Host "[INFO] Yeni setup başlatılıyor..." -ForegroundColor Cyan
if ($Silent) {
    $installArgs = '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART'
    $p = Start-Process -FilePath $resolvedSetupPath -ArgumentList $installArgs -Wait -PassThru
    if ($p.ExitCode -ne 0) {
        throw "Kurulum başarısız. ExitCode: $($p.ExitCode)"
    }
} else {
    $p = Start-Process -FilePath $resolvedSetupPath -Wait -PassThru
    if ($p.ExitCode -ne 0) {
        throw "Kurulum başarısız. ExitCode: $($p.ExitCode)"
    }
}

Write-Host "[OK] XHive temiz kurulum tamamlandı." -ForegroundColor Green
