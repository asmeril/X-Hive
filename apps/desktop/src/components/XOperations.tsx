import React, { useState } from "react";
import { invoke } from "@tauri-apps/api/core";

type OperationType = "post" | "reply" | "quote" | "like" | "retweet";

const XOperations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<OperationType>("post");
  const [tweetText, setTweetText] = useState("");
  const [tweetId, setTweetId] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const MAX_LENGTH = 280;

  const handlePost = async () => {
    if (!tweetText.trim()) {
      setMessage({ type: "error", text: "Tweet metni boş olamaz" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/operations/post",
        body: JSON.stringify({ text: tweetText }),
      });
      setMessage({ type: "success", text: "Tweet gönderildi!" });
      setTweetText("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Hata oluştu" });
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async () => {
    if (!tweetText.trim() || !tweetId.trim()) {
      setMessage({ type: "error", text: "Tweet ID ve metin gerekli" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/operations/reply",
        body: JSON.stringify({ tweet_id: tweetId, text: tweetText }),
      });
      setMessage({ type: "success", text: "Yanıt gönderildi!" });
      setTweetText("");
      setTweetId("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Hata oluştu" });
    } finally {
      setLoading(false);
    }
  };

  const handleQuote = async () => {
    if (!tweetText.trim() || !tweetId.trim()) {
      setMessage({ type: "error", text: "Tweet ID ve metin gerekli" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: "/operations/quote",
        body: JSON.stringify({ tweet_id: tweetId, text: tweetText }),
      });
      setMessage({ type: "success", text: "Alıntı gönderildi!" });
      setTweetText("");
      setTweetId("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Hata oluştu" });
    } finally {
      setLoading(false);
    }
  };

  const handleLike = async () => {
    if (!tweetId.trim()) {
      setMessage({ type: "error", text: "Tweet ID gerekli" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/operations/like/${tweetId}`,
      });
      setMessage({ type: "success", text: "Tweet beğenildi!" });
      setTweetId("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Hata oluştu" });
    } finally {
      setLoading(false);
    }
  };

  const handleRetweet = async () => {
    if (!tweetId.trim()) {
      setMessage({ type: "error", text: "Tweet ID gerekli" });
      return;
    }
    setLoading(true);
    setMessage(null);
    try {
      await invoke<string>("call_worker_api", {
        method: "POST",
        endpoint: `/operations/retweet/${tweetId}`,
      });
      setMessage({ type: "success", text: "Retweet yapıldı!" });
      setTweetId("");
    } catch (e: any) {
      setMessage({ type: "error", text: e.message || "Hata oluştu" });
    } finally {
      setLoading(false);
    }
  };

  const renderTabButton = (type: OperationType, icon: string, label: string) => (
    <button
      onClick={() => setActiveTab(type)}
      style={{
        flex: 1,
        padding: "12px 16px",
        borderRadius: "8px",
        border: "none",
        backgroundColor: activeTab === type ? "#3b82f6" : "#374151",
        color: "white",
        cursor: "pointer",
        fontSize: "14px",
        fontWeight: "600",
        transition: "background-color 0.2s"
      }}
    >
      {icon} {label}
    </button>
  );

  const charCount = tweetText.length;
  const charCountColor = charCount > MAX_LENGTH ? "#ef4444" : charCount > MAX_LENGTH * 0.9 ? "#f59e0b" : "#10b981";

  return (
    <div style={{
      minHeight: "calc(100vh - 73px)",
      backgroundColor: "#0f172a",
      padding: "24px",
      color: "white"
    }}>
      <div style={{ maxWidth: "800px", margin: "0 auto" }}>
        <h1 style={{ fontSize: "28px", fontWeight: "bold", marginBottom: "24px" }}>
          🐦 X İşlemleri
        </h1>

        {/* Tab Buttons */}
        <div style={{ display: "flex", gap: "8px", marginBottom: "24px" }}>
          {renderTabButton("post", "📝", "Gönderi")}
          {renderTabButton("reply", "💬", "Yanıt")}
          {renderTabButton("quote", "🔖", "Alıntı")}
          {renderTabButton("like", "❤️", "Beğen")}
          {renderTabButton("retweet", "🔁", "Retweet")}
        </div>

        {/* Message */}
        {message && (
          <div style={{
            backgroundColor: message.type === "success" ? "#065f46" : "#7f1d1d",
            border: `1px solid ${message.type === "success" ? "#10b981" : "#ef4444"}`,
            padding: "16px",
            borderRadius: "8px",
            marginBottom: "24px"
          }}>
            {message.type === "success" ? "✅" : "❌"} {message.text}
          </div>
        )}

        {/* Content Area */}
        <div style={{
          backgroundColor: "#1e293b",
          border: "1px solid #334155",
          borderRadius: "12px",
          padding: "24px"
        }}>
          {/* Post Tab */}
          {activeTab === "post" && (
            <>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
                Yeni Tweet Gönder
              </h2>
              <textarea
                value={tweetText}
                onChange={(e) => setTweetText(e.target.value)}
                placeholder="Ne düşünüyorsun?"
                style={{
                  width: "100%",
                  minHeight: "150px",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "16px",
                  resize: "vertical",
                  fontFamily: "inherit"
                }}
              />
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "12px"
              }}>
                <span style={{ fontSize: "14px", color: charCountColor, fontWeight: "bold" }}>
                  {charCount}/{MAX_LENGTH}
                </span>
                <button
                  onClick={handlePost}
                  disabled={loading || charCount > MAX_LENGTH || charCount === 0}
                  style={{
                    padding: "12px 32px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: loading || charCount > MAX_LENGTH || charCount === 0 ? "#374151" : "#3b82f6",
                    color: "white",
                    cursor: loading || charCount > MAX_LENGTH || charCount === 0 ? "not-allowed" : "pointer",
                    fontSize: "16px",
                    fontWeight: "600"
                  }}
                >
                  {loading ? "Gönderiliyor..." : "📤 Gönder"}
                </button>
              </div>
            </>
          )}

          {/* Reply Tab */}
          {activeTab === "reply" && (
            <>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
                Tweet'e Yanıt Ver
              </h2>
              <input
                type="text"
                value={tweetId}
                onChange={(e) => setTweetId(e.target.value)}
                placeholder="Tweet ID"
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "14px",
                  marginBottom: "12px"
                }}
              />
              <textarea
                value={tweetText}
                onChange={(e) => setTweetText(e.target.value)}
                placeholder="Yanıtınız..."
                style={{
                  width: "100%",
                  minHeight: "120px",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "16px",
                  resize: "vertical",
                  fontFamily: "inherit"
                }}
              />
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "12px"
              }}>
                <span style={{ fontSize: "14px", color: charCountColor, fontWeight: "bold" }}>
                  {charCount}/{MAX_LENGTH}
                </span>
                <button
                  onClick={handleReply}
                  disabled={loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId}
                  style={{
                    padding: "12px 32px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId ? "#374151" : "#3b82f6",
                    color: "white",
                    cursor: loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId ? "not-allowed" : "pointer",
                    fontSize: "16px",
                    fontWeight: "600"
                  }}
                >
                  {loading ? "Gönderiliyor..." : "💬 Yanıtla"}
                </button>
              </div>
            </>
          )}

          {/* Quote Tab */}
          {activeTab === "quote" && (
            <>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
                Tweet'i Alıntıla
              </h2>
              <input
                type="text"
                value={tweetId}
                onChange={(e) => setTweetId(e.target.value)}
                placeholder="Tweet ID"
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "14px",
                  marginBottom: "12px"
                }}
              />
              <textarea
                value={tweetText}
                onChange={(e) => setTweetText(e.target.value)}
                placeholder="Yorumunuz..."
                style={{
                  width: "100%",
                  minHeight: "120px",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "16px",
                  resize: "vertical",
                  fontFamily: "inherit"
                }}
              />
              <div style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                marginTop: "12px"
              }}>
                <span style={{ fontSize: "14px", color: charCountColor, fontWeight: "bold" }}>
                  {charCount}/{MAX_LENGTH}
                </span>
                <button
                  onClick={handleQuote}
                  disabled={loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId}
                  style={{
                    padding: "12px 32px",
                    borderRadius: "8px",
                    border: "none",
                    backgroundColor: loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId ? "#374151" : "#3b82f6",
                    color: "white",
                    cursor: loading || charCount > MAX_LENGTH || charCount === 0 || !tweetId ? "not-allowed" : "pointer",
                    fontSize: "16px",
                    fontWeight: "600"
                  }}
                >
                  {loading ? "Gönderiliyor..." : "🔖 Alıntıla"}
                </button>
              </div>
            </>
          )}

          {/* Like Tab */}
          {activeTab === "like" && (
            <>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
                Tweet'i Beğen
              </h2>
              <input
                type="text"
                value={tweetId}
                onChange={(e) => setTweetId(e.target.value)}
                placeholder="Tweet ID"
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "14px",
                  marginBottom: "16px"
                }}
              />
              <button
                onClick={handleLike}
                disabled={loading || !tweetId}
                style={{
                  width: "100%",
                  padding: "12px 32px",
                  borderRadius: "8px",
                  border: "none",
                  backgroundColor: loading || !tweetId ? "#374151" : "#ef4444",
                  color: "white",
                  cursor: loading || !tweetId ? "not-allowed" : "pointer",
                  fontSize: "16px",
                  fontWeight: "600"
                }}
              >
                {loading ? "İşleniyor..." : "❤️ Beğen"}
              </button>
            </>
          )}

          {/* Retweet Tab */}
          {activeTab === "retweet" && (
            <>
              <h2 style={{ fontSize: "18px", fontWeight: "bold", marginBottom: "16px" }}>
                Tweet'i Retweet Et
              </h2>
              <input
                type="text"
                value={tweetId}
                onChange={(e) => setTweetId(e.target.value)}
                placeholder="Tweet ID"
                style={{
                  width: "100%",
                  padding: "12px",
                  borderRadius: "8px",
                  border: "1px solid #475569",
                  backgroundColor: "#0f172a",
                  color: "white",
                  fontSize: "14px",
                  marginBottom: "16px"
                }}
              />
              <button
                onClick={handleRetweet}
                disabled={loading || !tweetId}
                style={{
                  width: "100%",
                  padding: "12px 32px",
                  borderRadius: "8px",
                  border: "none",
                  backgroundColor: loading || !tweetId ? "#374151" : "#10b981",
                  color: "white",
                  cursor: loading || !tweetId ? "not-allowed" : "pointer",
                  fontSize: "16px",
                  fontWeight: "600"
                }}
              >
                {loading ? "İşleniyor..." : "🔁 Retweet"}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default XOperations;
