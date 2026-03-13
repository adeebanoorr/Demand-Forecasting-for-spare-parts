# KPCL Forecasting App - Start All Servers
# Run from project root: .\start.ps1

$PROJECT_ROOT = Split-Path -Parent $MyInvocation.MyCommand.Definition
$PYTHON = "$PROJECT_ROOT\myenv\Scripts\python.exe"
$WEBAPP_DIR = "$PROJECT_ROOT\frontend"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  KPCL Spare Parts Forecasting App" -ForegroundColor Cyan
Write-Host "  Starting all servers..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Dash Performance Dashboard (port 8050)
Write-Host "[1/3] Starting Dash Dashboard  -> http://localhost:8050" -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PROJECT_ROOT'; Write-Host 'Dash Dashboard - port 8050' -ForegroundColor Yellow; & '$PYTHON' backend/visualization/dashboard.py"

Start-Sleep -Seconds 2

# 2. FastAPI Backend (port 8000)
Write-Host "[2/3] Starting FastAPI Backend -> http://localhost:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$PROJECT_ROOT'; Write-Host 'FastAPI Backend - port 8000' -ForegroundColor Green; & '$PYTHON' -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 2

# 3. Vite React Frontend (port 5173)
Write-Host "[3/3] Starting React Frontend  -> http://localhost:5173" -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$WEBAPP_DIR'; Write-Host 'React Frontend - port 5173' -ForegroundColor Magenta; npx vite --host 0.0.0.0 --port 5173"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All servers launching in new windows!" -ForegroundColor Cyan
Write-Host "  Open: http://localhost:5173" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
