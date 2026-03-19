# AGENT LOG

Bu dosya, XHive üzerinde yapılan teknik işlemlerin gerekçeli ve devralınabilir kayıt defteridir.

## 2026-03-19 21:15 - v1.2.6 Stabilizasyon ve Zaman Aşımı Güncellemesi
- Kapsam: `orchestrator.py`, `XDaemonMonitor.tsx`, `App.tsx`, `tauri.conf.json`
- İhtiyaç: Backend'in intel toplama veya AI üretimi sırasında süresiz takılması ve donması.
- Yapılan:
  - **Global Timeouts:** Tüm intel kaynaklarına (özellikle Telegram) ve AI generation pipeline'ına `asyncio.wait_for` eklendi.
  - **Heartbeat:** İzleme paneline `last_intel_collection` (Son Tarama) bilgisi eklendi.
  - **Stale Data Fix:** API hatalarında UI'ın eski "Çalışıyor" verisini temizlemesi sağlandı.
  - **Sequential Build:** Tauri build ve Installer paketleme sıralı hale getirilerek versiyon senkronizasyonu garanti altına alındı.
- Doğrulama: v1.2.6 installer üretildi ve süreçler test edildi.

---

## 2026-03-19 18:00 - Chrome Init Hang ve ContentItem Get Hatası Düzeltmeleri
- Kapsam: `apps/worker/app/main.py`, `apps/worker/chrome_pool.py`, `apps/worker/task_queue.py`, `apps/worker/orchestrator.py`
- İhtiyaç: Backend'in ayağa kalkamaması (Tauri'nin sürekli restart atması) ve AI fallback işlemlerinde AttributeError alınması.
- Kök Neden: 
  - Bazı Intel kaynaklarının (GitHub/Twitter) sonsuz beklemesi.
  - Veri tipi kontrollerinin eksikliği (`dict` vs `ContentItem`).
- Yapılan:
  - `orchestrator.py` içinde Intel toplama işlemlerine timeout eklendi.
  - `ai_content_generator.py` ve `visibility_engine.py` içinde güvenli alan çıkarma sağlandı.
- Doğrulama: `npm run tauri build` + `build_setup_versioned.ps1` akışı denendi.
