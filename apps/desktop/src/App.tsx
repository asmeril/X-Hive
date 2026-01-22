import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";
import XDaemonMonitor from "./components/XDaemonMonitor";
import XOperations from "./components/XOperations";

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
  const [activeTab, setActiveTab] = useState<"monitor" | "operations" | "health" | "lock">("monitor");

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
    <main style={{ backgroundColor: "#f3f4f6", minHeight: "100vh" }}>
      {activeTab === "monitor" ? (
        <XDaemonMonitor />
      ) : (
        <div
          style={{
            display: "flex",
            minHeight: "100vh",
            alignItems: "center",
            justifyContent: "center",
            backgroundColor: "#0f172a",
            color: "#e5e7eb",
            fontFamily: "system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
            padding: "24px",
          }}
        >
      <div
        style={{
          width: "100%",
          maxWidth: "640px",
          backgroundColor: "#111827",
          border: "1px solid #374151",
          borderRadius: "12px",
          padding: "24px",
          boxShadow: "0 10px 25px rgba(0,0,0,0.3)",
        }}
      >
        <h1 style={{ marginTop: 0, marginBottom: 16, textAlign: "center" }}>
          X-HIVE Control Panel
        </h1>

        <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
          <button
            onClick={() => setActiveTab("monitor")}
            style={{
              flex: 1,
              padding: "10px 12px",
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
            Monitor
          </button>
          <button
            onClick={() => setActiveTab("operations")}
            style={{
              flex: 1,
              padding: "10px 12px",
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
            Operations
          </button>
          <button
            onClick={() => setActiveTab("health")}
            style={{
              flex: 1,
              padding: "10px 12px",
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
            Health
          </button>
          <button
            onClick={() => setActiveTab("lock")}
            style={{
              flex: 1,
              padding: "10px 12px",
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
            Lock Manager
          </button>
        </div>

        {activeTab === "operations" && <XOperations />}

        {activeTab === "health" && (
          <button
            onClick={checkHealth}
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px 16px",
              borderRadius: "8px",
              border: "none",
              backgroundColor: loading ? "#2563eb" : "#3b82f6",
              color: "white",
              fontSize: "16px",
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background-color 0.2s ease",
              marginBottom: "16px",
            }}
          >
            {loading ? "Checking..." : "Check Worker Health"}
          </button>
        )}

        {activeTab === "lock" && (
          <div style={{ display: "flex", gap: "8px", marginBottom: "16px" }}>
            <button
              onClick={() => callWorkerApi("POST", "/lock/acquire")}
              disabled={loading}
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: loading ? "#16a34a" : "#22c55e",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              {loading ? "..." : "Acquire Lock"}
            </button>
            <button
              onClick={() => callWorkerApi("POST", "/lock/release")}
              disabled={loading}
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: loading ? "#dc2626" : "#ef4444",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              {loading ? "..." : "Release Lock"}
            </button>
            <button
              onClick={() => callWorkerApi("GET", "/lock/status")}
              disabled={loading}
              style={{
                flex: 1,
                padding: "12px 16px",
                borderRadius: "8px",
                border: "none",
                backgroundColor: loading ? "#2563eb" : "#3b82f6",
                color: "white",
                fontSize: "14px",
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
                transition: "background-color 0.2s ease",
              }}
            >
              {loading ? "..." : "Check Status"}
            </button>
          </div>
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

        {!data && !error && (
          <p style={{ textAlign: "center", color: "#9ca3af" }}>
            Click "Check Worker Health" to query the local worker.
          </p>
        )}
      )}
    </main>
  );
}

export default App;
