import { useCallback, useEffect, useMemo, useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type DashboardKpis = {
  thread_started_24h: number;
  thread_success_24h: number;
  thread_failed_24h: number;
  thread_success_rate_24h: number;
  sniper_started_24h: number;
  sniper_success_24h?: number;
  sniper_preview_done_24h: number;
  sniper_failed_24h: number;
  approvals_24h: number;
  rejections_24h: number;
};

type DashboardQueue = {
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  processed: number;
};

type DashboardViralProxy = {
  avg_processed_score: number;
  avg_pending_score: number;
  high_score_processed: number;
  note: string;
};

type EventItem = {
  event_id: string;
  timestamp: string;
  action: string;
  status: string;
  item_id?: string | null;
  source: string;
  viral_score?: number | null;
  details?: Record<string, unknown>;
};

type DashboardData = {
  kpis: DashboardKpis;
  queue: DashboardQueue;
  viral_proxy: DashboardViralProxy;
  recent_events: EventItem[];
};

type ApiEnvelope = {
  status: string;
  data?: DashboardData;
  message?: string;
};

const emptyData: DashboardData = {
  kpis: {
    thread_started_24h: 0,
    thread_success_24h: 0,
    thread_failed_24h: 0,
    thread_success_rate_24h: 0,
    sniper_started_24h: 0,
    sniper_preview_done_24h: 0,
    sniper_failed_24h: 0,
    approvals_24h: 0,
    rejections_24h: 0,
  },
  queue: {
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    processed: 0,
  },
  viral_proxy: {
    avg_processed_score: 0,
    avg_pending_score: 0,
    high_score_processed: 0,
    note: "",
  },
  recent_events: [],
};

function formatDateTime(value: string): string {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.toLocaleDateString("tr-TR")} ${date.toLocaleTimeString("tr-TR")}`;
}

function badgeColor(status: string): string {
  if (status === "success" || status === "approved" || status === "preview_done") return "#16a34a";
  if (status === "failed" || status === "rejected") return "#dc2626";
  if (status === "started") return "#2563eb";
  if (status === "no_targets") return "#d97706";
  return "#475569";
}

export default function OutcomeTracker() {
  const [data, setData] = useState<DashboardData>(emptyData);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await invoke<string>("call_worker_api", {
        method: "GET",
        endpoint: "/analytics/dashboard?limit=80",
      });
      const parsed: ApiEnvelope = JSON.parse(response);
      if (parsed.status !== "success" || !parsed.data) {
        setError(parsed.message || "Dashboard verisi alınamadı");
        return;
      }
      setData(parsed.data);
      setLastUpdated(new Date().toLocaleTimeString("tr-TR"));
    } catch (requestError: unknown) {
      const message = requestError instanceof Error ? requestError.message : "Unknown error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
    const timer = window.setInterval(() => {
      fetchDashboard();
    }, 20000);
    return () => window.clearInterval(timer);
  }, [fetchDashboard]);

  const summary = useMemo(
    () => [
      { label: "Thread Başladı (24s)", value: data.kpis.thread_started_24h },
      { label: "Thread Başarılı", value: data.kpis.thread_success_24h },
      { label: "Thread Başarı %", value: `${data.kpis.thread_success_rate_24h}%` },
      { label: "Sniper Başladı", value: data.kpis.sniper_started_24h },
      { label: "Sniper Başarılı", value: data.kpis.sniper_success_24h ?? data.kpis.sniper_preview_done_24h },
      { label: "Onaylanan", value: data.kpis.approvals_24h },
    ],
    [data]
  );

  return (
    <div style={{ minHeight: "calc(100vh - 73px)", backgroundColor: "#0f172a", color: "#e2e8f0", padding: "24px" }}>
      <div style={{ maxWidth: "1400px", margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
          <div>
            <h2 style={{ margin: 0, fontSize: "28px", color: "#f8fafc" }}>📈 Sonuçlar & Etkileşim</h2>
            <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "14px" }}>
              Thread/sniper/approval işlemlerinin 24 saatlik operasyon özeti
            </p>
          </div>
          <button
            onClick={fetchDashboard}
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

        {lastUpdated && (
          <p style={{ margin: "0 0 18px", color: "#64748b", fontSize: "12px" }}>
            Son güncelleme: {lastUpdated}
          </p>
        )}

        {error && (
          <div
            style={{
              backgroundColor: "#7f1d1d",
              border: "1px solid #ef4444",
              color: "#fecaca",
              borderRadius: "10px",
              padding: "12px 14px",
              marginBottom: "16px",
            }}
          >
            Dashboard hatası: {error}
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: "12px", marginBottom: "18px" }}>
          {summary.map((item) => (
            <div key={item.label} style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "10px", padding: "14px" }}>
              <div style={{ color: "#94a3b8", fontSize: "12px", marginBottom: "8px" }}>{item.label}</div>
              <div style={{ color: "#f8fafc", fontSize: "22px", fontWeight: 700 }}>{item.value}</div>
            </div>
          ))}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1.1fr 0.9fr", gap: "14px" }}>
          <div style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "12px", padding: "16px" }}>
            <h3 style={{ marginTop: 0, color: "#f1f5f9" }}>🕒 Son Olaylar</h3>
            <div style={{ maxHeight: "420px", overflowY: "auto" }}>
              {data.recent_events.length === 0 ? (
                <p style={{ color: "#94a3b8" }}>Henüz event yok.</p>
              ) : (
                data.recent_events.map((event) => (
                  <div
                    key={event.event_id}
                    style={{
                      borderBottom: "1px solid #334155",
                      padding: "10px 0",
                      display: "grid",
                      gridTemplateColumns: "170px 120px 120px 1fr",
                      gap: "8px",
                      alignItems: "center",
                      fontSize: "13px",
                    }}
                  >
                    <span style={{ color: "#94a3b8" }}>{formatDateTime(event.timestamp)}</span>
                    <span style={{ color: "#cbd5e1" }}>{event.action}</span>
                    <span
                      style={{
                        backgroundColor: badgeColor(event.status),
                        color: "white",
                        padding: "2px 8px",
                        borderRadius: "9999px",
                        textAlign: "center",
                        width: "fit-content",
                        fontSize: "12px",
                      }}
                    >
                      {event.status}
                    </span>
                    <span style={{ color: "#e2e8f0" }}>
                      {event.item_id || "-"} · {event.source}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "12px", padding: "16px" }}>
              <h3 style={{ marginTop: 0, color: "#f1f5f9" }}>🗂️ Queue Dağılımı</h3>
              <p style={{ margin: "4px 0", color: "#94a3b8" }}>Toplam: {data.queue.total}</p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>Pending: {data.queue.pending}</p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>Approved: {data.queue.approved}</p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>Rejected: {data.queue.rejected}</p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>Processed: {data.queue.processed}</p>
            </div>

            <div style={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: "12px", padding: "16px" }}>
              <h3 style={{ marginTop: 0, color: "#f1f5f9" }}>🔥 Viral Proxy</h3>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>
                Avg Processed Score: {data.viral_proxy.avg_processed_score}
              </p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>
                Avg Pending Score: {data.viral_proxy.avg_pending_score}
              </p>
              <p style={{ margin: "4px 0", color: "#e2e8f0" }}>
                High Score Processed (≥8): {data.viral_proxy.high_score_processed}
              </p>
              <p style={{ margin: "10px 0 0", color: "#94a3b8", fontSize: "12px", lineHeight: 1.5 }}>
                {data.viral_proxy.note}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
