# AGENT LOG

Bu dosya, XHive üzerinde yapılan teknik işlemlerin gerekçeli ve devralınabilir kayıt defteridir.

---

## 2026-03-05 00:00 - Build Öncesi Stabilizasyon ve Installer Güçlendirme
- Kapsam: `apps/worker/ai_content_generator.py`, `apps/worker/telegram_hub.py`, `apps/desktop/src-tauri/src/lib.rs`, `apps/desktop/src/main.tsx`, `installer/xhive_setup.iss`, build scriptleri
- İhtiyaç: Özelliklerin görünmemesi/çalışmaması, backend erişim problemi, installer uninstall ve sürüm akışında tutarsızlıklar
- Kök Neden: Üretim `.env` ile kaynak `.env` uyumsuzluğu; backend başlangıcını kıran string/syntax hatası; çoklu backend instance kaynaklı çakışmalar; installer tarafında uninstall akışının zayıf olması; version define geçişinin her zaman zorlanmaması
- Yapılan:
  - Üretim `.env` ile kaynak değerleri senkron kontrol edildi
  - `ai_content_generator.py` içindeki kırık çok satırlı string/syntax sorunu düzeltildi
  - Visibility/approval alanlarının frontend+worker akışı teyit edildi
  - Sniper ve post-thread endpointleri canlı çağrılarla doğrulandı
  - Telegram metin kaçış/biçim kaynaklı kırılmalara karşı iyileştirme yapıldı
  - Desktop kapanış/açılışta backend süreç temizliği için lifecycle düzenlemesi eklendi
  - `xhive_setup.iss` uninstall akışı XiDeAI'deki sağlam yaklaşıma yakınsandı
  - Build scriptlerinde sürüm define akışı (`version.txt` -> setup define) güçlendirildi
- Doğrulama: API endpoint çağrıları, worker log kayıtları, dosya içerik doğrulaması
- Risk/Açık Konu: Son installer derleme/kurulum senaryosunun (eski sürüm üstüne kurulum) uçtan uca yeniden teyidi gerekli; Telegram tarafında dışarıdan ikinci poller varsa `409` tekrar edebilir
- Sonraki Adım: Versioned setup derleyip, kurulu sürüm üstüne kurulumda uninstall davranışını test etmek; paketli sürümde tek-instance smoke test

## 2026-03-05 00:10 - Agent Workflow Seti Eklendi (/start, /end, /publish)
- Kapsam: `.agent/workflows/start.md`, `.agent/workflows/end.md`, `.agent/workflows/publish.md`, `docs/README.md`
- İhtiyaç: XiDeAI Pro'daki benzer operasyonel komut düzenini XHive'e taşımak ve devralınabilir çalışma akışı sağlamak
- Kök Neden: Operasyon adımları dağınık kaldığında (özellikle start/stop/publish) hata tekrarı ve süreç çakışması riski artıyor
- Yapılan:
  - XHive için üç workflow dosyası oluşturuldu: başlatma, kapatma, yayın
  - `start` akışına `repair_start_xhive.ps1` tabanlı güvenli başlatma konuldu
  - `end` akışına desktop+`app.main` süreç temizliği ve port doğrulama adımı eklendi
  - `publish` akışına `build_setup_versioned.ps1` temelli sürümlü setup derleme adımları konuldu
  - `docs/README.md` içinde yeni workflow indeks bölümü eklendi
- Doğrulama: Dosyalar oluşturuldu, yollar ve komutlar mevcut scriptlerle eşleştirildi
- Risk/Açık Konu: Workflow komutları operasyonel; son paket sonrası ortam bazlı küçük path farkları kontrol edilmeli
- Sonraki Adım: İlk yayın denemesinde workflow'ları birebir çalıştırıp gerekiyorsa path/çıktı notlarını revize etmek

## 2026-03-05 00:15 - /publish ve /end Workflow'larına GitHub Adımları Eklendi
- Kapsam: `.agent/workflows/publish.md`, `.agent/workflows/end.md`
- İhtiyaç: Workflow kapanış ve yayın adımlarında commit/push işlemlerinin standartlaştırılması
- Kök Neden: Git adımı workflow'a gömülü olmadığında değişiklikler yerelde kalabiliyor ve devir zinciri kırılıyor
- Yapılan:
  - `/publish` akışına zorunlu `git status`, `git add .`, `git commit`, `git push origin master` adımları eklendi
  - `/end` akışına oturum kapanış checkpoint commit/push adımları eklendi
  - Her iki akışa branch farklılığı notu eklendi (`master` yerine aktif branch)
