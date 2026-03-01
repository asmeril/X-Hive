# X-HIVE

Viral X otomasyonu: Telegram tabanlı onay akışı ile günde 3 paylaşım.

## Misyon
AI destekli karar mekanizması ve insan onayı ile sosyal medya içerik üretimi, kürasyonu ve X (Twitter) paylaşımının otomasyonu.

## Özellikler

### Günlük Paylaşımlar
- **Hedef**: Günde 3 paylaşım
- **Onay**: Telegram botu (SEND / EDIT / SKIP)
- **Risk Yönetimi**: Yüksek riskli/kontraversiyel içerik → otomatik SKIP

### Intel Kaynakları
- Telegram kanalları (Tele-Sentinel)
- Prediction markets
- X seed hesaplar (≥50 takipçi)

**Working Sources (9 total - ~309 items):**

*API-Based (Fast, No Auth):*
- ✅ **Hacker News**: 30 items (~2s)
- ✅ **ArXiv**: 120 papers (~5s)
- ✅ **Product Hunt**: 20 products (~3s)
- ✅ **Substack**: 9 newsletters (~8s, RSS, 4/6 feeds)
- ✅ **HuggingFace**: 50 models (~5s)
- ✅ **GitHub Trending**: 25 repos (~5s) ✅ FIXED
- ✅ **Polymarket**: 15 prediction markets (~3s) 🆕 NEW
- ✅ **RSS News**: 20 items (~5s, 5/6 feeds) 🆕 NEW

*Cookie-Based (Require Auth):*
- ✅ **Twitter/X Trends**: 20 trends (~30s, Playwright) ✅ FIXED

**Issues/Blocked:**
- ⚠️ **Reddit**: Timeout issues (needs investigation)
- ⚠️ **Google Trends**: RSS feed 404 error
- ❌ **Perplexity**: Cloudflare JS challenge
- ❌ **Medium**: Cloudflare (archived to `_archived/`)

**Recent Integrations from HiveProjesi:**
- 🆕 **Polymarket**: Prediction market intelligence (Gamma API with fallback endpoints)
- 🆕 **RSS News**: Multi-domain aggregator (BBC World, Nature, Defense News, NewAtlas, Medical News, AutoBlog)

**Future Enhancements (from HiveProjesi):**
- 📋 Enhanced GitHub: Topic-based search (AI, TECH, FINANCE) with 48-hour window
- 📋 Enhanced HuggingFace: Topic filtering (FINANCE, BUSINESS, PERSONAL, GLOBAL, TECH)

**Not Implemented:**
- ⏸️ Twitter/X (influencer tweets) - needs implementation
- ⏸️ YouTube - needs implementation  
- ⏸️ LinkedIn - needs implementation

### Global Lock Standardı
- **Yol**: `C:\XHive\locks\x_session.lock`
- **Amaç**: XiDeAI_Pro ile eşzamanlı çalışmayı engellemek
- **TTL**: 24 saat (otomatik temizlik)

## Mimari

```
X-HIVE Monorepo
├── apps/
│   ├── desktop/           # Tauri + React UI (onay arayüzü)
│   └── worker/            # Python FastAPI + Playwright (otomasyon)
├── packages/
│   └── contracts/         # Ortak şemalar & tipler
└── docs/                  # Prosedürler & dokümantasyon
```

### Desktop (Tauri + React)
- Seed hesap yönetimi
- Taslak inceleme arayüzü
- Gerçek zamanlı worker durumu
- Telegram entegrasyon bildirimleri

### Worker (Python FastAPI + Playwright)
- Çoklu kaynaktan intel toplama
- İçerik üretimi ve kuyruğa alma
- Otomatik X.com paylaşımı
- Telegram onay akışı
- Günlük 3 paylaşım hedefli zamanlayıcı

## Başlangıç

### Worker Kurulumu
```bash
cd apps/worker
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8765
```

### Desktop Setup
```bash
cd apps/desktop
npm install
npm run tauri dev
```

## Modules

- **apps/desktop**: Tauri + React UI for approval interface
- **apps/worker**: Python FastAPI backend for automation
- **packages/contracts**: Shared data schemas and types
- **docs**: Operational procedures and deployment guides
