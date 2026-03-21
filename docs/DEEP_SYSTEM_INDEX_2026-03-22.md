# X-Hive Deep System Index (22 Mart 2026)

## 1) Sistem Haritasi
- Desktop UI (Tauri + React): `apps/desktop/src/**`
- Worker API (FastAPI): `apps/worker/app/main.py`
- Approval queue + persistence: `apps/worker/approval/approval_queue.py`
- Orchestrator + intel pipeline: `apps/worker/orchestrator.py`
- X publish engine: `apps/worker/x_daemon.py`
- Browser/session katmani: `apps/worker/chrome_pool.py`
- Installer + publish pipeline: `installer/build_setup_versioned.ps1`, `installer/xhive_setup.iss`, `.agent/workflows/publish.md`

## 2) Kritik Akislar

### 2.1 Intel -> Approval
- Intel kaynaklari periyodik toplanir (orchestrator).
- Viral skor filtrelemesi sonrasi queue'ya item eklenir.
- Queue state diske yazilir: `data/approval_queue.json`.

### 2.2 Approval -> Publish
- UI, pending item'lari `GET /approval/pending` ile listeler.
- Onay: `POST /approval/approve/{item_id}` (state: approved).
- Manuel thread publish: `POST /approval/post-thread/{item_id}?lang=tr|en`.

### 2.3 Auto Scheduler Publish
- Worker icinde auto thread scheduler loop var.
- Saatler env ile kontrol edilir: `AUTO_THREAD_POST_TIMES`.
- Dil sirasi env ile kontrol edilir: `AUTO_THREAD_LANG_ORDER`.
- Aday secimi: approved/edited + ilgili dil publish edilmemis + inflight degil.

### 2.4 TR/EN State
- Queue item dil-bazli state tutar:
  - `published_languages`: `{tr: bool, en: bool}`
  - `published_urls`: `{tr: url, en: url}`
- Tum mevcut diller publish edilince status `processed` olur.

## 3) Mevcut Ana Sorunlar (Tespit)

### P0
- Race/duplicate riski: scheduler ve manuel publish ayni item'i ayni anda tetikleyebilir (inflight lock var ama aday secimi lock disinda).
- Publish retry stratejisi item-level state machine olarak formal degil (publishing/failed/partial yok).

### P1
- UI pending ekrani approved/processed item durumunu gormuyor; operasyon gorunurlugu dusuk.
- API hata semantigi yer yer zayif (kismi durumlarda UI tarafina net ayrismis kod donmuyor).
- Chrome/Playwright kopmalarinda operasyon dayanimi artmis olsa da scheduler tarafinda merkezi retry/backoff politikasi eksik.

### P2
- Test coverage daginik ve kritik akislarda E2E eksik:
  - dual-language publish
  - crash recovery after partial publish
  - scheduler + manual concurrency
  - queue persistence recovery

## 4) UI Durum Endeksi
- Approval ekrani: `apps/desktop/src/components/ApprovalInterface.tsx`
- Mevcut iyilestirme: TR/EN ayri publish butonlari, dil bazli yayinlandi etiketi.
- Geriye kalan eksik:
  - approved/processed sekmeleri
  - item timeline (pending -> approved -> publishing -> processed)
  - failed publish retry aksiyonu

## 5) Build / Release Endeksi
- Fast build (worker-only): `installer/build_setup_versioned.ps1`
- Full build (UI degisikliklerinde gerekli): `installer/build_setup_versioned.ps1 -FullBuild`
- Publish workflow dokumani: `.agent/workflows/publish.md`

## 6) Onerilen Sonraki Faz (Ileri Seviye)
- Faz A: Publish State Machine
  - `PENDING`, `APPROVED`, `PUBLISHING`, `PARTIAL_PUBLISHED`, `FAILED`, `PROCESSED`
- Faz B: Idempotent Publish Job
  - Item-level lock + durable job id
  - restart sonrasi resume
- Faz C: UI Operasyon Merkezi
  - Approval, Scheduled, Publishing, Failed, Processed sekmeleri
  - per-language status chip + retry
- Faz D: E2E Test Paketi
  - Queue persistence + scheduler/manual race + dual-language completion

## 7) Hakimiyet Siniri Notu
- Bu indeks kod tabani ve akislarin derin bir kesitini kapsar.
- Ancak canli ortam davranisi (X tarafi UI degisiklikleri, rate-limit dalgalanmalari, Playwright driver stabilitesi) runtime test olmadan %100 garanti vermez.
- Bu nedenle her release oncesi smoke + canli publish dry-run zorunlu tutulmalidir.