- Doğrulama: Workflow dosyaları içerik kontrolü ile güncellendi
- Risk/Açık Konu: Commit mesajı şablonları genel; takım isterse konvansiyon bazlı (feat/fix/chore) daha katı hale getirilebilir
- Sonraki Adım: İstenirse commit mesajlarını otomatik üreten küçük `git_checkpoint.ps1` yardımcı scripti eklemek

## 2026-03-05 00:20 - Git Remote Token Temizliği + iDeaLQuant Transfer Ön Kontrol
- Kapsam: `c:\XHive\X-Hive\.git\config`, GitHub repo erişim kontrolü
- İhtiyaç: Token içeren remote URL'yi temizlemek ve `iDeaLQuant` deposunu `asmeril` hesabına aktarma hazırlığını doğrulamak
- Kök Neden: Remote URL içinde gömülü PAT güvenlik riski yaratıyor; hedef repoda (`asmeril/iDeaLQuant`) henüz kaynak görünür değil
- Yapılan:
  - `X-Hive` origin URL içindeki token kaldırılarak temiz HTTPS URL'ye çevrildi
  - `marvelariantomarbun-spec/iDeaLQuant` kaynak repo erişimi doğrulandı
  - `asmeril/iDeaLQuant` hedef URL kontrolünde 404 tespit edildi (repo henüz yok)
- Doğrulama: `.git/config` içerik kontrolü + GitHub sayfa kontrolü
- Risk/Açık Konu: Aktarım için hedef repoyu oluşturma ve push yetkili kimlik doğrulaması gerekiyor
- Sonraki Adım: `asmeril/iDeaLQuant` repoyu oluşturup mirror push komutlarıyla içeriği taşımak

## 2026-03-05 00:30 - iDeaLQuant Repo Mirror Aktarımı Tamamlandı
- Kapsam: `https://github.com/marvelariantomarbun-spec/iDeaLQuant` -> `https://github.com/asmeril/iDeaLQuant`
- İhtiyaç: Kaynak projeyi `asmeril` hesabına birebir taşımak
- Kök Neden: Hedef repo oluşturulmadan önce push yapılamıyordu
- Yapılan:
  - Mirror clone alındı: `git clone --mirror`
  - Push URL hedefi `asmeril/iDeaLQuant` olarak ayarlandı
  - `git push --mirror` ile tüm refs taşındı
- Doğrulama: Task çıktısında `To https://github.com/asmeril/iDeaLQuant.git` ve `[new branch] main -> main`
- Risk/Açık Konu: Repoda `src/crash_log.txt` (54 MB) için GitHub large-file uyarısı var; ileride LFS/cleanup değerlendirilmeli
- Sonraki Adım: Hedef repoda branch/tag görünürlüğünü webden kontrol etmek; gerekirse release/koruma kuralları eklemek

## 2026-03-05 01:35 - /publish Workflow'a Zorunlu Tauri Build Adımı Eklendi
- Kapsam: `.agent/workflows/publish.md`
- İhtiyaç: Desktop/Tauri tarafındaki geliştirmelerin setup paketine kesin yansımasını sağlamak
- Kök Neden: Sadece installer derlemek, eski `x-hive-desktop.exe` kullanıldığı durumda UI/Tauri değişikliklerini pakete almayabiliyor
- Yapılan:
  - `/publish` akışına setup derlemeden önce zorunlu `npm run tauri build` adımı eklendi
  - Installer'ın paketlediği dosya yolu net şekilde belirtildi: `apps/desktop/src-tauri/target/release/x-hive-desktop.exe`
  - Publish adımları yeniden numaralandırıldı
- Doğrulama: Workflow dosyası içerik kontrolü ile yeni adımın setup build'den önce konumlandığı doğrulandı
- Risk/Açık Konu: `npm run tauri build` süresi ortama göre uzayabilir; CI/CD'de cache stratejisi düşünülebilir
- Sonraki Adım: Bir sonraki release'te workflow'u birebir çalıştırıp Tauri binary timestamp + setup timestamp uyumunu kontrol etmek

## 2026-03-05 01:45 - /publish Düzeltme Koşusu (2+ dk Tauri bekleme ile) Tamamlandı
- Kapsam: `.agent/workflows/publish.md`, `apps/desktop/src-tauri/target/release/x-hive-desktop.exe`, `installer/version.txt`, `installer/output`
- İhtiyaç: Tauri build sonrası en az 2 dakika bekleme şartını uygulayarak publish'i doğru şekilde tamamlamak
- Kök Neden: Hızlı geri dönüşte Tauri derleme süreçleri (`cargo/rustc`) hâlâ çalışırken setup derlemeye geçilmişti
- Yapılan:
  - Publish workflow'a `1.1` adımı olarak zorunlu `Start-Sleep -Seconds 120` + süreç kontrolü eklendi
  - Tauri build yeniden çalıştırıldı ve süreçler tamamen bitene kadar beklendi (`PROC=NONE` doğrulandı)
  - Tauri binary güncel zaman damgası doğrulandı (`x-hive-desktop.exe`)
  - Setup yeniden derlendi ve yeni çıktı üretildi: `XHive_Setup_v1.1.2_20260305_014427.exe`
  - `version.txt` değeri `1.1.2` olarak güncellendi
