# KPCL Forecasting App - Start Local Development Environment

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $PROJECT_ROOT

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KPCL Forecasting - Server Launcher" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. Start Python Backend & Dashboard
Write-Host "Launching Backend API and Analytics Dashboard..." -ForegroundColor Yellow
$PYTHON_CMD = "python"
if (Test-Path "$PROJECT_ROOT\myenv\Scripts\python.exe") {
    $PYTHON_CMD = "$PROJECT_ROOT\myenv\Scripts\python.exe"
}

Start-Process powershell.exe -ArgumentList "-NoExit -Command `"& $PYTHON_CMD app.py`"" -WindowStyle Normal

# 2. Start React Frontend
Write-Host "Launching React Frontend..." -ForegroundColor Yellow
if (Test-Path "$PROJECT_ROOT\frontend") {
    Start-Process powershell.exe -ArgumentList "-NoExit -Command `"cd '$PROJECT_ROOT\frontend'; npm run dev`"" -WindowStyle Normal
}

Write-Host ""
Write-Host "Servers are starting in new windows." -ForegroundColor Green
Write-Host "You can view the app at:" -ForegroundColor White
Write-Host "-> Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host "-> Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "-> Dash:     http://localhost:8000/analytics" -ForegroundColor Cyan
Write-Host ""
