import { useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import "./App.css";

type HealthResponse = {
  status: string;
  worker?: string;
  lock_path?: string;
  data_path?: string;
  timestamp?: string;
};

function App() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

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

  return (
    <main
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
      </div>
    </main>
  );
}

export default App;
