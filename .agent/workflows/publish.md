---
description: Build and publish setup for XHive with versioned Inno compile
---
// turbo-all

# /publish - XHive Yayın Workflow'u

## 0) Pre-Flight (Kritik)
1. `docs/AGENT_LOG.md` güncel mi?
2. Installer değişikliği varsa `installer/xhive_setup.iss` notu işlendi mi?
3. Çalışan backend süreçleri temiz mi?

## 0.5) Otomatik Versiyon Artır
```powershell
# Versiyonu otomatik artır ve tauri.conf.json / package.json / AGENT_LOG.md günceller.
if (Test-Path "$PSScriptRoot/../../bump-version.ps1") {
    & "$PSScriptRoot/../../bump-version.ps1"
} elseif (Test-Path "bump-version.ps1") {
    & "./bump-version.ps1"
}
```

## 1) Zorunlu Tauri Release Build
```powershell
# Set-Location to apps/desktop regardless of where the repo is
Set-Location "$PSScriptRoot/../apps/desktop" -ErrorAction SilentlyContinue
# Fallback for manual run
if ($LASTEXITCODE -ne 0) { Set-Location "apps/desktop" }
npm run tauri build
```

## 1.1) Zorunlu Stabilizasyon Bekleme (En az 120 sn)
```powershell
Start-Sleep -Seconds 120
Get-Process tauri,cargo,rustc -ErrorAction SilentlyContinue
```

Not:
- Tauri build tamamlandıktan sonra en az 2 dakika beklenir.
- Arka planda derleme/artifact yazımı sürüyorsa bu adımda görünür.

Not:
- `apps/desktop` veya `apps/desktop/src-tauri` tarafında değişiklik varsa bu adım atlanamaz.
- Installer, `apps/desktop/src-tauri/target/release/x-hive-desktop.exe` dosyasını paketler.

## 2) Versioned Setup Build (Önerilen Tek Komut)
```powershell
Set-Location "../../installer" -ErrorAction SilentlyContinue
# Fallback
if ($LASTEXITCODE -ne 0) { Set-Location "installer" }
.\build_setup_versioned.ps1
```

Bu akış:
- `version.txt` değerini okur ve artırır
- `ISCC` ile `/DMyAppVersion=...` geçerek setup derler
- Yeni sürümü `version.txt` içine kalıcı yazar

## 3) Çıktı Doğrulama
```powershell
Get-ChildItem "output" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length
```

- `XHive_Setup_v*.exe` çıktısının yeni timestamp ile üretildiğini doğrula.

## 4) Upgrade Test (Önerilen)
- Kurulu eski sürüm üstüne yeni setup çalıştır.
- Kurulumda uninstall adımının tetiklendiğini doğrula.
- Uygulama açılışında `health` ve temel UI aksiyonlarını smoke test et.

## 5) Hızlı Smoke
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing
```

## 6) GitHub İşlemleri (Zorunlu)
```powershell
# Set-Location back to repo root
Set-Location ".." -ErrorAction SilentlyContinue
git status
git add .
git commit -m "release: publish workflow run and setup output update"
git push origin master
```

Notlar:
- Commit öncesi `docs/AGENT_LOG.md` güncel olmalı.
- Branch farklıysa `master` yerine aktif branch kullanılmalı.
