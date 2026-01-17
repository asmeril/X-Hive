import { useState } from "react";
import { useEffect } from "react";
import "./App.css";

interface HealthResponse {
  status: string;
  timestamp: string;
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch("http://127.0.0.1:8765/health");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data: HealthResponse = await response.json();
      setHealth(data);
    } catch (err) {
      setError("Worker offline");
      setHealth(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <main
      style={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        backgroundColor: "#0f0f0f",
        fontFamily: "system-ui, -apple-system, sans-serif",
      }}
    >
      <div
        style={{
          backgroundColor: "#1a1a1a",
          border: "1px solid #333",
          borderRadius: "8px",
          padding: "32px",
          maxWidth: "500px",
          width: "100%",
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.5)",
        }}
      >
        <h1 style={{ marginTop: 0, color: "#fff", textAlign: "center" }}>
          X-HIVE Worker Status
        </h1>

        {isLoading && <p style={{ textAlign: "center", color: "#888" }}>Connecting...</p>}

        {error && (
          <div
            style={{
              backgroundColor: "#3a1a1a",
              border: "1px solid #ff4444",
              borderRadius: "4px",
              padding: "12px",
              color: "#ff6666",
              textAlign: "center",
              marginBottom: "16px",
            }}
          >
            {error}
          </div>
        )}

        {health && (
          <div style={{ marginBottom: "24px" }}>
            <div style={{ marginBottom: "12px" }}>
              <label style={{ color: "#aaa", fontSize: "12px" }}>Status:</label>
              <p
                style={{
                  margin: "4px 0 0 0",
                  color: "#4ade80",
                  fontSize: "18px",
                  fontWeight: "bold",
                }}
              >
                {health.status.toUpperCase()}
              </p>
            </div>
            <div>
              <label style={{ color: "#aaa", fontSize: "12px" }}>Timestamp:</label>
              <p
                style={{
                  margin: "4px 0 0 0",
                  color: "#888",
                  fontSize: "12px",
                  fontFamily: "monospace",
                  wordBreak: "break-all",
                }}
              >
                {health.timestamp}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={fetchHealth}
          disabled={isLoading}
          style={{
            width: "100%",
            padding: "12px",
            backgroundColor: "#0ea5e9",
            color: "#fff",
            border: "none",
            borderRadius: "6px",
            fontSize: "16px",
            fontWeight: "bold",
            cursor: isLoading ? "not-allowed" : "pointer",
            opacity: isLoading ? 0.6 : 1,
            transition: "all 0.2s",
          }}
          onMouseEnter={(e) => {
            if (!isLoading) (e.target as HTMLButtonElement).style.backgroundColor = "#0284c7";
          }}
          onMouseLeave={(e) => {
            (e.target as HTMLButtonElement).style.backgroundColor = "#0ea5e9";
          }}
        >
          {isLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>
    </main>
  );
}

export default App;
