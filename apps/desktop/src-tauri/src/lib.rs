// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use std::path::{Path, PathBuf};

#[cfg(target_os = "windows")]
use std::os::windows::process::CommandExt;

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
        let prod = PathBuf::from(appdata).join("XHive").join("worker");
        if prod.join("app").join("main.py").exists() {
            println!("📁 Worker path (production): {:?}", prod);
            return prod;
        }
    }
    // Dev fallback
    let dev = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .parent().unwrap()
        .parent().unwrap()
        .join("worker");
    println!("📁 Worker path (dev): {:?}", dev);
    dev
}

fn resolve_python_executable(worker_path: &Path) -> (String, Vec<String>) {
    // Check both .venv and venv directories - validate fastapi is installed
    for venv_dir in &[".venv", "venv"] {
        let venv_python = worker_path.join(venv_dir).join("Scripts").join("python.exe");
        if venv_python.exists() {
            let path_str = venv_python.to_string_lossy().to_string();
            if validate_python_has_fastapi(&path_str, worker_path) {
                println!("✅ Found working Python venv: {}", path_str);
                return (path_str, vec![]);
            } else {
                println!("⚠️ Python venv {} exists but fastapi not installed, skipping", venv_dir);
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
                        println!("🔍 Found system Python: {}", path_str);
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
                println!("✅ Backend already running");
                return;
            }
        }

        println!("🚀 Starting X-HIVE Backend...");

        // Resolve worker directory (production: AppData, dev: repo)
        let worker_path = resolve_worker_path();

        #[cfg(target_os = "windows")]
        {
            let (python_executable, mut python_prefix_args) = resolve_python_executable(&worker_path);
            python_prefix_args.push("-m".to_string());
            python_prefix_args.push("app.main".to_string());

            println!("🐍 Python executable: {}", python_executable);
            println!("📋 Args: {:?}", python_prefix_args);

            // Write a log file for debugging
            let log_file = worker_path.join("backend_stdout.log");
            let err_file = worker_path.join("backend_stderr.log");
            let stdout_file = std::fs::File::create(&log_file)
                .unwrap_or_else(|e| panic!("Cannot create stdout log: {}", e));
            let stderr_file = std::fs::File::create(&err_file)
                .unwrap_or_else(|e| panic!("Cannot create stderr log: {}", e));

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
                Ok(child) => println!("✅ Backend process spawned with PID: {}", child.id()),
                Err(e) => {
                    eprintln!("❌ Failed to spawn backend: {}", e);
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
        println!("⏳ Waiting for backend...");
        for i in 0..60 {
            thread::sleep(Duration::from_secs(1));
            if let Ok(resp) = reqwest::blocking::get("http://127.0.0.1:8765/health") {
                if resp.status().is_success() {
                    println!("✅ Backend started successfully after {}s!", i);
                    return;
                }
            }
            if i % 5 == 0 {
                println!("⏳ Still waiting... ({}/60s)", i);
            }
        }
        eprintln!("❌ Backend failed to start after 60s - check backend_stderr.log");
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
async fn call_worker_api(method: String, endpoint: String) -> Result<String, String> {
    let url = format!("http://127.0.0.1:8765{}", endpoint);
    let client = reqwest::Client::new();

    let response = match method.as_str() {
        "GET" => client.get(&url).send().await,
        "POST" => client.post(&url).send().await,
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
