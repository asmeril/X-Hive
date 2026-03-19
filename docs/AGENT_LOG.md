# AGENT LOG

Bu dosya, XHive üzerinde yapılan teknik işlemlerin gerekçeli ve devralınabilir kayıt defteridir.

## 2026-03-19 21:00 - v1.2.5 Kararlı Sürüm (Sync & UI Fix)
- Kapsam: `lib.rs`, `App.tsx`, `tauri.conf.json`, `chrome_pool.py`
- İhtiyaç: Playwright (EPIPE) çökmesi, süreç temizleme sorunları ve tanı panelindeki yanlış raporlama/buton gizleme hatalarının giderilmesi.
- Yapılan:
  - Tanı ve temizlik scriptlerine `run.py` desteği eklendi.
  - Asılı `node.exe` süreçlerini öldürme mantığı eklendi.
  - `App.tsx` üzerinden "Backend'i Başlat" butonu her durumda ulaşılabilir kılındı.
  - Versiyon **v1.2.4** olarak güncellendi.
- Doğrulama: Tüm senaryolar (manuel restart, otomatik temizlik) test edildi.

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
