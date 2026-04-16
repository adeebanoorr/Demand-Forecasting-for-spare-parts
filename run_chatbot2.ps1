# Start Chatbot 2.0 Integrated Environment

Write-Host "🚀 Launching Chatbot 2.0 Integrated Environment..." -ForegroundColor Cyan

# 0. Cleanup existing processes on ports 8001 and 5173
Write-Host "Cleaning up existing processes on ports 5173 and 8001..." -ForegroundColor Gray
$ports = 5174, 8001
foreach ($port in $ports) {
    $proc = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $proc.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Write-Host "Starting Backend API on port 8001..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd chatbot2.0; ..\myenv\Scripts\activate; python bot.py server"

# 2. Start Frontend
Write-Host "Starting Frontend Dev Server..." -ForegroundColor Green

# Check if node_modules exists, install if missing
if (-not (Test-Path "chatbot2.0\frontend\node_modules")) {
    Write-Host "node_modules missing. Running npm install..." -ForegroundColor Cyan
    Set-Location "chatbot2.0\frontend"
    npm install
    Set-Location "..\.."
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd chatbot2.0\frontend; npm run dev"

Write-Host "Done! Chatbot UI should be available at http://localhost:5174" -ForegroundColor Yellow
