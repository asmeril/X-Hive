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

export default function SettingsPanel() {
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

  const [xAccounts, setXAccounts] = useState<XAccount[]>([]);
  const [activeAccount, setActiveAccount] = useState<string>("");
  const [activeCookiePath, setActiveCookiePath] = useState<string>("");
  const [capabilityNote, setCapabilityNote] = useState<string>("");

  const [geminiMasked, setGeminiMasked] = useState<string>("");
  const [openaiMasked, setOpenaiMasked] = useState<string>("");
  const [telegramMasked, setTelegramMasked] = useState<string>("");

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
    } catch (requestError: unknown) {
      const message = requestError instanceof Error ? requestError.message : "Unknown error";
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

      await fetchSettings();
    } catch (saveError: unknown) {
      const message = saveError instanceof Error ? saveError.message : "Unknown error";
      setError(message);
    } finally {
      setSaving(false);
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
            <p style={{ margin: "0 0 10px", color: "#94a3b8", fontSize: "12px" }}>Mevcut Bot Token: {telegramMasked || "(yok)"}</p>
            <div style={{ display: "grid", gap: "10px", gridTemplateColumns: "1fr 1fr" }}>
              <input value={telegramBotToken} onChange={(event) => setTelegramBotToken(event.target.value)} placeholder="Yeni TELEGRAM_BOT_TOKEN (opsiyonel)" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramChatId} onChange={(event) => setTelegramChatId(event.target.value)} placeholder="TELEGRAM_CHAT_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramChannelId} onChange={(event) => setTelegramChannelId(event.target.value)} placeholder="TELEGRAM_CHANNEL_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
              <input value={telegramGroupId} onChange={(event) => setTelegramGroupId(event.target.value)} placeholder="TELEGRAM_GROUP_ID" style={{ padding: "10px", borderRadius: "8px", border: "1px solid #475569", backgroundColor: "#0f172a", color: "#e2e8f0" }} />
            </div>
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