- Doğrulama: Tauri süreç sonlanma kontrolü + setup derleme çıktısında `Successful compile` kaydı
- Risk/Açık Konu: Tauri derleme süresi makine yüküne bağlı değişebilir; bekleme sonrası süreç kontrolü zorunlu tutulmalı
- Sonraki Adım: Kurulu sürüm üstüne `install_latest_clean.ps1` ile upgrade testi ve kısa smoke test

## 2026-03-05 01:40 - /publish Çalıştırıldı (v1.1.1)
- Kapsam: `apps/desktop`, `installer/build_setup_versioned.ps1`, `installer/version.txt`, `installer/output`
- İhtiyaç: Güncel workflow ile publish akışını (Tauri build + setup build) uçtan uca çalıştırmak
- Kök Neden: Setup paketinin güncel desktop/worker artefact'larıyla üretilmesi ve sürüm artışının kalıcılaştırılması
- Yapılan:
  - `npm run tauri build` çalıştırıldı (`apps/desktop`)
  - `build_setup_versioned.ps1` ile yeni setup üretildi
  - `version.txt` değeri `1.1.1` olarak güncellendi
  - Yeni setup çıktısı üretildi: `XHive_Setup_v1.1.1_20260305_013630.exe`
- Doğrulama: `installer/output` klasöründe yeni dosya görüldü; setup sürümü `1.1.1` olarak doğrulandı
- Risk/Açık Konu: `x-hive-desktop.exe` timestamp'i değişmedi (incremental/no-op build olasılığı); release öncesi gerekirse clean rebuild stratejisi uygulanmalı
- Sonraki Adım: Bu publish koşusunu git commit/push ile finalize etmek ve kurulu sürüm üstüne temiz upgrade testi yapmak

## 2026-03-07 00:35 - Telegram 409 Kaynaklı Backend Düşmesi ve Stabilizasyon
- Kapsam: `apps/worker/app/main.py`, `apps/worker/content_generator.py`, `apps/desktop/src-tauri/src/lib.rs`, `apps/desktop/src/components/ApprovalInterface.tsx`, `installer/build_setup_versioned.ps1`
- İhtiyaç: Desktop'ta backend'in aralıklı düşmesi, Durum sekmesinde sürekli `0 listener / API Yanıt Yok`, Onay sekmesinde "Yeni Tarama" sonrası içeriklerin gelmemesi
- Kök Neden: Telegram Bot API `409 Conflict` (aynı bot token için eşzamanlı polling) backend'i düşürüyordu; ayrıca health monitor tek timeout'ta agresif restart yaparak döngü oluşturuyordu
- Yapılan:
  - `content_generator.py` içinde ikinci Telegram polling kaynağı kaldırıldı (duplicated polling engellendi)
  - Worker başlangıcında Telegram Hub polling varsayılanı `TELEGRAM_HUB_ENABLED=false` yapıldı (stabilite modu)
  - Tauri health monitor daha toleranslı hale getirildi (ardışık hata eşiği + listener/process kontrolü)
  - Onay ekranındaki manuel tarama polling akışı stale state kullanmayacak şekilde düzeltildi
  - Build script akışı FullBuild/Fast build ayrımı ile sürüm tutarlılığına göre güncellendi
- Doğrulama:
  - Foreground testte `409 Conflict` oluşunca sürecin öldüğü tekrarlandı (kök neden teyit)
  - Hotfix sonrası `http://127.0.0.1:8765/health` yanıtı `ok` doğrulandı
  - `backend_stderr.log` içinde `Telegram Hub polling disabled` satırı görüldü
- Risk/Açık Konu:
  - Telegram Hub kapalıyken Telegram üzerinden onay/bildirim/kanal yayın özellikleri devre dışı kalır
  - Kullanıcı Telegram otomasyonunu tekrar açmak isterse token tarafında tek-poller garantisi gerekir
- Sonraki Adım:
  - Telegram Hub için kalıcı "single owner"/lock mekanizması eklenip `TELEGRAM_HUB_ENABLED=true` modunda güvenli çalıştırma
