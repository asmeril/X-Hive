import { useEffect, useState, useCallback, useRef } from "react";
import { invoke } from "@tauri-apps/api/core";
import { getVersion } from "@tauri-apps/api/app";
import "./App.css";
import XDaemonMonitor from "./components/XDaemonMonitor";
import XOperations from "./components/XOperations";
import ApprovalInterface from "./components/ApprovalInterface";
import OutcomeTracker from "./components/OutcomeTracker";
import SettingsPanel from "./components/SettingsPanel";

type ApiResponse = Record<string, unknown>;

type ProcInfo = { pid: number; type: "venv" | "global"; cmd: string };
type DiagResult = {
  timestamp?: string;
  python_count?: number;
  python_procs?: ProcInfo[];
  killed_pids?: number[];
  port_listeners?: number;
  api_ok?: boolean;
  api_error?: string;
  orchestrator_running?: boolean;
  scheduler_running?: boolean;
  fixes_applied?: string[];
  recent_errors?: string[];
  error?: string;
};

// ─── küçük yardımcı bileşenler ─────────────────────────────────────────────

function StatusCard({
  icon, label, value, ok, note,
}: {
  icon: string; label: string; value: string; ok: boolean | null; note?: string;
}) {
  const bg   = ok === null ? "#1e293b" : ok ? "#052e16" : "#450a0a";
  const bord = ok === null ? "#334155" : ok ? "#166534" : "#991b1b";
  const col  = ok === null ? "#94a3b8" : ok ? "#4ade80" : "#f87171";
  return (
    <div style={{
      backgroundColor: bg, border: `1px solid ${bord}`,
      borderRadius: "10px", padding: "16px 20px",
      display: "flex", flexDirection: "column", gap: "4px",
    }}>
      <div style={{ fontSize: "11px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {icon} {label}
      </div>
      <div style={{ fontSize: "20px", fontWeight: 700, color: col }}>{value}</div>
      {note && <div style={{ fontSize: "11px", color: "#64748b" }}>{note}</div>}
    </div>
  );
}

function App() {
  // genel state
  const [data, setData]     = useState<ApiResponse | null>(null);
  const [error, setError]   = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<
    "monitor" | "operations" | "approval" | "results" | "settings" | "health" | "lock"
  >("monitor");
  const [appVersion, setAppVersion] = useState<string>("-");

  // tanı state
  const [diagResult,  setDiagResult]  = useState<DiagResult | null>(null);
  const [diagLoading, setDiagLoading] = useState<boolean>(false);
  const [diagTime,    setDiagTime]    = useState<string | null>(null);
  const diagIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getVersion().then(setAppVersion).catch(() => setAppVersion("unknown"));
  }, []);

  // ─── Tanı & Onarım ───────────────────────────────────────────────────────
  const runDiagnostic = useCallback(async () => {
    setDiagLoading(true);
    try {
      const raw = await invoke<string>("system_diagnose_and_fix");
      const parsed: DiagResult = JSON.parse(raw);
      setDiagResult(parsed);
      setDiagTime(new Date().toLocaleTimeString("tr-TR"));
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      setDiagResult({ error: msg });
      setDiagTime(new Date().toLocaleTimeString("tr-TR"));
    } finally {
      setDiagLoading(false);
    }
  }, []);

  // Tab değiştikçe periyodik kontrolü başlat/durdur
  useEffect(() => {
    if (activeTab === "health") {
      // Tab açıldığında hemen tara
      runDiagnostic();
      // Her 60s'de otomatik tara
      diagIntervalRef.current = setInterval(runDiagnostic, 60_000);
    } else {
      if (diagIntervalRef.current) {
        clearInterval(diagIntervalRef.current);
        diagIntervalRef.current = null;
      }
    }
    return () => {
      if (diagIntervalRef.current) clearInterval(diagIntervalRef.current);
    };
  }, [activeTab, runDiagnostic]);

  // ─── Worker API ──────────────────────────────────────────────────────────
  const callWorkerApi = async (method: "GET" | "POST", endpoint: string) => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const response = await invoke<string>("call_worker_api", { method, endpoint });
      setData(JSON.parse(response) as ApiResponse);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  // ─── Durum sekmesi içeriği ───────────────────────────────────────────────
  const d = diagResult;
  const hasIssues =
    d && !d.error &&
    ((d.python_count ?? 0) > 1 ||
      !d.api_ok ||
      (d.port_listeners ?? 0) > 1 ||
      (d.recent_errors?.length ?? 0) > 0);
  const allGood =
    d && !d.error &&
    (d.python_count ?? 0) <= 1 &&
    d.api_ok === true &&
    (d.port_listeners ?? 0) <= 1 &&
    (d.recent_errors?.length ?? 0) === 0;

  const navBtn = (tab: typeof activeTab, label: string) => (
    <button
      onClick={() => setActiveTab(tab)}
      style={{
        padding: "8px 16px", borderRadius: "6px", border: "none",
        backgroundColor: activeTab === tab ? "#3b82f6" : "#374151",
        color: "white", fontSize: "14px", fontWeight: 600,
        cursor: "pointer", transition: "background-color 0.2s ease",
      }}
    >
      {label}
    </button>
  );

  return (
    <main style={{ backgroundColor: "#0f172a", minHeight: "100vh" }}>
      {/* ── Nav ── */}
      <div style={{
        backgroundColor: "#111827", borderBottom: "1px solid #374151",
        padding: "12px 24px", position: "sticky", top: 0, zIndex: 1000,
      }}>
        <div style={{ maxWidth: "1600px", margin: "0 auto" }}>
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <h1 style={{ margin: 0, marginRight: "24px", fontSize: "20px", fontWeight: 700, color: "#f3f4f6" }}>
              X-HIVE Kontrol Paneli
            </h1>
            <span style={{ color: "#94a3b8", fontSize: "12px", marginRight: "14px" }}>v{appVersion}</span>
            {navBtn("monitor",    "📊 İzleme")}
            {navBtn("approval",   "✅ Onay")}
            {navBtn("operations", "⚙️ İşlemler")}
            {navBtn("results",    "📈 Sonuçlar")}
            {navBtn("settings",   "⚙️ Ayarlar")}
            {navBtn("health",     "❤️ Durum")}
            {navBtn("lock",       "🔒 Kilit")}
          </div>
        </div>
      </div>

      {/* ── Content ── */}
      {activeTab === "monitor" ? (
        <XDaemonMonitor />
      ) : activeTab === "approval" ? (
        <ApprovalInterface />
      ) : activeTab === "operations" ? (
        <div style={{ padding: "24px", backgroundColor: "#0f172a", minHeight: "calc(100vh - 73px)" }}>
          <XOperations />
        </div>
      ) : activeTab === "results" ? (
        <OutcomeTracker />
      ) : activeTab === "settings" ? (
        <SettingsPanel />
      ) : (
        /* ════════ HEALTH + LOCK ════════ */
        <div style={{
          minHeight: "calc(100vh - 73px)", backgroundColor: "#0f172a",
          color: "#e5e7eb", padding: "24px",
        }}>
          <div style={{ maxWidth: "860px", margin: "0 auto" }}>

            {/* ─── HEALTH TAB ─── */}
            {activeTab === "health" && (
              <>
                {/* Başlık + buton */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "28px" }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: "26px", fontWeight: 700, color: "#f3f4f6" }}>
                      🔬 Sistem Tanı &amp; Onarım
                    </h2>
                    <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: "13px" }}>
                      Çakışan süreçleri ve sorunları tespit eder, otomatik onarır. Her 60s otomatik çalışır.
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <button
                      onClick={runDiagnostic}
                      disabled={diagLoading}
                      style={{
                        padding: "10px 22px", borderRadius: "8px", border: "none",
                        backgroundColor: diagLoading ? "#1d4ed8" : "#3b82f6",
                        color: "white", fontSize: "14px", fontWeight: 600,
                        cursor: diagLoading ? "not-allowed" : "pointer",
                        transition: "background-color 0.2s ease",
                      }}
                    >
                      {diagLoading ? "⏳ Taranıyor..." : "🔍 Şimdi Tara & Onar"}
                    </button>
                    {diagTime && (
                      <div style={{ marginTop: "6px", fontSize: "11px", color: "#475569" }}>
                        Son kontrol: {diagTime} · Otomatik: 60s
                      </div>
                    )}
                  </div>
                </div>

                {/* Genel sonuç banner */}
                {d && !d.error && (
                  <div style={{
                    padding: "12px 18px", borderRadius: "8px", marginBottom: "20px",
                    backgroundColor: allGood ? "#052e16" : hasIssues ? "#450a0a" : "#1e293b",
                    border: `1px solid ${allGood ? "#166534" : hasIssues ? "#991b1b" : "#334155"}`,
                    color: allGood ? "#4ade80" : hasIssues ? "#f87171" : "#94a3b8",
                    fontWeight: 600, fontSize: "15px",
                  }}>
                    {allGood
                      ? "✅ Her şey normal. Çalışan süreç sayısı uygun, API yanıt veriyor."
                      : (d.killed_pids?.length ?? 0) > 0
                        ? `🔧 ${d.killed_pids!.length} sorunlu süreç sonlandırıldı. Durum iyileştirildi.`
                        : "⚠️ Bazı sorunlar tespit edildi."}
                  </div>
                )}

                {/* Hata */}
                {d?.error && (
                  <div style={{
                    backgroundColor: "#45060a", border: "1px solid #991b1b",
                    color: "#fca5a5", padding: "14px 18px", borderRadius: "8px",
                    marginBottom: "20px", fontSize: "13px",
                  }}>
                    ❌ Tanı başarısız: {d.error}
                  </div>
                )}

                {/* Status kartları */}
                {d && !d.error && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "12px", marginBottom: "20px" }}>
                    <StatusCard
                      icon="🐍" label="Python Süreçleri"
                      value={`${d.python_count ?? "?"} adet`}
                      ok={(d.python_count ?? 0) === 1}
                      note={(d.python_count ?? 0) > 1 ? "Fazla süreç tespit edildi" : (d.python_count ?? 0) === 0 ? "Backend çalışmıyor!" : "Normal"}
                    />
                    <StatusCard
                      icon="🌐" label="API Durumu"
                      value={d.api_ok ? "Çalışıyor" : "Yanıt Yok"}
                      ok={d.api_ok ?? null}
                      note={d.api_ok ? "HTTP 200 OK" : d.api_error?.substring(0, 40)}
                    />
                    <StatusCard
                      icon="🔌" label="Port 8765"
                      value={`${d.port_listeners ?? "?"} listener`}
                      ok={(d.port_listeners ?? 0) === 1}
                      note={(d.port_listeners ?? 0) > 1 ? "Port çakışması!" : (d.port_listeners ?? 0) === 0 ? "Dinlenmiyor" : "Normal"}
                    />
                    <StatusCard
                      icon="🎯" label="Orchestrator"
                      value={d.orchestrator_running ? "Aktif" : d.api_ok ? "Durdu" : "—"}
                      ok={d.api_ok ? (d.orchestrator_running ?? false) : null}
                    />
                    <StatusCard
                      icon="⏰" label="Zamanlayıcı"
                      value={d.scheduler_running ? "Aktif" : d.api_ok ? "Durdu" : "—"}
                      ok={d.api_ok ? (d.scheduler_running ?? false) : null}
                    />
                    <StatusCard
                      icon="🔧" label="Bu Taramada Onarılan"
                      value={`${d.killed_pids?.length ?? 0} süreç`}
                      ok={(d.killed_pids?.length ?? 0) === 0}
                      note={(d.killed_pids?.length ?? 0) > 0 ? `PID: ${d.killed_pids!.join(", ")}` : "Sorun yok"}
                    />
                  </div>
                )}

                {/* Süreç detayı */}
                {d && !d.error && (d.python_procs?.length ?? 0) > 0 && (
                  <div style={{
                    backgroundColor: "#1e293b", border: "1px solid #334155",
                    borderRadius: "10px", padding: "16px 20px", marginBottom: "16px",
                  }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#94a3b8", marginBottom: "10px", textTransform: "uppercase" }}>
                      🐍 Aktif Python Süreçleri
                    </div>
                    {d.python_procs!.map((p) => (
                      <div key={p.pid} style={{
                        display: "flex", alignItems: "center", gap: "10px",
                        padding: "6px 0", borderBottom: "1px solid #1f2d40", fontSize: "12px",
                      }}>
                        <span style={{
                          backgroundColor: p.type === "venv" ? "#052e16" : "#450a0a",
                          color: p.type === "venv" ? "#4ade80" : "#f87171",
                          padding: "2px 8px", borderRadius: "4px", fontWeight: 700, minWidth: "50px", textAlign: "center",
                        }}>
                          {p.type.toUpperCase()}
                        </span>
                        <span style={{ color: "#64748b" }}>PID {p.pid}</span>
                        <span style={{ color: "#94a3b8", fontFamily: "monospace", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {p.cmd}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Yapılan onarımlar */}
                {d && (d.fixes_applied?.length ?? 0) > 0 && (
                  <div style={{
                    backgroundColor: "#052e16", border: "1px solid #166534",
                    borderRadius: "10px", padding: "16px 20px", marginBottom: "16px",
                  }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#4ade80", marginBottom: "10px", textTransform: "uppercase" }}>
                      🔧 Uygulanan Onarımlar
                    </div>
                    {d.fixes_applied!.map((fix, i) => (
                      <div key={i} style={{ fontSize: "13px", color: "#86efac", padding: "3px 0" }}>• {fix}</div>
                    ))}
                  </div>
                )}

                {/* Son hatalar */}
                {d && (d.recent_errors?.length ?? 0) > 0 && (
                  <div style={{
                    backgroundColor: "#1c1a10", border: "1px solid #854d0e",
                    borderRadius: "10px", padding: "16px 20px",
                  }}>
                    <div style={{ fontSize: "12px", fontWeight: 700, color: "#fbbf24", marginBottom: "10px", textTransform: "uppercase" }}>
                      📋 Son Log Hataları (bilgi amaçlı)
                    </div>
                    {d.recent_errors!.map((err, i) => (
                      <div key={i} style={{
                        fontSize: "11px", color: "#fde68a", padding: "3px 0",
                        fontFamily: "monospace", wordBreak: "break-all",
                      }}>
                        {err}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}

            {/* ─── LOCK TAB ─── */}
            {activeTab === "lock" && (
              <>
                <h2 style={{ fontSize: "26px", fontWeight: 700, marginBottom: "10px", color: "#f3f4f6" }}>
                  🔒 Kilit Yönetimi
                </h2>
                <p style={{ marginBottom: "24px", color: "#94a3b8", fontSize: "13px" }}>
                  Daemon oturum kilidini al, bırak veya durumunu kontrol et
                </p>
                <div style={{ display: "flex", gap: "12px" }}>
                  {[
                    { label: "🔒 Kilidi Al",         color: "#22c55e",  method: "POST" as const, ep: "/lock/acquire" },
                    { label: "🔓 Kilidi Bırak",      color: "#ef4444",  method: "POST" as const, ep: "/lock/release" },
                    { label: "🔍 Durumu Kontrol Et", color: "#3b82f6",  method: "GET"  as const, ep: "/lock/status"  },
                  ].map(({ label, color, method, ep }) => (
                    <button
                      key={ep}
                      onClick={() => callWorkerApi(method, ep)}
                      disabled={loading}
                      style={{
                        flex: 1, padding: "14px 20px", borderRadius: "8px", border: "none",
                        backgroundColor: loading ? "#374151" : color,
                        color: "white", fontSize: "15px", fontWeight: 600,
                        cursor: loading ? "not-allowed" : "pointer",
                        transition: "background-color 0.2s ease",
                      }}
                    >
                      {loading ? "⏳" : label}
                    </button>
                  ))}
                </div>

                {error && (
                  <div style={{
                    backgroundColor: "#7f1d1d", border: "1px solid #ef4444",
                    color: "#fecaca", padding: "12px", borderRadius: "8px",
                    marginTop: "16px", textAlign: "center", fontSize: "13px",
                  }}>
                    {error}
                  </div>
                )}
                {data && (
                  <pre style={{
                    backgroundColor: "#0b1020", border: "1px solid #1f2937",
                    borderRadius: "8px", padding: "16px", marginTop: "16px",
                    overflowX: "auto", fontFamily: "monospace", fontSize: "12px",
                    lineHeight: 1.6, whiteSpace: "pre-wrap", wordBreak: "break-word", color: "#e2e8f0",
                  }}>
                    {JSON.stringify(data, null, 2)}
                  </pre>
                )}
              </>
            )}

          </div>
        </div>
      )}
    </main>
  );
}

export default App;
