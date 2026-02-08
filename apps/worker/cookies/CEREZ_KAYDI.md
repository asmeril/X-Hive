# Çerez Kaydı - Adım Adım Rehber

## 1. EditThisCookie'yi Kur

### Chrome/Chromium:
1. https://chrome.google.com/webstore/detail/editthiscookie/fngmhnnpilhplaeedifhccceomclgfbg
2. "Chrome'a Ekle" butonuna tıkla

### Firefox:
1. https://addons.mozilla.org/en-US/firefox/addon/editthistcookie/
2. "Firefox'a Ekle" butonuna tıkla

---

## 2. Çerezleri Dışa Aktar

### Reddit için:
```
1. https://reddit.com adresine git
2. Giriş yap (sağ üst köşeye bakarak kontrol et)
3. EditThisCookie ikonu (sağ üst)
4. "Export" tuşuna tıkla
5. JSON array kopyala (Ctrl+A, Ctrl+C)
6. apps/worker/cookies/reddit.json dosyasını aç
7. Kopyaladığını yapıştır (Ctrl+V)
8. Kaydet
```

### Medium için:
```
1. https://medium.com adresine git
2. Giriş yap
3. EditThisCookie ikonu
4. "Export" tuşu
5. JSON kopyala
6. apps/worker/cookies/medium.json dosyasını aç
7. Yapıştır
8. Kaydet
```

### Perplexity için:
```
1. https://www.perplexity.ai adresine git
2. Giriş yap
3. EditThisCookie ikonu
4. "Export" tuşu
5. JSON kopyala
6. apps/worker/cookies/perplexity.json dosyasını aç
7. Yapıştır
8. Kaydet
```

### Twitter için:
```
1. https://twitter.com adresine git
2. Giriş yap
3. EditThisCookie ikonu
4. "Export" tuşu
5. JSON kopyala
6. apps/worker/cookies/twitter.json dosyasını aç
7. Yapıştır
8. Kaydet
```

### Substack için:
```
1. https://substack.com adresine git
2. Giriş yap
3. EditThisCookie ikonu
4. "Export" tuşu
5. JSON kopyala
6. apps/worker/cookies/substack.json dosyasını aç
7. Yapıştır
8. Kaydet
```

### Arxiv için:
```
1. https://arxiv.org adresine git
2. (İsteğe bağlı giriş - Arxiv çoğunlukla kimliksiz kullanılır)
3. Eğer giriş yaptıysan: EditThisCookie ikonu
4. "Export" tuşu
5. JSON kopyala
6. apps/worker/cookies/arxiv.json dosyasını aç
7. Yapıştır
8. Kaydet
```

---

## 3. JSON Formatı Kontrol Et

Yapıştırılan metin şu şekilde görünmeli:

```json
[
    {
        "domain": ".reddit.com",
        "name": "reddit_session",
        "value": "YOUR_VALUE_HERE",
        ...
    },
    {
        "domain": ".reddit.com",
        "name": "token_v2",
        "value": "YOUR_VALUE_HERE",
        ...
    }
]
```

---

## 4. Çerezleri Test Et

Terminalden şu komutu çalıştır:

```bash
cd c:\XHive\X-Hive\apps\worker
python -c "from intel.cookie_manager import get_cookie_manager; cm = get_cookie_manager(); print('Medium çerezleri:', cm.get_headers_for_site('medium'))"
```

Eğer `Cookie:` başlığı görürsen, başarılı! ✅

---

## 5. Kazıyıcıları Çalıştır

Artık kazıyıcılar çerezleri otomatik olarak kullanacak:

```bash
python test_phase1_complete.py
```

Medium ve Perplexity şimdi çalışmalı! 🎉

---

**Not:** Çerezler .gitignore tarafından korunuyor - GitHub'a gönderilmeyecek! ✅
