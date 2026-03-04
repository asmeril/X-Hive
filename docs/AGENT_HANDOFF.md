# AGENT HANDOFF STANDARDI

Bu dosya, XHive üzerinde çalışan agent'ların yaptığı işlemleri **kalıcı**, **gerekçeli** ve **devralınabilir** şekilde saklamak için standarttır.

## Amaç
- Yapılan değişiklikleri sadece "ne" değil, **"neden"** ve **"etkisi"** ile kaydetmek
- Sonraki agent'ın hızlıca bağlam almasını sağlamak
- Tekrarlı hata/teşhis döngülerini azaltmak

## Zorunlu Kayıt Alanları
Her anlamlı işlemden sonra `docs/AGENT_LOG.md` içine aşağıdaki formatta kayıt düşülür:

1. Tarih/Saat
2. Kapsam (dosya/modül/servis)
3. Problem veya ihtiyaç
4. Kök neden (varsa)
5. Yapılan değişiklik
6. Doğrulama (log/test/endpoint)
7. Risk veya açık kalanlar
8. Sonraki adım önerisi

## Kayıt Şablonu
Aşağıdaki şablon birebir kullanılmalıdır:

```markdown
## YYYY-MM-DD HH:mm - Kısa Başlık
- Kapsam: `path/or/module`
- İhtiyaç: ...
- Kök Neden: ...
- Yapılan: ...
- Doğrulama: ...
- Risk/Açık Konu: ...
- Sonraki Adım: ...
```

## Kullanım Kuralları
- "Düzeltildi" gibi tek satır geçiş yapılmaz; sebep ve etki mutlaka yazılır.
- Sadece ilgili değişiklik kaydedilir; alakasız konular eklenmez.
- Üretim etkisi olan değişikliklerde doğrulama adımı zorunludur.
- Build/installer değişiklikleri için ilgili script/dosya yolları mutlaka belirtilir.

## Not
Bu standart, oturum belleğine bağlı kalmadan kalıcı iz bırakmak içindir. Yeni agent işe buradan başlar.
