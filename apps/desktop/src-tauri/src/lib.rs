// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use std::path::{Path, PathBuf};
use std::io::Write;

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

/// Write a debug message to %LOCALAPPDATA%\XHive\tauri_debug.log
/// This is essential because GUI apps have no visible stdout/stderr.
fn debug_log(msg: &str) {
    let log_path = if let Ok(appdata) = std::env::var("LOCALAPPDATA") {
        let dir = PathBuf::from(&appdata).join("XHive");
        let _ = std::fs::create_dir_all(&dir);
        dir.join("tauri_debug.log")
    } else {
        PathBuf::from("tauri_debug.log")
    };
    if let Ok(mut file) = std::fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&log_path)
    {
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();
        let _ = writeln!(file, "[{}] {}", timestamp, msg);
    }
}

fn validate_python_has_fastapi(python_path: &str, worker_path: &Path) -> bool {
    Command::new(python_path)
        .args(["-c", "import fastapi"])
        .current_dir(worker_path)
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

/// Resolve the worker directory.
/// Production: %LOCALAPPDATA%\XHive\worker
/// Dev fallback: <repo>/apps/worker  (CARGO_MANIFEST_DIR based)
fn resolve_worker_path() -> PathBuf {
    // Production path first
    if let Ok(appdata) = std::env::var("LOCALAPPDATA") {
        let prod = PathBuf::from(&appdata).join("XHive").join("worker");
        let main_py = prod.join("app").join("main.py");
        debug_log(&format!("Checking production path: {:?}", prod));
        debug_log(&format!("main.py exists: {}", main_py.exists()));
        if main_py.exists() {
            debug_log(&format!("Worker path (production): {:?}", prod));
            return prod;
        }
        // main.py yoksa bile worker klasörü varsa production'dayız
        if prod.exists() {
            debug_log(&format!("Worker dir exists but main.py missing — using production path anyway: {:?}", prod));
            return prod;
        }
        debug_log(&format!("LOCALAPPDATA={}, prod dir does not exist: {:?}", appdata, prod));
        // Release build'te dev fallback'e inme: kurulu uygulama her zaman LocalAppData worker kullanmalı.
        if !cfg!(debug_assertions) {
            debug_log("Release mode: forcing LocalAppData worker path");
            return prod;
        }
    } else {
        debug_log("LOCALAPPDATA env var not found!");
    }
    // Dev fallback
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap()
        .parent().unwrap()
        .join("worker");
    debug_log(&format!("Worker path (dev fallback): {:?}", dev));
    dev
}

fn resolve_python_executable(worker_path: &Path) -> (String, Vec<String>) {
    // Check both .venv and venv directories - validate fastapi is installed
    for venv_dir in &[".venv", "venv"] {
        let venv_python = worker_path.join(venv_dir).join("Scripts").join("python.exe");
        if venv_python.exists() {
            let path_str = venv_python.to_string_lossy().to_string();
            if validate_python_has_fastapi(&path_str, worker_path) {
                debug_log(&format!("Found working Python venv: {}", path_str));
                return (path_str, vec![]);
            } else {
                debug_log(&format!("Python venv {} exists but fastapi not installed, skipping", venv_dir));
            }
        }
    }

    if let Ok(local_app_data) = std::env::var("LOCALAPPDATA") {
        let python_root = PathBuf::from(local_app_data).join("Programs").join("Python");
        if python_root.exists() {
            if let Ok(entries) = std::fs::read_dir(&python_root) {
                let mut candidates: Vec<_> = entries.flatten().collect();
                // Sort to prefer newer Python versions (Python311 > Python310 etc.)
                candidates.sort_by(|a, b| b.file_name().cmp(&a.file_name()));
                for entry in candidates {
                    let candidate = entry.path().join("python.exe");
                    if candidate.exists() {
                        let path_str = candidate.to_string_lossy().to_string();
                        debug_log(&format!("Found system Python: {}", path_str));
                        return (path_str, vec![]);
                    }
                }
            }
        }
    }

    if let Ok(output) = Command::new("where").arg("python").output() {
        if output.status.success() {
            if let Ok(stdout) = String::from_utf8(output.stdout) {
                if let Some(first_path) = stdout
                    .lines()
                    .map(|line| line.trim())
                    .find(|line| {
                        if line.is_empty() {
                            return false;
                        }
                        if !Path::new(line).exists() {
                            return false;
                        }
                        if line.to_ascii_lowercase().contains("windowsapps") {
                            return false;
                        }
                        Command::new(line)
                            .arg("--version")
                            .stdout(Stdio::null())
                            .stderr(Stdio::null())
                            .status()
                            .map(|status| status.success())
                            .unwrap_or(false)
                    })
                {
                    return (first_path.to_string(), vec![]);
                }
            }
        }
    }

    if Command::new("py")
        .args(["-3", "--version"])
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .status()
        .is_ok()
    {
        return ("py".to_string(), vec!["-3".to_string()]);
    }

    let absolute_py_launcher = Path::new("C:\\Windows\\py.exe");
    if absolute_py_launcher.exists() {
        return (
            absolute_py_launcher.to_string_lossy().to_string(),
            vec!["-3".to_string()],
        );
    }

    ("python".to_string(), vec![])
}

#[cfg(target_os = "windows")]
fn cleanup_backend_processes() {
        let ps_script = r#"
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" |
    Where-Object {
        $_.CommandLine -and (
            $_.CommandLine -match '-m app\.main' -or
            $_.CommandLine -match 'run_approval_bot\.py' -or
            $_.CommandLine -match 'telegram_bot\.py'
        )
    } |
    ForEach-Object {
        try { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
"#;

        let result = Command::new("powershell.exe")
                .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script])
                .creation_flags(0x08000000)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .status();

        match result {
                Ok(status) => debug_log(&format!("cleanup_backend_processes finished: {}", status)),
                Err(e) => debug_log(&format!("cleanup_backend_processes failed: {}", e)),
        }
}

#[cfg(not(target_os = "windows"))]
fn cleanup_backend_processes() {}

fn start_backend() {
    thread::spawn(|| {
        // Ensure no stale/duplicate backend processes remain
        cleanup_backend_processes();
        thread::sleep(Duration::from_millis(500));

        // Check if backend is already running
        let check = reqwest::blocking::get("http://127.0.0.1:8765/health");
        if let Ok(resp) = check {
            if resp.status().is_success() {
                debug_log("Backend already running");
                return;
            }
        }

        debug_log("Starting X-HIVE Backend...");

        // Resolve worker directory (production: AppData, dev: repo)
        let worker_path = resolve_worker_path();

        #[cfg(target_os = "windows")]
        {
            let (python_executable, mut python_prefix_args) = resolve_python_executable(&worker_path);
            python_prefix_args.push("-m".to_string());
            python_prefix_args.push("app.main".to_string());

            debug_log(&format!("Python executable: {}", python_executable));
            debug_log(&format!("Worker path: {:?}", worker_path));
            debug_log(&format!("Args: {:?}", python_prefix_args));

            // Worker path yoksa oluştur
            if let Err(e) = std::fs::create_dir_all(&worker_path) {
                debug_log(&format!("Cannot create worker dir {:?}: {}", worker_path, e));
                return;
            }

            // Release build'te app/main.py yoksa net hata ver (sessizce repo fallback olmasın)
            if !cfg!(debug_assertions) {
                let entrypoint = worker_path.join("app").join("main.py");
                if !entrypoint.exists() {
                    debug_log(&format!(
                        "Backend start aborted: missing {:?}. Installer worker files are incomplete.",
                        entrypoint
                    ));
                    return;
                }
            }

            // Log dosyalarını oluştur — panic yerine graceful hata
            let log_file = worker_path.join("backend_stdout.log");
            let err_file = worker_path.join("backend_stderr.log");

            let stdout_file = match std::fs::File::create(&log_file) {
                Ok(f) => f,
                Err(e) => {
                    debug_log(&format!("Cannot create stdout log {:?}: {}", log_file, e));
                    return;
                }
            };
            let stderr_file = match std::fs::File::create(&err_file) {
                Ok(f) => f,
                Err(e) => {
                    debug_log(&format!("Cannot create stderr log {:?}: {}", err_file, e));
                    return;
                }
            };

            match Command::new(&python_executable)
                .args(&python_prefix_args)
                .current_dir(&worker_path)
                .creation_flags(
                    0x08000000 | // CREATE_NO_WINDOW
                    0x00000200   // CREATE_NEW_PROCESS_GROUP
                )
                .stdin(Stdio::null())
                .stdout(stdout_file)
                .stderr(stderr_file)
                .spawn()
            {
                Ok(child) => debug_log(&format!("Backend process spawned with PID: {}", child.id())),
                Err(e) => {
                    debug_log(&format!("Failed to spawn backend: {}", e));
                    return;
                }
            }
        }

        #[cfg(not(target_os = "windows"))]
        {
            Command::new("python3")
                .args(&["-m", "app.main"])
                .current_dir(worker_path)
                .stdout(Stdio::null())
                .stderr(Stdio::null())
                .spawn()
                .expect("Failed to start backend");
        }

        // Wait for backend to start
        debug_log("Waiting for backend...");
        for i in 0..60 {
            thread::sleep(Duration::from_secs(1));
            if let Ok(resp) = reqwest::blocking::get("http://127.0.0.1:8765/health") {
                if resp.status().is_success() {
                    debug_log(&format!("Backend started successfully after {}s!", i));
                    return;
                }
            }
            if i % 5 == 0 {
                debug_log(&format!("Still waiting... ({}/60s)", i));
            }
        }
        debug_log("Backend failed to start after 60s - check backend_stderr.log");
    });
}

#[tauri::command]
fn shutdown_backend_processes() -> Result<String, String> {
    cleanup_backend_processes();
    Ok("backend processes cleaned".to_string())
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn check_worker_health() -> Result<String, String> {
    let url = "http://127.0.0.1:8765/health";
    match reqwest::get(url).await {
        Ok(resp) => {
            let bytes = resp.bytes().await.map_err(|e| format!("Body read error: {}", e))?;
            let text = String::from_utf8_lossy(&bytes).to_string();
            match serde_json::from_str::<serde_json::Value>(&text) {
                Ok(json) => serde_json::to_string_pretty(&json)
                    .map_err(|e| format!("JSON serialize error: {}", e)),
                Err(_) => {
                    let wrapped = serde_json::json!({ "status": "ok", "message": text });
                    serde_json::to_string_pretty(&wrapped)
                        .map_err(|e| format!("JSON wrap error: {}", e))
                }
            }
        }
        Err(e) => Err(format!("Request failed: {}", e)),
    }
}

#[tauri::command]
async fn call_worker_api(method: String, endpoint: String, body: Option<String>) -> Result<String, String> {
    let url = format!("http://127.0.0.1:8765{}", endpoint);
    let client = reqwest::Client::new();

    let response = match method.as_str() {
        "GET" => client.get(&url).send().await,
        "POST" => {
            let req = client.post(&url);
            if let Some(ref json_body) = body {
                req.header("Content-Type", "application/json")
                   .body(json_body.clone())
                   .send().await
            } else {
                req.send().await
            }
        }
        _ => return Err("Unsupported method".to_string()),
    };

    match response {
        Ok(resp) => {
            let status = resp.status();
            // Read raw bytes first to avoid charset decoding issues
            let bytes = resp.bytes().await.map_err(|e| format!("Body read error: {}", e))?;
            let text = String::from_utf8_lossy(&bytes).to_string();

            if !status.is_success() {
                // Return error with status code + body for debugging
                return Err(format!("HTTP {}: {}", status.as_u16(), text));
            }

            // Try to parse as JSON, fall back to plain text wrapped in JSON
            match serde_json::from_str::<serde_json::Value>(&text) {
                Ok(json) => serde_json::to_string_pretty(&json)
                    .map_err(|e| format!("JSON serialize error: {}", e)),
                Err(_) => {
                    // Backend returned non-JSON (e.g. plain text) — wrap it
                    let wrapped = serde_json::json!({ "status": "ok", "message": text });
                    serde_json::to_string_pretty(&wrapped)
                        .map_err(|e| format!("JSON wrap error: {}", e))
                }
            }
        }
        Err(e) => Err(format!("Request failed: {}", e)),
    }
}

/// Sistem tanı ve otomatik onarım: çakışan Python süreçlerini/portları tespit edip temizle.
/// Frontend'den çağrılır, JSON rapor döndürür.
#[tauri::command]
fn system_diagnose_and_fix() -> String {
    let ps_script = r#"
$r = @{
    timestamp       = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    python_procs    = @()
    killed_pids     = @()
    port_listeners  = 0
    api_ok          = $false
    api_error       = ""
    fixes_applied   = @()
}

# 1. Tüm app.main Python süreçleri
$all = Get-CimInstance Win32_Process | Where-Object {
    $_.Name -like "python*" -and $_.CommandLine -match "-m app\.main"
}
$r.python_procs = @($all | ForEach-Object {
    @{
        pid  = [int]$_.ProcessId
        type = if ($_.CommandLine -match "\.venv") { "venv" } else { "global" }
        cmd  = $_.CommandLine.Substring(0, [Math]::Min($_.CommandLine.Length, 90))
    }
})
$r.python_count = $all.Count

# 2. Global (zombie) süreçleri öldür
$global_procs = @($all | Where-Object { $_.CommandLine -notmatch "\.venv" })
foreach ($proc in $global_procs) {
    Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
    $r.killed_pids += [int]$proc.ProcessId
    $r.fixes_applied += "Killed global Python PID $($proc.ProcessId)"
}

# 3. Fazla venv süreci varsa (birden fazla) en eskisini öldür
$venv_procs = @($all | Where-Object { $_.CommandLine -match "\.venv" })
if ($venv_procs.Count -gt 1) {
    $sorted = $venv_procs | Sort-Object ProcessId -Descending
    $to_kill = $sorted | Select-Object -Skip 1
    foreach ($proc in $to_kill) {
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        $r.killed_pids += [int]$proc.ProcessId
        $r.fixes_applied += "Killed duplicate venv Python PID $($proc.ProcessId)"
    }
}

# 4. Port 8765 listener sayısı
$r.port_listeners = @(netstat -ano | Select-String ":8765\s.*LISTEN").Count

# 5. API sağlık kontrolü
try {
    $resp = Invoke-RestMethod "http://localhost:8765/system/status" -TimeoutSec 3
    $r.api_ok = $true
    $r.orchestrator_running = $resp.services.orchestrator.running
    $r.scheduler_running    = $resp.services.scheduler.running
} catch {
    $r.api_ok    = $false
    $r.api_error = $_.Exception.Message -replace "`n"," "
}

# 6. Son stderr log (hata satırlarını özetle)
$stderr_path = "$env:LOCALAPPDATA\XHive\worker\backend_stderr.log"
if (Test-Path $stderr_path) {
    $last_errors = Get-Content $stderr_path -Tail 80 |
        Select-String "Conflict|KeyError|ImportError|CRITICAL|ERROR:" |
        Select-Object -Last 5 |
        ForEach-Object { $_.Line.Trim() }
    $r.recent_errors = @($last_errors)
} else {
    $r.recent_errors = @()
}

$r | ConvertTo-Json -Depth 4
"#;

    #[cfg(target_os = "windows")]
    {
        match Command::new("powershell.exe")
            .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script])
            .creation_flags(0x08000000)
            .output()
        {
            Ok(output) => {
                let stdout = String::from_utf8_lossy(&output.stdout).to_string();
                if stdout.trim().is_empty() {
                    r#"{"error":"Tanı scripti çıktı vermedi"}"#.to_string()
                } else {
                    stdout.trim().to_string()
                }
            }
            Err(e) => format!(r#"{{"error":"Script başlatılamadı: {}"}}"#, e),
        }
    }
    #[cfg(not(target_os = "windows"))]
    {
        r#"{"error":"Bu özellik yalnızca Windows'ta desteklenir"}"#.to_string()
    }
}

/// Arka planda her 90 saniyede bir sessizce zombie Python süreçlerini temizle.
fn start_background_health_monitor() {
    thread::spawn(|| {
        // İlk çalıştırmayı biraz geciktir (worker başlasın)
        thread::sleep(Duration::from_secs(75));
        loop {
            #[cfg(target_os = "windows")]
            {
                let ps = r#"
Get-CimInstance Win32_Process | Where-Object {
    $_.Name -like "python*" -and $_.CommandLine -match "-m app\.main"
} | ForEach-Object {
    $is_global = $_.CommandLine -notmatch "\.venv"
    if ($is_global) { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
# Fazla venv süreci
$venv = @(Get-CimInstance Win32_Process | Where-Object {
    $_.Name -like "python*" -and $_.CommandLine -match "\.venv.*-m app\.main"
})
if ($venv.Count -gt 1) {
    $venv | Sort-Object ProcessId -Descending | Select-Object -Skip 1 |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}
"#;
                let _ = Command::new("powershell.exe")
                    .args(["-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps])
                    .creation_flags(0x08000000)
                    .stdout(Stdio::null())
                    .stderr(Stdio::null())
                    .status();
            }
            thread::sleep(Duration::from_secs(90));
        }
    });
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Start backend before starting Tauri
    start_backend();

    // Arka plan sağlık monitörü: her 90s'de zombie süreçleri temizle
    start_background_health_monitor();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            check_worker_health,
            call_worker_api,
            shutdown_backend_processes,
            system_diagnose_and_fix
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
