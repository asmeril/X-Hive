// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
async fn check_worker_health() -> Result<String, String> {
    let url = "http://127.0.0.1:8765/health";
    match reqwest::get(url).await {
        Ok(response) => match response.json::<serde_json::Value>().await {
            Ok(json) => serde_json::to_string_pretty(&json)
                .map_err(|e| format!("JSON serialize error: {}", e)),
            Err(e) => Err(format!("JSON parse error: {}", e)),
        },
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
        Ok(resp) => match resp.json::<serde_json::Value>().await {
            Ok(json) => serde_json::to_string_pretty(&json)
                .map_err(|e| format!("JSON error: {}", e)),
            Err(e) => Err(format!("Parse error: {}", e)),
        },
        Err(e) => Err(format!("Request failed: {}", e)),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
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
