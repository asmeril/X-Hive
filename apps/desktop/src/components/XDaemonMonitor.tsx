import React, { useState, useEffect, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";

interface SystemStatus {
  status: string;
  services: {
    orchestrator: {
      running: boolean;
      ai_enabled: boolean;
      intel_enabled: boolean;
    };
    task_queue: {
      running: boolean;
      stats: {
        active_count: number;
        completed_count: number;
      };
    };
    chrome_pool: {
      running: boolean;
      healthy: boolean;
    };
    x_daemon: {
      daemon_status: string;
      uptime_seconds: number;
    };
    scheduler: {
      running: boolean;
    };
  };
}

const XDaemonMonitor: React.FC = () => {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [autoStartTried, setAutoStartTried] = useState(false);
  const [isForceIntelLoading, setIsForceIntelLoading] = useState(false);
  const userStoppedRef = useRef(false);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      
      const response = await invoke<string>("call_worker_api", {
        method: "GET",
        endpoint: "/system/status",
      });
      const parsed: SystemStatus | any = JSON.parse(response);

      if (parsed.status === "ok") {
        setStatus(parsed);
      } else {
        // Fallback or error state
        setError("API yanitinda hata: " + parsed.message);
      }
      
      setError(null);

      if (!parsed.services?.x_daemon?.daemon_status || parsed.services.x_daemon.daemon_status !== "running") {
        if (!autoStartTried && !userStoppedRef.current) {
          setAutoStartTried(true);
          await invoke<string>("call_worker_api", {
            method: "POST",
            endpoint: "/daemon/start",
          });
          // Retry
          const retryResponse = await invoke<string>("call_worker_api", {
            method: "GET",
            endpoint: "/system/status",
          });
          const retryParsed = JSON.parse(retryResponse);
          if (retryParsed.status === "ok") setStatus(retryParsed);
        }
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

  const forceIntelCollection = async () => {
    try {
      setIsForceIntelLoading(true);
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/system/force-intel",
      });
      const parsed = JSON.parse(response);
      if (parsed.status === "ok") {
        alert(parsed.message || "Haber toplama manuel olarak başlatıldı.");
      } else {
        setError(parsed.message || "Başlatılamadı");
      }
    } catch (e: any) {
      setError(typeof e === "string" ? e : e?.message || JSON.stringify(e));
    } finally {
      setIsForceIntelLoading(false);
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
    if (!seconds) return "0s";
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) return `${hours}s ${minutes}d ${secs}s`;
    if (minutes > 0) return `${minutes}d ${secs}s`;
    return `${secs}s`;
  };

  const isOrchestratorRunning = status?.services?.orchestrator?.running;
  const isAiEnabled = status?.services?.orchestrator?.ai_enabled;
  const isSchedulerRunning = status?.services?.scheduler?.running;
  const isChromeHealthy = status?.services?.chrome_pool?.healthy;

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
            🤖 X-Hive Sistem İzleme (Tüm Servisler)
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
          {/* Orchestrator Status Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <div style={{ fontSize: "14px", color: "#94a3b8" }}>
                🛠️ Ana Orkestratör
              </div>
              <button
                onClick={forceIntelCollection}
                disabled={!isOrchestratorRunning || isForceIntelLoading}
                style={{
                  padding: "4px 8px",
                  borderRadius: "6px",
                  border: "none",
                  backgroundColor: !isOrchestratorRunning || isForceIntelLoading ? "#374151" : "#8b5cf6",
                  color: "white",
                  cursor: !isOrchestratorRunning || isForceIntelLoading ? "not-allowed" : "pointer",
                  fontSize: "11px",
                  fontWeight: "bold",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px"
                }}
              >
                {isForceIntelLoading ? "⏳ Başlıyor" : "🔍 Hemen Tarama Başlat"}
              </button>
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
                backgroundColor: isOrchestratorRunning ? "#10b981" : "#ef4444"
              }} />
              {loading ? "..." : isOrchestratorRunning ? "Çalışıyor" : "Durdu"}
            </div>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
              📡 Haber Toplayıcı: Aktif
            </div>
          </div>

          {/* AI Generator Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              🧠 Yapay Zeka (AI) Motoru
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
                backgroundColor: isAiEnabled ? "#10b981" : "#ef4444"
              }} />
              {loading ? "..." : isAiEnabled ? "Aktif" : "Devre Dışı"}
            </div>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
              🤖 İçerikler Tweet'e Çevriliyor
            </div>
          </div>

          {/* Post Scheduler Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              📅 Paylaşım Zamanlayıcı
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
                backgroundColor: isSchedulerRunning ? "#10b981" : "#b45309"
              }} />
              {loading ? "..." : isSchedulerRunning ? "Aktif" : "Beklemede"}
            </div>
          </div>
          
          {/* Daemon Status Card */}
          <div style={{
            backgroundColor: "#1e293b",
            border: "1px solid #334155",
            borderRadius: "12px",
            padding: "20px"
          }}>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginBottom: "8px" }}>
              🐦 X-Daemon (Tarayıcı İşçisi)
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
                backgroundColor: status?.services?.x_daemon?.daemon_status === "running" ? "#10b981" : "#ef4444"
              }} />
              {loading ? "..." : status?.services?.x_daemon?.daemon_status === "running" ? "Çalışıyor" : "Durdu"}
            </div>
            {status?.services?.x_daemon?.uptime_seconds !== undefined && (
              <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
                ⏱️ Çalışma süresi: {formatUptime(status.services.x_daemon.uptime_seconds)}
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
              Görev Kuyruğu (Task Queue)
            </div>
            <div style={{ fontSize: "32px", fontWeight: "bold", color: "#3b82f6" }}>
              {loading ? "..." : status?.services?.task_queue?.stats?.active_count || 0}
            </div>
            <div style={{ fontSize: "14px", color: "#94a3b8", marginTop: "8px" }}>
              📊 Tamamlanan: {status?.services?.task_queue?.stats?.completed_count || 0}
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
              Görünmez Tarayıcı (Headless Chrome)
            </div>
            <div style={{ fontSize: "24px", fontWeight: "bold", color: "#10b981" }}>
              {loading ? "..." : (isChromeHealthy ? "Sağlıklı ✅" : "Sorunlu ❌")}
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
              disabled={status?.services?.x_daemon?.daemon_status === "running"}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: status?.services?.x_daemon?.daemon_status === "running" ? "#374151" : "#10b981",
                color: "white",
                cursor: status?.services?.x_daemon?.daemon_status === "running" ? "not-allowed" : "pointer",
                fontSize: "16px",
                fontWeight: "600"
              }}
            >
              ▶️ Başlat
            </button>
            <button
              onClick={stopDaemon}
              disabled={status?.services?.x_daemon?.daemon_status !== "running"}
              style={{
                flex: 1,
                padding: "12px 24px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: status?.services?.x_daemon?.daemon_status !== "running" ? "#374151" : "#ef4444",
                color: "white",
                cursor: status?.services?.x_daemon?.daemon_status !== "running" ? "not-allowed" : "pointer",
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
