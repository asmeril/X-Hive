import React, { useState, useEffect } from "react";
import { invoke } from "@tauri-apps/api/core";

interface ApprovalItem {
  id: string;
  tweet_id: string;
  generated_tweet: string;
  status: string;
  created_at: string;
}

interface ApiResponse {
  status: string;
  data?: {
    items: ApprovalItem[];
    total: number;
  };
  message?: string;
}

const ApprovalInterface: React.FC = () => {
  const [items, setItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchItems = async () => {
      try {
        console.log("🔵 Fetching pending items...");
        setLoading(true);
        
        const response = await invoke<string>("call_worker_api", {
          method: "GET",
          endpoint: "/approval/pending",
        });
        
        console.log("🟢 Raw Response:", response);
        const parsed: ApiResponse = JSON.parse(response);
        console.log("🟡 Parsed:", parsed);
        
        if (parsed.status === "success" && parsed.data?.items) {
          console.log("✅ Items received:", parsed.data.items.length);
          setItems(parsed.data.items);
        } else {
          console.log("⚠️ No items in response");
          setError("No items found");
        }
      } catch (e: any) {
        console.error("❌ Error:", e);
        setError(e.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    
    fetchItems();
  }, []);

  const handleApprove = async (itemId: string) => {
    try {
      console.log("🟢 Approving item:", itemId);
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/approve/${itemId}`,
      });
      const parsed: ApiResponse = JSON.parse(response);
      
      if (parsed.status === "success") {
        console.log("✅ Item approved:", itemId);
        setItems(prev => prev.filter(item => item.tweet_id !== itemId));
      }
    } catch (e: any) {
      console.error("❌ Approve error:", e);
      setError(e.message);
    }
  };

  const handleReject = async (itemId: string) => {
    try {
      console.log("🔴 Rejecting item:", itemId);
      const response = await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/approval/reject/${itemId}`,
      });
      const parsed: ApiResponse = JSON.parse(response);
      
      if (parsed.status === "success") {
        console.log("✅ Item rejected:", itemId);
        setItems(prev => prev.filter(item => item.tweet_id !== itemId));
      }
    } catch (e: any) {
      console.error("❌ Reject error:", e);
      setError(e.message);
    }
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
        <h1 style={{ fontSize: "28px", fontWeight: "bold", marginBottom: "24px" }}>
          ✅ İçerik Onayı
        </h1>

      {/* Debug Info */}
      <div style={{ 
        backgroundColor: "#111827",
        border: "1px solid #374151",
        padding: "16px", 
        borderRadius: "8px",
        marginBottom: "24px",
        fontFamily: "monospace",
        fontSize: "14px"
      }}>
        <div>⏱️ Yükleniyor: {loading.toString()}</div>
        <div>📦 İçerikler: {items.length}</div>
        <div>❌ Hata: {error || "yok"}</div>
      </div>

      {loading && (
        <div style={{ textAlign: "center", padding: "40px" }}>
          <div style={{ fontSize: "48px" }}>⏳</div>
          <div style={{ marginTop: "16px" }}>Yüklenıyor...</div>
        </div>
      )}

      {error && !loading && (
        <div style={{ 
          backgroundColor: "#7f1d1d", 
          padding: "16px", 
          borderRadius: "8px",
          marginBottom: "16px"
        }}>
          ❌ Hata: {error}
        </div>
      )}
      
      {!loading && items.length === 0 && !error && (
        <div style={{ 
          textAlign: "center", 
          padding: "40px",
          backgroundColor: "#374151",
          borderRadius: "8px"
        }}>
          <div style={{ fontSize: "48px" }}>✅</div>
          <div style={{ marginTop: "16px", fontSize: "18px" }}>
            Bekleyen içerik yok
          </div>
        </div>
      )}
      
      {items.length > 0 && (
        <div style={{ display: "grid", gap: "16px" }}>
          {items.map((item: ApprovalItem) => (
            <div key={item.tweet_id} style={{ 
              backgroundColor: "#374151", 
              padding: "20px", 
              borderRadius: "12px",
              border: "1px solid #4b5563"
            }}>
              <div style={{ 
                fontSize: "16px", 
                fontWeight: "500", 
                marginBottom: "12px",
                lineHeight: "1.5"
              }}>
                {item.generated_tweet || "No content"}
              </div>
              
              <div style={{ 
                fontSize: "12px", 
                color: "#9ca3af", 
                marginBottom: "16px",
                display: "flex",
                gap: "16px"
              }}>
                <span>🆔 {item.tweet_id}</span>
                <span>📊 {item.status}</span>
                <span>🕐 {new Date(item.created_at).toLocaleString()}</span>
              </div>

              <div style={{ display: "flex", gap: "12px" }}>
                <button
                  onClick={() => handleApprove(item.tweet_id)}
                  style={{
                    backgroundColor: "#10b981",
                    color: "white",
                    padding: "10px 20px",
                    borderRadius: "8px",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "500"
                  }}
                >
                  ✅ Onayla
                </button>
                <button
                  onClick={() => handleReject(item.tweet_id)}
                  style={{
                    backgroundColor: "#ef4444",
                    color: "white",
                    padding: "10px 20px",
                    borderRadius: "8px",
                    border: "none",
                    cursor: "pointer",
                    fontSize: "14px",
                    fontWeight: "500"
                  }}
                >
                  ❌ Reddet
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
      </div>
    </div>
  );
};

export default ApprovalInterface;
