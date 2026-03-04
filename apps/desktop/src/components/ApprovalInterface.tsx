import React, { useState, useEffect, useCallback } from "react";
import { invoke } from "@tauri-apps/api/core";

interface ContentItemData {
  title: string;
  url: string;
  source_name: string;
  source_type: string;
  category: string | null;
}

interface ApprovalItem {
  id: string;
  tweet_id: string;
  generated_tweet: string;
  status: string;
  created_at: string;
  viral_score: number;
  tr_thread: string[];
  en_thread: string[];
  mentions: string[];
  keywords: string[];
  image_url: string | null;
  sniper_targets: Array<{ username: string; handle: string; name: string; relevance_score: number }>;
  content_item: ContentItemData;
}

interface ApiResponse {
  status: string;
  data?: {
    items: ApprovalItem[];
    total: number;
  };
  message?: string;
}

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
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [langTab, setLangTab] = useState<Record<string, "tr" | "en">>({});

  const fetchItems = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await invoke<string>("call_worker_api", {
        method: "GET",
        endpoint: "/approval/pending",
      });
      const parsed: ApiResponse = JSON.parse(response);
      if (parsed.status === "success" && parsed.data?.items) {
        setItems(parsed.data.items);
      } else {
        setItems([]);
      }
    } catch (e: any) {
      setError(e.message || "Bağlantı hatası");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchItems(); }, [fetchItems]);

  const handleScan = async () => {
    setScanning(true);
    setError(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/system/force-intel",
      });
      // Poll until done (check every 15s, max 5 min)
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        await fetchItems();
        if (items.length > 0 || attempts > 20) {
          clearInterval(poll);
          setScanning(false);
        }
      }, 15000);
      // Also show message
      setTimeout(() => fetchItems(), 30000);
    } catch (e: any) {
      setError(e.message);
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
        setItems(prev => prev.filter(item => item.tweet_id !== itemId));
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
        setItems(prev => prev.filter(item => item.tweet_id !== itemId));
      }
    } catch (e: any) {
      setError(e.message);
    }
  };

  const handlePostThread = async (itemId: string) => {
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/post-thread/${itemId}`,
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        setItems(prev => prev.filter(item => item.tweet_id !== itemId));
        setError(null);
      } else {
        setError(parsed.message || "Thread yayınlanamadı");
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
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/approval/approve-all-threads",
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "success") {
        setItems([]);
      }
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
        {!loading && items.length === 0 && !error && (
          <div style={{
            textAlign: "center", padding: "60px",
            backgroundColor: "#1e293b", borderRadius: "12px"
          }}>
            <div style={{ fontSize: "48px" }}>📭</div>
            <div style={{ marginTop: "16px", fontSize: "18px", color: "#d1d5db" }}>
              Bekleyen thread yok
            </div>
            <div style={{ marginTop: "8px", color: "#6b7280", fontSize: "14px" }}>
              "Yeni Tarama" ile viral içerikleri keşfedin
            </div>
          </div>
        )}

        {/* Thread Cards */}
        {items.length > 0 && (
          <div style={{ display: "grid", gap: "16px" }}>
            {items.map((item: ApprovalItem) => {
              const isExpanded = expandedId === item.tweet_id;
              const currentLang = getLang(item.tweet_id);
              const thread = currentLang === "tr" ? (item.tr_thread || []) : (item.en_thread || []);
              const viralColor = getViralColor(item.viral_score || 0);
              const hasThread = thread.length > 0;

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
                          onClick={() => handlePostThread(item.tweet_id)}
                          style={{
                            backgroundColor: "#6366f1", color: "white",
                            padding: "10px 24px", borderRadius: "8px",
                            border: "none", cursor: "pointer",
                            fontSize: "14px", fontWeight: 600,
                          }}
                        >
                          🚀 Yayınla (Thread At)
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
                        <button
                          onClick={() => handleApprove(item.tweet_id)}
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
