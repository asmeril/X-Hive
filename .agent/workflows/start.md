---
description: Start XHive safely (single-backend, health check)
---
// turbo-all

# /start - XHive Başlatma Workflow'u

## 1) Ön Kontrol
- Amaç: Çift backend/poller çakışmasını önlemek.
- Beklenti: `http://127.0.0.1:8765/health` 200 dönmeli.

## 2) Güvenli Başlatma (Önerilen)
```powershell
Set-Location "C:\XHive\X-Hive\apps\worker\tools"
.\repair_start_xhive.ps1
```

Bu adım:
- Masaüstü sürecini kapatır
- `-m app.main` çalışan eski Python süreçlerini temizler
- Backend'i yeniden başlatır
- Health kontrolü sonrası masaüstü uygulamasını açar

## 3) Hızlı Sağlık Kontrolü
```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -UseBasicParsing
```

## 4) Sorun Durumunda
```powershell
Get-Content "$env:LOCALAPPDATA\XHive\worker\backend_stderr.log" -Tail 80
Get-Content "$env:LOCALAPPDATA\XHive\worker\backend_stdout.log" -Tail 80
```
