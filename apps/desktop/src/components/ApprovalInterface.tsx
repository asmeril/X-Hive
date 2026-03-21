import React, { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { ApprovalFilters, ApprovalItem, ApprovalResponse, ApprovalSummary, PublishStateValue } from "../types/daemon";

const VIRAL_COLORS: Record<string, string> = {
  high: "#22c55e",   // 8-10
  medium: "#f59e0b", // 5-7
  low: "#ef4444",    // 1-4
};

function getViralColor(score: number): string {
  if (score >= 8) return VIRAL_COLORS.high;
  if (score >= 5) return VIRAL_COLORS.medium;
  return VIRAL_COLORS.low;
}

function getViralLabel(score: number): string {
  if (score >= 9) return "🔥 Viral";
  if (score >= 7) return "🚀 Yüksek";
  if (score >= 5) return "📈 Orta";
  return "📉 Düşük";
}

const ApprovalInterface: React.FC = () => {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [summary, setSummary] = useState<ApprovalSummary>({
    pending: 0,
    approved: 0,
    publishing: 0,
    failed: 0,
    processed: 0,
    rejected: 0,
  });
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [langTab, setLangTab] = useState<Record<string, "tr" | "en">>({});
  const [activeTab, setActiveTab] = useState<"pending" | "approved" | "publishing" | "failed" | "processed">("pending");
  const [filters, setFilters] = useState<ApprovalFilters>({
    category: "all",
    source: "all",
    searchQuery: "",
  });

  const fetchItems = useCallback(async (showSpinner: boolean = true): Promise<number> => {
    try {
      if (showSpinner) setLoading(true);
      setError(null);
      const response = await invoke<string>("call_worker_api", {
        method: "GET",
        endpoint: "/approval/items",
      });
      const parsed: ApprovalResponse = JSON.parse(response);
      if (parsed.status === "success" && parsed.data?.items) {
        setItems(parsed.data.items);
        setSummary(parsed.data.summary || {
          pending: 0,
          approved: 0,
          publishing: 0,
          failed: 0,
          processed: 0,
          rejected: 0,
        });
        return parsed.data.items.length;
      } else {
        setItems([]);
        setSummary({ pending: 0, approved: 0, publishing: 0, failed: 0, processed: 0, rejected: 0 });
        return 0;
      }
    } catch (e: any) {
      setError(e.message || "Bağlantı hatası");
      return 0;
    } finally {
      if (showSpinner) setLoading(false);
    }
  }, []);

  useEffect(() => { fetchItems(true); }, [fetchItems]);

  const handleScan = async () => {
    setScanning(true);
    setError(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/system/force-intel",
      });

      // Poll until data arrives (every 15s, max 5 min) — stale state kullanılmaz.
      for (let attempts = 0; attempts < 20; attempts++) {
        await new Promise((resolve) => setTimeout(resolve, 15000));
        const count = await fetchItems(false);
        if (count > 0) break;
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setScanning(false);
    }
  };

  const handleApprove = async (itemId: string) => {
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/approve/${itemId}`,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        await fetchItems(false);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleReject = async (itemId: string) => {
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/reject/${itemId}`,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        await fetchItems(false);
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handlePostThread = async (itemId: string, lang: "tr" | "en") => {
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/post-thread/${itemId}?lang=${lang}`,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        await fetchItems(false);
        setError(null);
      } else {
        setError(parsed.message || "Thread yayınlanamadı");
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleRetryThread = async (itemId: string, lang?: "tr" | "en") => {
    try {
      const endpoint = lang
        ? `/approval/retry-thread/${itemId}?lang=${lang}`
        : `/approval/retry-thread/${itemId}`;
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        await fetchItems(false);
        setError(null);
      } else {
        setError(parsed.message || "Retry başlatılamadı");
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleSniperReply = async (itemId: string) => {
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/sniper-reply/${itemId}`,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        alert(`🎯 Sniper Reply başlatıldı!\nHedefler: ${parsed.targets?.join(", ")}`);
      } else {
        setError(parsed.message || "Sniper reply başarısız");
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleApproveAll = async () => {
    try {
      const pendingVisible = filteredItems.filter((item) => item.status === "pending");
      for (const item of pendingVisible) {
        const response = await invoke<string>("call_worker_api", {
          method: "POST",
          endpoint: `/approval/approve/${item.tweet_id}`,
        });
        const parsed = JSON.parse(response);
        if (parsed.status !== "success") {
          throw new Error(parsed.message || `${item.tweet_id} onaylanamadı`);
        }
      }
      await fetchItems(false);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handleRetryVisibleFailed = async () => {
    try {
      const failedItems = filteredItems.filter((item) => item.publish_state === "failed");
      for (const item of failedItems) {
        await handleRetryThread(item.tweet_id);
      }
      await fetchItems(false);
    } catch (e: any) {
      setError(e.message);
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  const getLang = (id: string): "tr" | "en" => langTab[id] || "tr";
  const setLang = (id: string, lang: "tr" | "en") => {
    setLangTab(prev => ({ ...prev, [id]: lang }));
  };

  const tabItems = items.filter((item) => {
    const publishState = (item.publish_state || "idle") as PublishStateValue;
    if (activeTab === "pending") return item.status === "pending";
    if (activeTab === "approved") return (item.status === "approved" || item.status === "edited") && publishState !== "publishing" && publishState !== "failed";
    if (activeTab === "publishing") return publishState === "publishing";
    if (activeTab === "failed") return publishState === "failed";
    if (activeTab === "processed") return item.status === "processed" || publishState === "completed";
    return false;
  });

  const sourceOptions = Array.from(new Set(items.map((item) => item.content_item?.source_name).filter(Boolean))).sort();
  const categoryOptions = Array.from(new Set(items.map((item) => item.content_item?.category).filter(Boolean))).sort();

  const filteredItems = tabItems.filter((item) => {
    const search = filters.searchQuery.trim().toLowerCase();
    const matchesSearch = !search || [
      item.generated_tweet,
      item.content_item?.title,
      item.content_item?.source_name,
      ...(item.keywords || []),
      ...(item.mentions || []),
    ].filter(Boolean).some((value) => String(value).toLowerCase().includes(search));

    const matchesSource = filters.source === "all" || item.content_item?.source_name === filters.source;
    const matchesCategory = filters.category === "all" || item.content_item?.category === filters.category;
    return matchesSearch && matchesSource && matchesCategory;
  });

  const tabButton = (
    key: "pending" | "approved" | "publishing" | "failed" | "processed",
    label: string,
    count: number,
  ) => (
    <button
      key={key}
      onClick={() => setActiveTab(key)}
      style={{
        backgroundColor: activeTab === key ? "#2563eb" : "#1e293b",
        color: "white",
        padding: "8px 14px",
        borderRadius: "999px",
        border: activeTab === key ? "1px solid #3b82f6" : "1px solid #334155",
        cursor: "pointer",
        fontSize: "13px",
        fontWeight: 600,
      }}
    >
      {label} ({count})
    </button>
  );

  return (
    <div style={{
      minHeight: "calc(100vh - 73px)",
      backgroundColor: "#0f172a",
      color: "white",
      padding: "24px",
      overflowY: "auto"
    }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
          <div>
            <h1 style={{ fontSize: "28px", fontWeight: "bold", margin: 0 }}>
              🧵 Viral İçerik Onayı
            </h1>
            <p style={{ color: "#9ca3af", margin: "4px 0 0", fontSize: "14px" }}>
              AI, en viral potansiyelli içerikleri seçti ve TR + EN thread'ler hazırladı
            </p>
          </div>
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              onClick={handleScan}
              disabled={scanning}
              style={{
                backgroundColor: scanning ? "#4b5563" : "#6366f1",
                color: "white",
                padding: "10px 20px",
                borderRadius: "8px",
                border: "none",
                cursor: scanning ? "not-allowed" : "pointer",
                fontSize: "14px",
                fontWeight: 600,
              }}
            >
              {scanning ? "⏳ Taranıyor..." : "🔍 Yeni Tarama"}
            </button>
            {items.length > 0 && (
              <button
                onClick={handleApproveAll}
                style={{
                  backgroundColor: "#10b981",
                  color: "white",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "14px",
                  fontWeight: 600,
                }}
              >
                ✅ Hepsini Onayla ({items.length})
              </button>
            )}
          </div>
        </div>

        {/* Stats Bar */}
        {items.length > 0 && (
          <div style={{
            display: "flex", gap: "16px", marginBottom: "20px",
            backgroundColor: "#1e293b", padding: "12px 20px", borderRadius: "10px",
          }}>
            <span>📦 <strong>{items.length}</strong> thread</span>
            <span>🔥 Ort. skor: <strong>
              {(items.reduce((a, b) => a + (b.viral_score || 0), 0) / items.length).toFixed(1)}
            </strong>/10</span>
            <span>🏆 En yüksek: <strong>
              {Math.max(...items.map(i => i.viral_score || 0))}
            </strong>/10</span>
          </div>
        )}

        {/* Tabs */}
        <div style={{ display: "flex", gap: "10px", marginBottom: "20px", flexWrap: "wrap" }}>
          {tabButton("pending", "Bekleyen", summary.pending)}
          {tabButton("approved", "Onaylanan", summary.approved)}
          {tabButton("publishing", "Yayınlanan İş", summary.publishing)}
          {tabButton("failed", "Hatalı", summary.failed)}
          {tabButton("processed", "Tamamlanan", summary.processed)}
        </div>

        <div style={{
          display: "grid",
          gridTemplateColumns: "minmax(220px, 1.6fr) minmax(150px, 1fr) minmax(150px, 1fr) auto",
          gap: "12px",
          marginBottom: "20px",
          alignItems: "center",
        }}>
          <input
            value={filters.searchQuery}
            onChange={(e) => setFilters((prev) => ({ ...prev, searchQuery: e.target.value }))}
            placeholder="Başlık, tweet, mention, keyword ara"
            style={{
              backgroundColor: "#1e293b",
              color: "white",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "14px",
            }}
          />
          <select
            value={filters.source}
            onChange={(e) => setFilters((prev) => ({ ...prev, source: e.target.value }))}
            style={{
              backgroundColor: "#1e293b",
              color: "white",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "14px",
            }}
          >
            <option value="all">Tüm kaynaklar</option>
            {sourceOptions.map((source) => (
              <option key={source} value={source}>{source}</option>
            ))}
          </select>
          <select
            value={filters.category}
            onChange={(e) => setFilters((prev) => ({ ...prev, category: e.target.value as ApprovalFilters["category"] }))}
            style={{
              backgroundColor: "#1e293b",
              color: "white",
              border: "1px solid #334155",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "14px",
            }}
          >
            <option value="all">Tüm kategoriler</option>
            {categoryOptions.map((category) => (
              <option key={String(category)} value={String(category)}>{String(category)}</option>
            ))}
          </select>
          <button
            onClick={() => setFilters({ category: "all", source: "all", searchQuery: "" })}
            style={{
              backgroundColor: "#334155",
              color: "white",
              border: "1px solid #475569",
              borderRadius: "8px",
              padding: "10px 12px",
              fontSize: "13px",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Filtreyi Temizle
          </button>
        </div>

        {activeTab === "pending" && filteredItems.length > 0 && (
          <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
            <button
              onClick={handleApproveAll}
              style={{
                backgroundColor: "#16a34a",
                color: "white",
                padding: "10px 18px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 700,
              }}
            >
              ✅ Görünenleri Onayla ({filteredItems.length})
            </button>
          </div>
        )}

        {activeTab === "failed" && filteredItems.length > 0 && (
          <div style={{ display: "flex", gap: "10px", marginBottom: "16px" }}>
            <button
              onClick={handleRetryVisibleFailed}
              style={{
                backgroundColor: "#ea580c",
                color: "white",
                padding: "10px 18px",
                borderRadius: "8px",
                border: "none",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 700,
              }}
            >
              🔁 Görünen Failed Item'ları Retry Et ({filteredItems.length})
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ textAlign: "center", padding: "60px" }}>
            <div style={{ fontSize: "48px" }}>⏳</div>
            <div style={{ marginTop: "16px", color: "#9ca3af" }}>İçerikler yükleniyor...</div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div style={{
            backgroundColor: "#7f1d1d", padding: "12px 16px",
            borderRadius: "8px", marginBottom: "16px", fontSize: "14px"
          }}>
            ❌ {error}
          </div>
        )}

        {/* Empty */}
        {!loading && filteredItems.length === 0 && !error && (
          <div style={{
            textAlign: "center", padding: "60px",
            backgroundColor: "#1e293b", borderRadius: "12px"
          }}>
            <div style={{ fontSize: "48px" }}>📭</div>
            <div style={{ marginTop: "16px", fontSize: "18px", color: "#d1d5db" }}>
              Bu sekmede içerik yok
            </div>
            <div style={{ marginTop: "8px", color: "#6b7280", fontSize: "14px" }}>
              "Yeni Tarama" ile viral içerikleri keşfedin
            </div>
          </div>
        )}

        {/* Thread Cards */}
        {filteredItems.length > 0 && (
          <div style={{ display: "grid", gap: "16px" }}>
            {filteredItems.map((item: ApprovalItem) => {
              const isExpanded = expandedId === item.tweet_id;
              const currentLang = getLang(item.tweet_id);
              const thread = currentLang === "tr" ? (item.tr_thread || []) : (item.en_thread || []);
              const viralColor = getViralColor(item.viral_score || 0);
              const hasThread = thread.length > 0;
              const trPublished = Boolean(item.published_languages?.tr);
              const enPublished = Boolean(item.published_languages?.en);
              const publishState = item.publish_state || "idle";

              return (
                <div key={item.tweet_id} style={{
                  backgroundColor: "#1e293b",
                  borderRadius: "12px",
                  border: `1px solid ${viralColor}33`,
                  overflow: "hidden",
                }}>
                  {/* Card Header */}
                  <div
                    onClick={() => toggleExpand(item.tweet_id)}
                    style={{
                      padding: "16px 20px",
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "flex-start",
                      gap: "16px",
                      transition: "background-color 0.2s",
                    }}
                    onMouseEnter={e => (e.currentTarget.style.backgroundColor = "#263348")}
                    onMouseLeave={e => (e.currentTarget.style.backgroundColor = "transparent")}
                  >
                    {/* Viral Score Badge */}
                    <div style={{
                      minWidth: "56px", textAlign: "center",
                      padding: "8px 4px", borderRadius: "10px",
                      backgroundColor: `${viralColor}22`,
                      border: `1px solid ${viralColor}44`,
                    }}>
                      <div style={{ fontSize: "22px", fontWeight: "bold", color: viralColor }}>
                        {item.viral_score || "?"}
                      </div>
                      <div style={{ fontSize: "10px", color: viralColor, marginTop: "2px" }}>
                        {getViralLabel(item.viral_score || 0)}
                      </div>
                    </div>

                    {/* Content Preview */}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: "15px", fontWeight: 600,
                        marginBottom: "6px", lineHeight: 1.4,
                        whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis",
                      }}>
                        {item.content_item?.title || item.generated_tweet?.substring(0, 80)}
                      </div>
                      <div style={{
                        fontSize: "13px", color: "#9ca3af", lineHeight: 1.4,
                        display: "-webkit-box", WebkitLineClamp: 2,
                        WebkitBoxOrient: "vertical", overflow: "hidden",
                      }}>
                        {item.generated_tweet}
                      </div>
                      <div style={{
                        display: "flex", gap: "12px", marginTop: "8px",
                        fontSize: "12px", color: "#6b7280", flexWrap: "wrap",
                      }}>
                        <span>📰 {item.content_item?.source_name}</span>
                        {item.content_item?.category && <span>🏷️ {item.content_item.category}</span>}
                        <span>🧵 {(item.tr_thread?.length || 0)} TR + {(item.en_thread?.length || 0)} EN</span>
                        {item.mentions?.length > 0 && (
                          <span style={{ color: "#60a5fa" }}>🏷️ {item.mentions.join(" ")}</span>
                        )}
                        {item.image_url && <span style={{ color: "#34d399" }}>🖼️ Görsel</span>}
                        {item.sniper_targets?.length > 0 && (
                          <span style={{ color: "#f59e0b" }}>🎯 {item.sniper_targets.length} hedef</span>
                        )}
                        <span style={{ color: trPublished ? "#22c55e" : "#6b7280" }}>
                          🇹🇷 {trPublished ? "yayında" : "yayınlanmadı"}
                        </span>
                        <span style={{ color: enPublished ? "#22c55e" : "#6b7280" }}>
                          🇬🇧 {enPublished ? "yayında" : "yayınlanmadı"}
                        </span>
                        <span style={{ color: publishState === "failed" ? "#f87171" : publishState === "publishing" ? "#fbbf24" : "#94a3b8" }}>
                          ⚙️ {publishState}
                        </span>
                        <span>🕐 {new Date(item.created_at).toLocaleTimeString("tr-TR")}</span>
                      </div>
                    </div>

                    {/* Expand Arrow */}
                    <div style={{ color: "#6b7280", fontSize: "18px", marginTop: "4px" }}>
                      {isExpanded ? "▲" : "▼"}
                    </div>
                  </div>

                  {/* Expanded: Thread Detail */}
                  {isExpanded && (
                    <div style={{
                      borderTop: "1px solid #374151",
                      padding: "16px 20px",
                      backgroundColor: "#0f172a",
                    }}>

                      {/* ── Visibility Info Panel ── */}
                      {(item.mentions?.length > 0 || item.keywords?.length > 0 || item.image_url || item.sniper_targets?.length > 0) && (
                        <div style={{
                          display: "grid", gridTemplateColumns: "1fr 1fr",
                          gap: "10px", marginBottom: "16px",
                          backgroundColor: "#1e293b", borderRadius: "10px",
                          padding: "12px 16px", border: "1px solid #374151",
                        }}>
                          {/* Mentions */}
                          {item.mentions?.length > 0 && (
                            <div>
                              <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "4px" }}>
                                🏷️ AKİLLI ETİKETLEME
                              </div>
                              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                                {item.mentions.map((m, i) => (
                                  <span key={i} style={{
                                    backgroundColor: "#1d4ed833", color: "#60a5fa",
                                    padding: "2px 8px", borderRadius: "4px", fontSize: "12px",
                                    border: "1px solid #1d4ed855",
                                  }}>{m}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {/* Keywords */}
                          {item.keywords?.length > 0 && (
                            <div>
                              <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "4px" }}>
                                🔑 TREND ANAHTAR KELİMELER
                              </div>
                              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                                {item.keywords.map((k, i) => (
                                  <span key={i} style={{
                                    backgroundColor: "#065f4633", color: "#34d399",
                                    padding: "2px 8px", borderRadius: "4px", fontSize: "12px",
                                    border: "1px solid #065f4655",
                                  }}>{k}</span>
                                ))}
                              </div>
                            </div>
                          )}
                          {/* Image */}
                          {item.image_url && (
                            <div>
                              <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "4px" }}>
                                🖼️ GÖRSEL KANCASI
                              </div>
                              <img
                                src={item.image_url}
                                alt="OG"
                                style={{
                                  maxWidth: "200px", maxHeight: "100px",
                                  borderRadius: "6px", border: "1px solid #374151",
                                  objectFit: "cover",
                                }}
                                onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                              />
                            </div>
                          )}
                          {/* Sniper Targets */}
                          {item.sniper_targets?.length > 0 && (
                            <div>
                              <div style={{ fontSize: "11px", color: "#6b7280", marginBottom: "4px" }}>
                                🎯 SNİPER REPLY HEDEFLERİ
                              </div>
                              <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                                {item.sniper_targets.map((t, i) => (
                                  <span key={i} style={{
                                    backgroundColor: "#78350f33", color: "#fbbf24",
                                    padding: "2px 8px", borderRadius: "4px", fontSize: "12px",
                                    border: "1px solid #78350f55",
                                  }}>
                                    {t.handle} <span style={{ color: "#9ca3af" }}>({t.name})</span>
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                      {/* Language Tabs */}
                      {hasThread && (
                        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
                          <button
                            onClick={() => setLang(item.tweet_id, "tr")}
                            style={{
                              padding: "6px 16px", borderRadius: "6px", border: "none",
                              backgroundColor: currentLang === "tr" ? "#3b82f6" : "#374151",
                              color: "white", fontSize: "13px", fontWeight: 600, cursor: "pointer",
                            }}
                          >
                            🇹🇷 Türkçe Thread
                          </button>
                          <button
                            onClick={() => setLang(item.tweet_id, "en")}
                            style={{
                              padding: "6px 16px", borderRadius: "6px", border: "none",
                              backgroundColor: currentLang === "en" ? "#3b82f6" : "#374151",
                              color: "white", fontSize: "13px", fontWeight: 600, cursor: "pointer",
                            }}
                          >
                            🇬🇧 English Thread
                          </button>
                          {item.content_item?.url && (
                            <a
                              href={item.content_item.url}
                              target="_blank"
                              rel="noreferrer"
                              style={{
                                padding: "6px 16px", borderRadius: "6px",
                                backgroundColor: "#374151", color: "#60a5fa",
                                fontSize: "13px", textDecoration: "none",
                                display: "flex", alignItems: "center",
                              }}
                            >
                              🔗 Kaynak
                            </a>
                          )}
                        </div>
                      )}

                      {item.last_error && (
                        <div style={{
                          backgroundColor: "#7f1d1d",
                          color: "#fecaca",
                          padding: "10px 12px",
                          borderRadius: "8px",
                          marginBottom: "16px",
                          fontSize: "13px",
                        }}>
                          Son hata: {item.last_error}
                        </div>
                      )}

                      {/* Thread Tweets */}
                      {hasThread ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                          {thread.map((tweet, idx) => (
                            <div key={idx} style={{
                              backgroundColor: "#1e293b",
                              padding: "14px 16px",
                              borderRadius: "10px",
                              border: "1px solid #374151",
                              borderLeft: idx === 0 ? `3px solid ${viralColor}` : "1px solid #374151",
                              fontSize: "14px",
                              lineHeight: 1.6,
                              position: "relative",
                            }}>
                              <span style={{
                                position: "absolute", top: "8px", right: "10px",
                                fontSize: "11px", color: "#4b5563",
                              }}>
                                {idx + 1}/{thread.length}
                              </span>
                              {tweet}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{
                          backgroundColor: "#1e293b", padding: "16px",
                          borderRadius: "10px", fontSize: "14px", lineHeight: 1.6,
                        }}>
                          {item.generated_tweet}
                        </div>
                      )}

                      {/* Action Buttons */}
                      <div style={{ display: "flex", gap: "12px", marginTop: "16px", flexWrap: "wrap" }}>
                        <button
                          onClick={() => handlePostThread(item.tweet_id, "tr")}
                          disabled={trPublished || !item.tr_thread?.length || publishState === "publishing"}
                          style={{
                            backgroundColor: trPublished ? "#334155" : "#6366f1", color: "white",
                            padding: "10px 24px", borderRadius: "8px",
                            border: "none", cursor: trPublished ? "not-allowed" : "pointer",
                            fontSize: "14px", fontWeight: 600,
                            opacity: trPublished ? 0.8 : 1,
                          }}
                        >
                          {trPublished ? "✅ TR Yayınlandı" : "🚀 TR Thread Yayınla"}
                        </button>
                        <button
                          onClick={() => handlePostThread(item.tweet_id, "en")}
                          disabled={enPublished || !item.en_thread?.length || publishState === "publishing"}
                          style={{
                            backgroundColor: enPublished ? "#334155" : "#0ea5e9", color: "white",
                            padding: "10px 24px", borderRadius: "8px",
                            border: "none", cursor: enPublished ? "not-allowed" : "pointer",
                            fontSize: "14px", fontWeight: 600,
                            opacity: enPublished ? 0.8 : 1,
                          }}
                        >
                          {enPublished ? "✅ EN Yayınlandı" : "🚀 EN Thread Yayınla"}
                        </button>
                        {item.sniper_targets?.length > 0 && (
                          <button
                            onClick={() => handleSniperReply(item.tweet_id)}
                            style={{
                              backgroundColor: "#d97706", color: "white",
                              padding: "10px 24px", borderRadius: "8px",
                              border: "none", cursor: "pointer",
                              fontSize: "14px", fontWeight: 600,
                            }}
                          >
                            🎯 Sniper Reply ({item.sniper_targets.length} hedef)
                          </button>
                        )}
                        {publishState === "failed" && (
                          <button
                            onClick={() => handleRetryThread(item.tweet_id, currentLang)}
                            style={{
                              backgroundColor: "#f97316", color: "white",
                              padding: "10px 24px", borderRadius: "8px",
                              border: "none", cursor: "pointer",
                              fontSize: "14px", fontWeight: 600,
                            }}
                          >
                            🔁 {currentLang.toUpperCase()} Retry / Resume
                          </button>
                        )}
                        <button
                          onClick={() => handleApprove(item.tweet_id)}
                          disabled={publishState === "publishing" || item.status === "processed"}
                          style={{
                            backgroundColor: "#10b981", color: "white",
                            padding: "10px 24px", borderRadius: "8px",
                            border: "none", cursor: "pointer",
                            fontSize: "14px", fontWeight: 600,
                          }}
                        >
                          ✅ Onayla
                        </button>
                        <button
                          onClick={() => handleReject(item.tweet_id)}
                          disabled={publishState === "publishing" || item.status === "processed"}
                          style={{
                            backgroundColor: "#ef4444", color: "white",
                            padding: "10px 24px", borderRadius: "8px",
                            border: "none", cursor: "pointer",
                            fontSize: "14px", fontWeight: 600,
                          }}
                        >
                          ❌ Reddet
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ApprovalInterface;
