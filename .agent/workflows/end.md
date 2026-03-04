---
description: End XHive safely (close desktop + stop backend cleanly)
---
// turbo-all

# /end - XHive Kapatma Workflow'u

## 1) Desktop Sürecini Kapat
```powershell
Get-Process -Name 'x-hive-desktop','XHive' -ErrorAction SilentlyContinue | Stop-Process -Force
```

## 2) Backend Süreçlerini Temizle
```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" |
Where-Object { $_.CommandLine -and $_.CommandLine -match '-m app.main' } |
ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
```

## 3) Port Doğrulama
```powershell
try {
  Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing -TimeoutSec 2
  "[UYARI] Backend hala ayakta"
} catch {
  "[OK] Backend kapalı"
}
```

## 4) Not
Tauri tarafında kapanışta cleanup mevcut; bu workflow manuel/operasyonel güvence adımıdır.

## 5) GitHub İşlemleri (Zorunlu)
```powershell
Set-Location "C:\XHive\X-Hive"
git status
git add .
git commit -m "chore: end workflow checkpoint"
git push origin master
```

Notlar:
- Kapanış öncesi yapılan değişiklikler için commit zorunludur.
- Branch farklıysa `master` yerine aktif branch kullanılmalı.
