# X-HIVE Backend Starter Script
# This script starts the Python backend in a hidden window

$WorkerPath = "C:\XHive\X-Hive\apps\worker"
$PythonCmd = "python -m app.main"

Write-Host "🚀 Starting X-HIVE Backend..." -ForegroundColor Green

# Check if backend is already running
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8765/health" -Method GET -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend already running" -ForegroundColor Green
        exit 0
    }
} catch {
    Write-Host "⚙️ Backend not running, starting..." -ForegroundColor Yellow
}

# Start backend in minimized window
$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "powershell.exe"
$processInfo.Arguments = "-NoExit -Command `"cd '$WorkerPath'; $PythonCmd`""
$processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
$processInfo.WorkingDirectory = $WorkerPath

$process = [System.Diagnostics.Process]::Start($processInfo)

Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verify backend started
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8765/health" -Method GET -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Backend started successfully!" -ForegroundColor Green
        Write-Host "📡 Orchestrator running" -ForegroundColor Cyan
        Write-Host "🤖 AI generation enabled" -ForegroundColor Cyan
        Write-Host "📅 Post schedule: 09:00, 14:00, 20:00" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Backend failed to start" -ForegroundColor Red
    exit 1
}
