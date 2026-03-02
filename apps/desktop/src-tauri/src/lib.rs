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

fn start_backend() {
    thread::spawn(|| {
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

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Start backend before starting Tauri
    start_backend();

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            check_worker_health,
            call_worker_api
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
