param(
    [string]$Version = ""
)

$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$tauriConfPath = Join-Path $root "apps/desktop/src-tauri/tauri.conf.json"
$packagePath = Join-Path $root "apps/desktop/package.json"
$agentLogPath = Join-Path $root "docs/AGENT_LOG.md"

if (-not (Test-Path $tauriConfPath)) {
    Write-Host "[HATA] tauri.conf.json bulunamadı: $tauriConfPath" -ForegroundColor Red
    exit 1
}

# 1. Mevcut versiyonu al
$tauriConf = Get-Content $tauriConfPath -Raw
if ($tauriConf -match '"version":\s*"([^"]+)"') {
    $currentVersion = $Matches[1]
} else {
    Write-Host "[HATA] tauri.conf.json içinde versiyon bulunamadı." -ForegroundColor Red
    exit 1
}

# 2. Yeni versiyonu belirle
if ($Version -eq "") {
    $parts = $currentVersion.Split('.')
    if ($parts.Count -ne 3) {
        Write-Host "[HATA] Geçersiz versiyon formatı: $currentVersion" -ForegroundColor Red
        exit 1
    }
    $major = [int]$parts[0]
    $minor = [int]$parts[1]
    $patch = [int]$parts[2] + 1
    $newVersion = "$major.$minor.$patch"
} else {
    $newVersion = $Version
}

Write-Host "[INFO] Versiyon güncelleniyor: $currentVersion -> $newVersion" -ForegroundColor Cyan

# 3. tauri.conf.json güncelle
$tauriConf = $tauriConf -replace '"version":\s*"[^"]+"', ('"version": "' + $newVersion + '"')
$tauriConf | Set-Content $tauriConfPath -Encoding UTF8 -NoNewline
Write-Host "[OK] tauri.conf.json güncellendi." -ForegroundColor Green

# 4. package.json güncelle
if (Test-Path $packagePath) {
    $packageJson = Get-Content $packagePath -Raw
    $packageJson = $packageJson -replace '"version":\s*"[^"]+"', ('"version": "' + $newVersion + '"')
    $packageJson | Set-Content $packagePath -Encoding UTF8 -NoNewline
    Write-Host "[OK] package.json güncellendi." -ForegroundColor Green
}

# 5. AGENT_LOG.md güncelle (Opsiyonel)
if (Test-Path $agentLogPath) {
    $agentLog = Get-Content $agentLogPath -Raw
    $date = Get-Date -Format "yyyy-MM-dd HH:mm"
    if ($agentLog -notmatch "## .* - v$newVersion") {
        $header = "## $date - v$newVersion Kararlı Sürüm`n- Kapsam: `n- Yapılan:`n  - `n`n---`n"
        
        # İlk ## başlığının hemen öncesine ekle
        if ($agentLog -match "(?m)^## ") {
            $agentLog = $agentLog -replace "(?m)^## ", ($header + "## ")
        } else {
            # Eğer hiç başlık yoksa sona ekle
            $agentLog += "`n" + $header
        }
        $agentLog | Set-Content $agentLogPath -Encoding UTF8 -NoNewline
        Write-Host "[OK] AGENT_LOG.md güncellendi (Yeni versiyon başlığı eklendi)." -ForegroundColor Green
    }
}

Write-Host "[BİTTİ] Versiyon $newVersion başarıyla uygulandı." -ForegroundColor Magenta
