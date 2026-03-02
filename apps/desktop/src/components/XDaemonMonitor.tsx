import React, { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";

interface DaemonStatus {
  status: string;
  uptime?: number;
  active_tasks?: number;
  completed_tasks?: number;
  chrome_pool?: {
    active: number;
    idle: number;
    total: number;
  };
}

interface DaemonApiResponse {
  status: string;
  daemon?: {
    daemon_status?: string;
    uptime_seconds?: number;
    queue_stats?: {
      running?: number;
      completed?: number;
      active_count?: number;
      completed_count?: number;
    };
    chrome_pool_healthy?: boolean;
  };
}

const XDaemonMonitor: React.FC = () => {
  const [status, setStatus] = useState<DaemonStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [autoStartTried, setAutoStartTried] = useState(false);
  const userStoppedRef = useRef(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const response = await invoke<string>("call_worker_api", {
        method: "GET",
        endpoint: "/daemon/status",
      });
      const parsed: DaemonApiResponse & any = JSON.parse(response);

      const daemonNode = parsed.daemon || parsed;

      const daemonStatus: DaemonStatus = {
        status: daemonNode.daemon_status || parsed.status || "stopped",
        uptime: daemonNode.uptime_seconds || parsed.uptime || 0,
        active_tasks:
          daemonNode.queue_stats?.running ||
          daemonNode.queue_stats?.active_count ||
          parsed.active_tasks ||
          0,
        completed_tasks:
          daemonNode.queue_stats?.completed ||
          daemonNode.queue_stats?.completed_count ||
          parsed.completed_tasks ||
          0,
        chrome_pool: {
          active: daemonNode.chrome_pool_healthy ? 1 : 0,
          idle: 0,
          total: daemonNode.chrome_pool_healthy ? 1 : 0,
        },
      };

      setStatus(daemonStatus);
      setError(null);

      if (daemonStatus.status !== "running" && !autoStartTried && !userStoppedRef.current) {
        setAutoStartTried(true);
        await invoke<string>("call_worker_api", {
          method: "POST",
          endpoint: "/daemon/start",
        });
        const retryResponse = await invoke<string>("call_worker_api", {
          method: "GET",
          endpoint: "/daemon/status",
        });
        const retryParsed: DaemonApiResponse & any = JSON.parse(retryResponse);
        const retryDaemonNode = retryParsed.daemon || retryParsed;
        setStatus((prev) => ({
          ...(prev || { status: "stopped" }),
          status: retryDaemonNode.daemon_status || retryParsed.status || "stopped",
          uptime: retryDaemonNode.uptime_seconds || retryParsed.uptime || 0,
          active_tasks:
            retryDaemonNode.queue_stats?.running ||
            retryDaemonNode.queue_stats?.active_count ||
            retryParsed.active_tasks ||
            0,
          completed_tasks:
            retryDaemonNode.queue_stats?.completed ||
            retryDaemonNode.queue_stats?.completed_count ||
            retryParsed.completed_tasks ||
            0,
          chrome_pool: {
            active: retryDaemonNode.chrome_pool_healthy ? 1 : 0,
            idle: 0,
            total: retryDaemonNode.chrome_pool_healthy ? 1 : 0,
          },
        }));
      }
    } catch (e: any) {
      console.error("Status fetch error:", e);
      const errorMsg = typeof e === "string" ? e : e?.message || JSON.stringify(e);
      setError(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const startDaemon = async () => {
    try {
      userStoppedRef.current = false;
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/daemon/start",
      });
      await fetchStatus();
    } catch (e: any) {
      setError(typeof e === "string" ? e : e?.message || JSON.stringify(e));
    }
  };

  const stopDaemon = async () => {
    try {
      userStoppedRef.current = true;
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/daemon/stop",
      });
      await fetchStatus();
    } catch (e: any) {
      setError(typeof e === "string" ? e : e?.message || JSON.stringify(e));
    }
  };

  const restartDaemon = async () => {
    try {
      userStoppedRef.current = false;
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/daemon/restart",
      });
      setTimeout(() => fetchStatus(), 2000);
    } catch (e: any) {
      setError(typeof e === "string" ? e : e?.message || JSON.stringify(e));
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) return `${hours}s ${minutes}d ${secs}s`;
    if (minutes > 0) return `${minutes}d ${secs}s`;
    return `${secs}s`;
  };

  return (
    <div style={{
      minHeight: "calc(100vh - 73px)",
      backgroundColor: "#0f172a",
      padding: "24px",
      color: "white"
    }}>
      <div style={{ maxWidth: "1200px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "24px"
        }}>
          <h1 style={{ fontSize: "28px", fontWeight: "bold" }}>
            🤖 X-Daemon İzleme
          </h1>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "8px", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                style={{ width: "18px", height: "18px", cursor: "pointer" }}
              />
              <span style={{ fontSize: "14px" }}>Otomatik Yenile (5s)</span>
            </label>
            <button
              onClick={fetchStatus}
              disabled={loading}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: loading ? "#4b5563" : "#3b82f6",
                color: "white",
                cursor: loading ? "not-allowed" : "pointer",
                fontSize: "14px",
                fontWeight: "500"
              }}
            >
              🔄 Yenile
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            backgroundColor: "#7f1d1d",
            border: "1px solid #ef4444",
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "24px"
          }}>
            ❌ {error}
          </div>
        )}

        {/* Status Cards */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
          gap: "16px",
          marginBottom: "24px"
        }}>
          {/* Daemon Status Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              Daemon Durumu
            </div>
            <div style={{
              fontSize: "24px",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              gap: "8px"
            }}>
              <span style={{
                width: "12px",
                height: "12px",
                borderRadius: "50%",
                backgroundColor: status?.status === "running" ? "#10b981" : "#ef4444"
              }} />
              {loading ? "..." : status?.status === "running" ? "Çalışıyor" : "Durdu"}
            </div>
            {status?.uptime && (
              <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
                ⏱️ Çalışma süresi: {formatUptime(status.uptime)}
              </div>
            )}
          </div>

          {/* Active Tasks Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              Aktif Görevler
            </div>
            <div style={{ fontSize: "32px", fontWeight: "bold", color: "#3b82f6" }}>
              {loading ? "..." : status?.active_tasks || 0}
            </div>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
              📊 Tamamlanan: {status?.completed_tasks || 0}
            </div>
          </div>

          {/* Chrome Pool Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              Chrome Havuzu
            </div>
            <div style={{ fontSize: "32px", fontWeight: "bold", color: "#10b981" }}>
              {loading ? "..." : status?.chrome_pool?.active || 0}/{status?.chrome_pool?.total || 0}
            </div>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
              💤 Boşta: {status?.chrome_pool?.idle || 0}
            </div>
          </div>
        </div>

        {/* Control Buttons */}
        <div style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "24px"
        }}>
          <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
            Daemon Kontrolleri
          </h2>
          <div style={{ display: "flex", gap: "12px" }}>
            <button
              onClick={startDaemon}
              disabled={status?.status === "running"}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: status?.status === "running" ? "#374151" : "#10b981",
                color: "white",
                cursor: status?.status === "running" ? "not-allowed" : "pointer",
                fontSize: "16px",
                fontWeight: "600"
              }}
            >
              ▶️ Başlat
            </button>
            <button
              onClick={stopDaemon}
              disabled={status?.status !== "running"}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: status?.status !== "running" ? "#374151" : "#ef4444",
                color: "white",
                cursor: status?.status !== "running" ? "not-allowed" : "pointer",
                fontSize: "16px",
                fontWeight: "600"
              }}
            >
              ⏹️ Durdur
            </button>
            <button
              onClick={restartDaemon}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: "#f59e0b",
                color: "white",
                cursor: "pointer",
                fontSize: "16px",
                fontWeight: "600"
              }}
            >
              🔄 Yeniden Başlat
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default XDaemonMonitor;
