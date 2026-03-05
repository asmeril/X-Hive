import { useCallback, useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type XAccount = {
  name: string;
  username: string;
  cookie_path: string;
  enabled: boolean;
};

type SettingsResponse = {
  status: string;
  data?: {
    sniper_allow_fallback: boolean;
    ai: {
      gemini_key_masked: string;
      openai_key_masked: string;
      gemini_key_set: boolean;
      openai_key_set: boolean;
    };
    telegram: {
      bot_token_masked: string;
      chat_id: string;
      channel_id: string;
      group_id: string;
      api_id_set: boolean;
      api_hash_set: boolean;
      phone_masked: string;
    };
    x_accounts: XAccount[];
    active_x_account: string;
    active_cookie_path: string;
    capabilities: {
      multi_account_parallel_supported: boolean;
      multi_account_mode: string;
      note: string;
    };
  };
  message?: string;
};

type SaveResponse = {
  status: string;
  message?: string;
  requires_restart?: boolean;
  daemon_restarted?: boolean;
  active_cookie_path?: string;
};

type TelegramStatusResponse = {
  status: string;
  telegram?: {
    hub: {
      running: boolean;
      admin_chat: boolean;
      channel_configured: boolean;
      group_configured: boolean;
    };
    intel: {
      enabled_in_orchestrator: boolean;
      telethon_available: boolean;
      credentials_set: boolean;
      phone_set: boolean;
      session_file_exists: boolean;
      authorized: boolean;
      last_error?: string;
    };
  };
  message?: string;
};

type TelegramIntelAuthResponse = {
  status: string;
  step?: "already_authorized" | "code_sent" | "password_required" | "authorized" | "not_authorized";
  message?: string;
};

export default function SettingsPanel() {
  const getErrorMessage = (value: unknown, fallback = "Unknown error") => {
    if (value instanceof Error) return value.message;
    if (typeof value === "string") return value;
    if (value && typeof value === "object" && "message" in value) {
      const message = (value as { message?: unknown }).message;
      if (typeof message === "string") return message;
    }
    return fallback;
  };

  const [loading, setLoading] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [success, setSuccess] = useState<string>("");

  const [sniperFallback, setSniperFallback] = useState<boolean>(false);

  const [geminiKey, setGeminiKey] = useState<string>("");
  const [openaiKey, setOpenaiKey] = useState<string>("");

  const [telegramBotToken, setTelegramBotToken] = useState<string>("");
  const [telegramChatId, setTelegramChatId] = useState<string>("");
  const [telegramChannelId, setTelegramChannelId] = useState<string>("");
  const [telegramGroupId, setTelegramGroupId] = useState<string>("");
  const [telegramApiId, setTelegramApiId] = useState<string>("");
  const [telegramApiHash, setTelegramApiHash] = useState<string>("");
  const [telegramPhone, setTelegramPhone] = useState<string>("");

  const [xAccounts, setXAccounts] = useState<XAccount[]>([]);
  const [activeAccount, setActiveAccount] = useState<string>("");
  const [activeCookiePath, setActiveCookiePath] = useState<string>("");
  const [capabilityNote, setCapabilityNote] = useState<string>("");

  const [geminiMasked, setGeminiMasked] = useState<string>("");
  const [openaiMasked, setOpenaiMasked] = useState<string>("");
  const [telegramMasked, setTelegramMasked] = useState<string>("");
  const [telegramPhoneMasked, setTelegramPhoneMasked] = useState<string>("");

  const [telegramHubRunning, setTelegramHubRunning] = useState<boolean>(false);
  const [telegramHubAdminChat, setTelegramHubAdminChat] = useState<boolean>(false);
  const [telegramHubChannelConfigured, setTelegramHubChannelConfigured] = useState<boolean>(false);
  const [telegramHubGroupConfigured, setTelegramHubGroupConfigured] = useState<boolean>(false);

  const [telegramIntelTelethonAvailable, setTelegramIntelTelethonAvailable] = useState<boolean>(false);
  const [telegramIntelCredentialsSet, setTelegramIntelCredentialsSet] = useState<boolean>(false);
  const [telegramIntelPhoneSet, setTelegramIntelPhoneSet] = useState<boolean>(false);
  const [telegramIntelSessionExists, setTelegramIntelSessionExists] = useState<boolean>(false);
  const [telegramIntelAuthorized, setTelegramIntelAuthorized] = useState<boolean>(false);
  const [telegramIntelError, setTelegramIntelError] = useState<string>("");

  const [telegramAuthCode, setTelegramAuthCode] = useState<string>("");
  const [telegramAuthPassword, setTelegramAuthPassword] = useState<string>("");
  const [telegramAuthBusy, setTelegramAuthBusy] = useState<boolean>(false);
  const [telegramAuthStatus, setTelegramAuthStatus] = useState<string>("");
  const [telegramAuthNeedPassword, setTelegramAuthNeedPassword] = useState<boolean>(false);

  const fetchSettings = useCallback(async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const raw = await invoke<string>("call_worker_api", { method: "GET", endpoint: "/settings/ui" });
      const parsed: SettingsResponse = JSON.parse(raw);
      if (parsed.status !== "ok" || !parsed.data) {
        setError(parsed.message || "Ayarlar alınamadı");
        return;
      }

      setSniperFallback(Boolean(parsed.data.sniper_allow_fallback));
      setTelegramChatId(parsed.data.telegram.chat_id || "");
      setTelegramChannelId(parsed.data.telegram.channel_id || "");
      setTelegramGroupId(parsed.data.telegram.group_id || "");
      setXAccounts(parsed.data.x_accounts || []);
      setActiveAccount(parsed.data.active_x_account || "");
      setActiveCookiePath(parsed.data.active_cookie_path || "");
      setCapabilityNote(parsed.data.capabilities?.note || "");

      setGeminiMasked(parsed.data.ai.gemini_key_masked || "");
      setOpenaiMasked(parsed.data.ai.openai_key_masked || "");
      setTelegramMasked(parsed.data.telegram.bot_token_masked || "");
      setTelegramPhoneMasked(parsed.data.telegram.phone_masked || "");

      try {
        const telegramStatusRaw = await invoke<string>("call_worker_api", { method: "GET", endpoint: "/telegram/status" });
        const telegramStatusParsed: TelegramStatusResponse = JSON.parse(telegramStatusRaw);
        if (telegramStatusParsed.status === "ok" && telegramStatusParsed.telegram) {
          setTelegramHubRunning(Boolean(telegramStatusParsed.telegram.hub.running));
          setTelegramHubAdminChat(Boolean(telegramStatusParsed.telegram.hub.admin_chat));
          setTelegramHubChannelConfigured(Boolean(telegramStatusParsed.telegram.hub.channel_configured));
          setTelegramHubGroupConfigured(Boolean(telegramStatusParsed.telegram.hub.group_configured));

          setTelegramIntelTelethonAvailable(Boolean(telegramStatusParsed.telegram.intel.telethon_available));
          setTelegramIntelCredentialsSet(Boolean(telegramStatusParsed.telegram.intel.credentials_set));
          setTelegramIntelPhoneSet(Boolean(telegramStatusParsed.telegram.intel.phone_set));
          setTelegramIntelSessionExists(Boolean(telegramStatusParsed.telegram.intel.session_file_exists));
          setTelegramIntelAuthorized(Boolean(telegramStatusParsed.telegram.intel.authorized));
          setTelegramIntelError(telegramStatusParsed.telegram.intel.last_error || "");
        }
      } catch {
        // Eski worker sürümlerinde /telegram/status endpoint'i olmayabilir.
        // Bu durum Ayarlar ekranını kırmamalı.
        setTelegramHubRunning(false);
        setTelegramHubAdminChat(false);
        setTelegramHubChannelConfigured(false);
        setTelegramHubGroupConfigured(false);
        setTelegramIntelTelethonAvailable(false);
        setTelegramIntelCredentialsSet(false);
        setTelegramIntelPhoneSet(false);
        setTelegramIntelSessionExists(false);
        setTelegramIntelAuthorized(false);
        setTelegramIntelError("Telegram durum endpointi erişilemedi (worker eski sürüm olabilir)");
      }
    } catch (requestError: unknown) {
      const message = getErrorMessage(requestError);
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const addXAccount = () => {
    setXAccounts((prev) => [
      ...prev,
      {
        name: `Hesap-${prev.length + 1}`,
        username: "",
        cookie_path: "",
        enabled: true,
      },
    ]);
  };

  const updateXAccount = (index: number, field: keyof XAccount, value: string | boolean) => {
    setXAccounts((prev) =>
      prev.map((item, itemIndex) => {
        if (itemIndex !== index) return item;
        return {
          ...item,
          [field]: value,
        };
      })
    );
  };

  const removeXAccount = (index: number) => {
    setXAccounts((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
  };

  const saveSettings = async () => {
    setSaving(true);
    setError("");
    setSuccess("");

    try {
      const payload: Record<string, unknown> = {
        sniper_allow_fallback: sniperFallback,
        telegram_chat_id: telegramChatId,
        telegram_channel_id: telegramChannelId,
        telegram_group_id: telegramGroupId,
        x_accounts: xAccounts,
        active_x_account: activeAccount,
        apply_active_account_cookie: true,
      };

      if (geminiKey.trim()) payload.gemini_api_key = geminiKey.trim();
      if (openaiKey.trim()) payload.openai_api_key = openaiKey.trim();
      if (telegramBotToken.trim()) payload.telegram_bot_token = telegramBotToken.trim();
      if (telegramApiId.trim()) payload.telegram_api_id = telegramApiId.trim();
      if (telegramApiHash.trim()) payload.telegram_api_hash = telegramApiHash.trim();
      if (telegramPhone.trim()) payload.telegram_phone = telegramPhone.trim();

      const raw = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/settings/ui",
        body: JSON.stringify(payload),
      } as Record<string, unknown>);

      const parsed: SaveResponse = JSON.parse(raw);
      if (parsed.status !== "ok") {
        setError(parsed.message || "Ayarlar kaydedilemedi");
        return;
      }

      let message = parsed.message || "Ayarlar kaydedildi";
      if (parsed.requires_restart) {
        message += " | Bazı ayarlar için worker restart gerekir.";
      }
      if (parsed.daemon_restarted) {
        message += " | Aktif hesap değişimi için daemon yeniden başlatıldı.";
      }
      setSuccess(message);

      if (parsed.active_cookie_path) setActiveCookiePath(parsed.active_cookie_path);

      setGeminiKey("");
      setOpenaiKey("");
      setTelegramBotToken("");
      setTelegramApiId("");
      setTelegramApiHash("");
      setTelegramPhone("");

      await fetchSettings();
    } catch (saveError: unknown) {
      const message = getErrorMessage(saveError);
      setError(message);
    } finally {
      setSaving(false);
    }
  };

  const startTelegramIntelAuth = async () => {
    setTelegramAuthBusy(true);
    setTelegramAuthStatus("");
    setTelegramAuthNeedPassword(false);
    try {
      const payload: Record<string, string> = {};
      if (telegramApiId.trim()) payload.api_id = telegramApiId.trim();
      if (telegramApiHash.trim()) payload.api_hash = telegramApiHash.trim();
      if (telegramPhone.trim()) payload.phone = telegramPhone.trim();

      const raw = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/telegram/intel/auth/start",
        body: JSON.stringify(payload),
      } as Record<string, unknown>);

      const parsed: TelegramIntelAuthResponse = JSON.parse(raw);
      if (parsed.status !== "ok") {
        setTelegramAuthStatus(parsed.message || "Telegram auth başlatılamadı");
        return;
      }

      if (parsed.step === "already_authorized") {
        setTelegramAuthStatus("✅ Oturum zaten yetkili");
      } else if (parsed.step === "code_sent") {
        setTelegramAuthStatus("📩 Kod gönderildi. Lütfen kodu girin.");
      } else {
        setTelegramAuthStatus(parsed.message || "Durum alındı");
      }

      await fetchSettings();
    } catch (authError: unknown) {
      const message = getErrorMessage(authError);
      setTelegramAuthStatus(message);
    } finally {
      setTelegramAuthBusy(false);
    }
  };

  const verifyTelegramIntelCode = async () => {
    setTelegramAuthBusy(true);
    setTelegramAuthStatus("");
    try {
      const raw = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/telegram/intel/auth/verify-code",
        body: JSON.stringify({ code: telegramAuthCode.trim() }),
      } as Record<string, unknown>);

      const parsed: TelegramIntelAuthResponse = JSON.parse(raw);
      if (parsed.status !== "ok") {
        setTelegramAuthStatus(parsed.message || "Kod doğrulama başarısız");
        return;
      }

      if (parsed.step === "password_required") {
        setTelegramAuthNeedPassword(true);
        setTelegramAuthStatus("🔐 2FA parolası gerekli");
      } else if (parsed.step === "authorized") {
        setTelegramAuthNeedPassword(false);
        setTelegramAuthStatus("✅ Telegram Intel doğrulandı");
      } else {
        setTelegramAuthStatus(parsed.message || "Kod doğrulama tamamlandı");
      }

      await fetchSettings();
    } catch (authError: unknown) {
      const message = getErrorMessage(authError);
      setTelegramAuthStatus(message);
    } finally {
      setTelegramAuthBusy(false);
    }
  };

  const verifyTelegramIntelPassword = async () => {
    setTelegramAuthBusy(true);
    setTelegramAuthStatus("");
    try {
      const raw = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/telegram/intel/auth/verify-password",
        body: JSON.stringify({ password: telegramAuthPassword }),
      } as Record<string, unknown>);

      const parsed: TelegramIntelAuthResponse = JSON.parse(raw);
      if (parsed.status !== "ok") {
        setTelegramAuthStatus(parsed.message || "2FA doğrulama başarısız");
        return;
      }

      if (parsed.step === "authorized") {
        setTelegramAuthNeedPassword(false);
        setTelegramAuthStatus("✅ Telegram Intel 2FA doğrulandı");
      } else {
        setTelegramAuthStatus(parsed.message || "2FA doğrulama tamamlandı");
      }

      await fetchSettings();
    } catch (authError: unknown) {
      const message = getErrorMessage(authError);
      setTelegramAuthStatus(message);
    } finally {
      setTelegramAuthBusy(false);
    }
  };

  const hasAccountNameMismatch = useMemo(() => {
    if (!activeAccount) return false;
    return !xAccounts.some((item) => item.name === activeAccount);
  }, [activeAccount, xAccounts]);

  return (
    <div style={{ minHeight: "calc(100vh - 73px)", backgroundColor: "#0f172a", color: "#e2e8f0", padding: "24px" }}>
      <div style={{ maxWidth: "1320px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "28px", color: "#f8fafc" }}>⚙️ Ayarlar</h2>
            <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "14px" }}>
              API anahtarları, sniper davranışı ve tek aktif X hesap yönetimi
            </p>
          </div>
          <button
            onClick={fetchSettings}
            disabled={loading}
            style={{
              padding: "10px 16px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: loading ? "#1d4ed8" : "#2563eb",
              color: "white",
              cursor: loading ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {loading ? "⏳ Yenileniyor" : "🔄 Yenile"}
          </button>
        </div>

        {error && <div style={{ backgroundColor: "#7f1d1d", border: "1px solid #ef4444", color: "#fecaca", borderRadius: "8px", padding: "12px", marginBottom: "12px" }}>{error}</div>}
        {success && <div style={{ backgroundColor: "#14532d", border: "1px solid #22c55e", color: "#bbf7d0", borderRadius: "8px", padding: "12px", marginBottom: "12px" }}>{success}</div>}

        <div style={{ display: "grid", gap: "14px" }}>
          <section style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "10px", padding: "16px" }}>
            <h3 style={{ marginTop: 0 }}>🛡️ Güvenlik Davranışları</h3>
            <label style={{ display: "flex", gap: "10px", alignItems: "center" }}>
              <input type="checkbox" checked={sniperFallback} onChange={(event) => setSniperFallback(event.target.checked)} />
              <span>Sniper fallback aktif olsun (tweet_url yoksa son tweet dene)</span>
            </label>
          </section>

          <section style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "10px", padding: "16px" }}>
            <h3 style={{ marginTop: 0 }}>🔑 AI API Key Yönetimi</h3>
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: "12px" }}>Mevcut Gemini: {geminiMasked || "(yok)"} | OpenAI: {openaiMasked || "(yok)"}</p>
            <div style={{ display: "grid", gap: "10px" }}>
              <input value={geminiKey} onChange={(event) => setGeminiKey(event.target.value)} placeholder="Yeni GEMINI_API_KEY (değiştirmek için doldurun)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={openaiKey} onChange={(event) => setOpenaiKey(event.target.value)} placeholder="Yeni OPENAI_API_KEY (değiştirmek için doldurun)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
            </div>
          </section>

          <section style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "10px", padding: "16px" }}>
            <h3 style={{ marginTop: 0 }}>📲 Telegram Ayarları</h3>
            <p style={{ margin: "0 0 6px", color: "#94a3b8", fontSize: "12px" }}>Mevcut Bot Token: {telegramMasked || "(yok)"}</p>
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: "12px" }}>Mevcut Telefon: {telegramPhoneMasked || "(yok)"}</p>

            <div style={{ display: "grid", gap: "10px", gridTemplateColumns: "1fr 1fr", marginBottom: "10px" }}>
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #334155", borderRadius: "8px", padding: "10px" }}>
                <div style={{ fontWeight: 700, marginBottom: "6px" }}>🤖 Telegram Bot Modülü</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Çalışıyor: {telegramHubRunning ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Admin Chat: {telegramHubAdminChat ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Channel: {telegramHubChannelConfigured ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Group: {telegramHubGroupConfigured ? "✅" : "❌"}</div>
              </div>
              <div style={{ backgroundColor: "#0f172a", border: "1px solid #334155", borderRadius: "8px", padding: "10px" }}>
                <div style={{ fontWeight: 700, marginBottom: "6px" }}>🔎 Telegram Intel Modülü</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Telethon: {telegramIntelTelethonAvailable ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Kimlik bilgileri: {telegramIntelCredentialsSet ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Telefon: {telegramIntelPhoneSet ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Session dosyası: {telegramIntelSessionExists ? "✅" : "❌"}</div>
                <div style={{ fontSize: "12px", color: "#cbd5e1" }}>Yetkili oturum: {telegramIntelAuthorized ? "✅" : "❌"}</div>
                {telegramIntelError && <div style={{ fontSize: "12px", color: "#fca5a5", marginTop: "4px" }}>Hata: {telegramIntelError}</div>}
              </div>
            </div>

            <div style={{ display: "grid", gap: "10px", gridTemplateColumns: "1fr 1fr" }}>
              <input value={telegramBotToken} onChange={(event) => setTelegramBotToken(event.target.value)} placeholder="Yeni TELEGRAM_BOT_TOKEN (opsiyonel)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramChatId} onChange={(event) => setTelegramChatId(event.target.value)} placeholder="TELEGRAM_CHAT_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramChannelId} onChange={(event) => setTelegramChannelId(event.target.value)} placeholder="TELEGRAM_CHANNEL_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramGroupId} onChange={(event) => setTelegramGroupId(event.target.value)} placeholder="TELEGRAM_GROUP_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramApiId} onChange={(event) => setTelegramApiId(event.target.value)} placeholder="TELEGRAM_API_ID (Intel)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramApiHash} onChange={(event) => setTelegramApiHash(event.target.value)} placeholder="TELEGRAM_API_HASH (Intel)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramPhone} onChange={(event) => setTelegramPhone(event.target.value)} placeholder="TELEGRAM_PHONE (Intel)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
            </div>
            <div style={{ marginTop: "10px", display: "grid", gap: "8px", gridTemplateColumns: "1fr auto" }}>
              <input value={telegramAuthCode} onChange={(event) => setTelegramAuthCode(event.target.value)} placeholder="Telegram doğrulama kodu" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <button onClick={verifyTelegramIntelCode} disabled={telegramAuthBusy || !telegramAuthCode.trim()} style={{ padding: "10px 14px", borderRadius: "8px", border: "none", backgroundColor: telegramAuthBusy ? "#475569" : "#2563eb", color: "white", cursor: telegramAuthBusy ? "not-allowed" : "pointer", fontWeight: 600 }}>
                Kodu Doğrula
              </button>
            </div>
            {telegramAuthNeedPassword && (
              <div style={{ marginTop: "8px", display: "grid", gap: "8px", gridTemplateColumns: "1fr auto" }}>
                <input value={telegramAuthPassword} onChange={(event) => setTelegramAuthPassword(event.target.value)} type="password" placeholder="Telegram 2FA parolası" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
                <button onClick={verifyTelegramIntelPassword} disabled={telegramAuthBusy || !telegramAuthPassword} style={{ padding: "10px 14px", borderRadius: "8px", border: "none", backgroundColor: telegramAuthBusy ? "#475569" : "#7c3aed", color: "white", cursor: telegramAuthBusy ? "not-allowed" : "pointer", fontWeight: 600 }}>
                  2FA Doğrula
                </button>
              </div>
            )}
            <div style={{ marginTop: "8px", display: "flex", gap: "8px", alignItems: "center" }}>
              <button onClick={startTelegramIntelAuth} disabled={telegramAuthBusy} style={{ padding: "10px 14px", borderRadius: "8px", border: "none", backgroundColor: telegramAuthBusy ? "#475569" : "#0ea5e9", color: "white", cursor: telegramAuthBusy ? "not-allowed" : "pointer", fontWeight: 600 }}>
                {telegramAuthBusy ? "⏳ İşleniyor" : "🔐 Telegram Intel Giriş Başlat"}
              </button>
              {telegramAuthStatus && <span style={{ color: "#cbd5e1", fontSize: "12px" }}>{telegramAuthStatus}</span>}
            </div>
            <p style={{ margin: "8px 0 0", color: "#94a3b8", fontSize: "12px" }}>Not: Intel modülünde ilk doğrulama bir kez yapılır, session dosyası ile devam eder.</p>
          </section>

          <section style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "10px", padding: "16px" }}>
            <h3 style={{ marginTop: 0 }}>🐦 X Hesap Profilleri (Tek Aktif)</h3>
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: "12px" }}>{capabilityNote}</p>
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: "12px" }}>Aktif cookie path: {activeCookiePath || "(yok)"}</p>

            <div style={{ marginBottom: "10px", display: "flex", gap: "10px" }}>
              <input
                value={activeAccount}
                onChange={(event) => setActiveAccount(event.target.value)}
                placeholder="ACTIVE_X_ACCOUNT adı"
                style={{ flex: 1, padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }}
              />
              <button onClick={addXAccount} style={{ padding: "10px 14px", borderRadius: "8px", border: "none", backgroundColor: "#334155", color: "white", cursor: "pointer" }}>
                + Hesap Ekle
              </button>
            </div>

            {hasAccountNameMismatch && (
              <div style={{ color: "#fbbf24", fontSize: "12px", marginBottom: "8px" }}>
                Aktif hesap adı listedeki bir profil ile eşleşmiyor.
              </div>
            )}

            <div style={{ display: "grid", gap: "8px" }}>
              {xAccounts.map((account, index) => (
                <div key={`${account.name}-${index}`} style={{ border: "1px solid #334155", borderRadius: "8px", padding: "10px", display: "grid", gap: "8px", gridTemplateColumns: "1fr 1fr 2fr auto auto" }}>
                  <input value={account.name} onChange={(event) => updateXAccount(index, "name", event.target.value)} placeholder="Profil Adı" style={{ padding: "8px", borderRadius: "6px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
                  <input value={account.username} onChange={(event) => updateXAccount(index, "username", event.target.value)} placeholder="Kullanıcı adı" style={{ padding: "8px", borderRadius: "6px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
                  <input value={account.cookie_path} onChange={(event) => updateXAccount(index, "cookie_path", event.target.value)} placeholder="Cookie dosya yolu" style={{ padding: "8px", borderRadius: "6px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
                  <label style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "12px" }}>
                    <input type="checkbox" checked={account.enabled} onChange={(event) => updateXAccount(index, "enabled", event.target.checked)} />
                    Aktif
                  </label>
                  <button onClick={() => removeXAccount(index)} style={{ padding: "8px 10px", borderRadius: "6px", border: "none", backgroundColor: "#7f1d1d", color: "white", cursor: "pointer" }}>Sil</button>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div style={{ marginTop: "16px", display: "flex", justifyContent: "flex-end" }}>
          <button
            onClick={saveSettings}
            disabled={saving}
            style={{
              padding: "12px 18px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: saving ? "#2563eb" : "#3b82f6",
              color: "white",
              fontWeight: 700,
              cursor: saving ? "not-allowed" : "pointer",
            }}
          >
            {saving ? "⏳ Kaydediliyor" : "💾 Ayarları Kaydet"}
          </button>
        </div>
      </div>
    </div>
  );
}
