# AGENT LOG

Bu dosya, XHive üzerinde yapılan teknik işlemlerin gerekçeli ve devralınabilir kayıt defteridir.

## 2026-03-19 21:50 - Backend Crash Loop Diagnostics & Intel Collection Isolation Test
- **Kapsam:** Production backend, Intel collection pipeline, Tauri health monitor cycle
- **Sorun:** Backend v1.2.6'da başlıyor ama ~90s sonra sık sık çöküyor. Tauri health monitor 3 fail after restart loop'una giriyor.
- **Belirlenen Neden:** 
  - Backend manuel başlatıldığında başarılı başlıyor (tüm sistemler initialize oluyor)
  - Orchestrator `run()` loop başlıyor ve intel collection başlatıyor
  - Intel collection geçtiği noktada process terminate oluyor (unhandled exception veya fatal error)
  - Tauri health monitor `/health` 3 kere fail → restart cycle
- **v1.2.6 Timeout Validations:**
  - ✅ GitHub: 30s timeout with asyncio.wait_for
  - ✅ Google Trends: 30s timeout
  - ✅ HackerNews: 20s timeout
  - ✅ Reddit: 45s timeout
  - ✅ Telegram: 30s timeout (with exception handling)
  - ✅ AI Generation: 120s timeout
  - ✅ Visibility Enrichment: 60s timeout
  - Timeouts **VAR** ama crash hala happening - bu timeout layer'ının FARK problem src barındırması anlamına  gelebilir.
- **Yapılan Çözüm:**
  1. **Intel Collection DISABLED** (`orchestrator.config.intel_enabled=False`) - Backend stabilizesi amaçlı
  2. **test_intel_isolation.py** oluşturuldu - Her intel source'u izole test etmek için
  3. Logs daha ayrıntılı debug mode'a alındı
  4. Production path'ten backend başlatıldı: C:\Users\ttevf\AppData\Local\XHive\worker
- **Sonraki Adımlar:**
  1. Backend stabilitiesi çalışıp çalışmadığını test et (Intel disabled)
  2. Intel isolation test çalıştırarak hangi source crash edip etmediğini bul
  3. Crash eden source'ı fix et veya skip et
  4. Intel collection'ı re-enable et
  5. Full pipeline test et (intel → AI generation → viral threads)
- **Files Modified:**
  - `apps/worker/app/main.py`: `intel_enabled=False` set for v1.2.6 patch
  - `apps/worker/test_intel_isolation.py`: New diagnostic utility

---

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
