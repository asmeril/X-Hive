---
description: Build and publish setup for XHive with versioned Inno compile
---
// turbo-all

# /publish - XHive Yayın Workflow'u

## 0) Pre-Flight (Kritik)
1. `docs/AGENT_LOG.md` güncel mi?
2. Installer değişikliği varsa `installer/xhive_setup.iss` notu işlendi mi?
3. Çalışan backend süreçleri temiz mi?

## 1) Versioned Setup Build (Önerilen Tek Komut)
```powershell
Set-Location "C:\XHive\X-Hive\installer"
.\build_setup_versioned.ps1
```

Bu akış:
- `version.txt` değerini okur ve artırır
- `ISCC` ile `/DMyAppVersion=...` geçerek setup derler
- Yeni sürümü `version.txt` içine kalıcı yazar

## 2) Çıktı Doğrulama
```powershell
Get-ChildItem "C:\XHive\X-Hive\installer\output" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 Name,LastWriteTime,Length
```

## 3) Upgrade Test (Önerilen)
- Kurulu eski sürüm üstüne yeni setup çalıştır.
- Kurulumda uninstall adımının tetiklendiğini doğrula.
- Uygulama açılışında `health` ve temel UI aksiyonlarını smoke test et.

## 4) Hızlı Smoke
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing
```

## 5) GitHub İşlemleri (Zorunlu)
```powershell
Set-Location "C:\XHive\X-Hive"
git status
git add .
git commit -m "release: publish workflow run and setup output update"
git push origin master
```

Notlar:
- Commit öncesi `docs/AGENT_LOG.md` güncel olmalı.
- Branch farklıysa `master` yerine aktif branch kullanılmalı.
