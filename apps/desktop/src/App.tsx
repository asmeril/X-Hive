import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";
import XDaemonMonitor from "./components/XDaemonMonitor";
import XOperations from "./components/XOperations";
import ApprovalInterface from "./components/ApprovalInterface";

type HealthResponse = {
  status: string;
  worker?: string;
  lock_path?: string;
  data_path?: string;
  timestamp?: string;
};

type ApiResponse = Record<string, unknown>;

function App() {
  const [data, setData] = useState<HealthResponse | ApiResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<"monitor" | "operations" | "approval" | "health" | "lock">("monitor");

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const response = await invoke<string>("check_worker_health");
      const json: HealthResponse = JSON.parse(response);
      setData(json);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(`Failed to invoke health: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  const callWorkerApi = async (method: "GET" | "POST", endpoint: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const response = await invoke<string>("call_worker_api", { method, endpoint });
      const json: ApiResponse = JSON.parse(response);
      setData(json);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(`API call failed: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main style={{ backgroundColor: "#0f172a", minHeight: "100vh" }}>
      {/* Top Navigation Bar */}
      <div
        style={{
          backgroundColor: "#111827",
          borderBottom: "1px solid #374151",
          padding: "12px 24px",
          position: "sticky",
          top: 0,
          zIndex: 1000,
        }}
      >
        <div style={{ maxWidth: "1600px", margin: "0 auto" }}>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <h1 style={{ margin: 0, marginRight: "24px", fontSize: "20px", fontWeight: 700, color: "#f3f4f6" }}>
              X-HIVE Kontrol Paneli
            </h1>
            <button
              onClick={() => setActiveTab("monitor")}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "monitor" ? "#3b82f6" : "#374151",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              📊 İzleme
            </button>
            <button
              onClick={() => setActiveTab("approval")}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "approval" ? "#3b82f6" : "#374151",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              ✅ Onay
            </button>
            <button
              onClick={() => setActiveTab("operations")}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "operations" ? "#3b82f6" : "#374151",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              ⚙️ İşlemler
            </button>
            <button
              onClick={() => setActiveTab("health")}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "health" ? "#3b82f6" : "#374151",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              ❤️ Durum
            </button>
            <button
              onClick={() => setActiveTab("lock")}
              style={{
                padding: "8px 16px",
                borderRadius: "6px",
                border: "none",
                backgroundColor: activeTab === "lock" ? "#3b82f6" : "#374151",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              🔒 Kilit
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      {activeTab === "monitor" ? (
        <XDaemonMonitor />
      ) : activeTab === "approval" ? (
        <ApprovalInterface />
      ) : activeTab === "operations" ? (
        <div style={{ padding: "24px", backgroundColor: "#0f172a", minHeight: "calc(100vh - 73px)" }}>
          <XOperations />
        </div>
      ) : (
        <div
          style={{
            minHeight: "calc(100vh - 73px)",
            backgroundColor: "#0f172a",
            color: "#e5e7eb",
            padding: "24px",
          }}
        >
          <div
            style={{
              maxWidth: "800px",
              margin: "0 auto",
              backgroundColor: "#1e293b",
              border: "1px solid #334155",
              borderRadius: "12px",
              padding: "32px",
            }}
          >
            {activeTab === "health" && (
              <>
                <h2 style={{ 
                  fontSize: "28px", 
                  fontWeight: "bold", 
                  marginBottom: "12px",
                  color: "#f3f4f6" 
                }}>
                  ❤️ Worker Durumu
                </h2>
                <p style={{ 
                  marginBottom: "28px", 
                  color: "#94a3b8",
                  fontSize: "14px"
                }}>
                  Worker'ın sağlık durumunu kontrol edin
                </p>
                <button
                  onClick={checkHealth}
                  disabled={loading}
                  style={{
                    width: "100%",
                    padding: "14px 24px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: loading ? "#2563eb" : "#3b82f6",
                    color: "white",
                    fontSize: "16px",
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                    transition: "background-color 0.2s ease",
                  }}
                >
                  {loading ? "⏳ Kontrol ediliyor..." : "🔍 Worker Durumunu Kontrol Et"}
                </button>
              </>
            )}

            {activeTab === "lock" && (
              <>
                <h2 style={{ 
                  fontSize: "28px", 
                  fontWeight: "bold", 
                  marginBottom: "12px",
                  color: "#f3f4f6" 
                }}>
                  🔒 Kilit Yönetimi
                </h2>
                <p style={{ 
                  marginBottom: "28px", 
                  color: "#94a3b8",
                  fontSize: "14px"
                }}>
                  Worker kilidi al, bırak veya durumunu kontrol et
                </p>
                <div style={{ display: "flex", gap: "12px" }}>
                  <button
                    onClick={() => callWorkerApi("POST", "/lock/acquire")}
                    disabled={loading}
                    style={{
                      flex: 1,
                      padding: "14px 20px",
                      borderRadius: "8px",
                      border: "none",
                      backgroundColor: loading ? "#16a34a" : "#22c55e",
                      color: "white",
                      fontSize: "15px",
                      fontWeight: 600,
                      cursor: loading ? "not-allowed" : "pointer",
                      transition: "background-color 0.2s ease",
                    }}
                  >
                    {loading ? "⏳" : "🔒 Kilidi Al"}
                  </button>
                  <button
                    onClick={() => callWorkerApi("POST", "/lock/release")}
                    disabled={loading}
                    style={{
                      flex: 1,
                      padding: "14px 20px",
                      borderRadius: "8px",
                      border: "none",
                      backgroundColor: loading ? "#dc2626" : "#ef4444",
                      color: "white",
                      fontSize: "15px",
                      fontWeight: 600,
                      cursor: loading ? "not-allowed" : "pointer",
                      transition: "background-color 0.2s ease",
                    }}
                  >
                    {loading ? "⏳" : "🔓 Kilidi Bırak"}
                  </button>
                  <button
                    onClick={() => callWorkerApi("GET", "/lock/status")}
                    disabled={loading}
                    style={{
                      flex: 1,
                      padding: "14px 20px",
                      borderRadius: "8px",
                      border: "none",
                      backgroundColor: loading ? "#2563eb" : "#3b82f6",
                      color: "white",
                      fontSize: "15px",
                      fontWeight: 600,
                      cursor: loading ? "not-allowed" : "pointer",
                      transition: "background-color 0.2s ease",
                    }}
                  >
                    {loading ? "⏳" : "🔍 Durumu Kontrol Et"}
                  </button>
                </div>
              </>
            )}

        {error && (
          <div
            style={{
              backgroundColor: "#7f1d1d",
              border: "1px solid #ef4444",
              color: "#fecaca",
              padding: "12px",
              borderRadius: "8px",
              marginBottom: "12px",
              textAlign: "center",
            }}
          >
            {error}
          </div>
        )}

        {data && (
          <pre
            style={{
              backgroundColor: "#0b1020",
              border: "1px solid #1f2937",
              borderRadius: "8px",
              padding: "16px",
              overflowX: "auto",
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
              fontSize: "13px",
              lineHeight: 1.6,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        )}
      </div>
      </div>
      )}
    </main>
  );
}

export default App;
