# Study Pilot Dev Launcher
# Starts both FastAPI backend and Next.js frontend in separate PowerShell windows

$Root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"

Write-Host "Starting Study Pilot Backend (FastAPI on port 8000)..." -ForegroundColor Cyan
Start-Process powershell -WorkingDirectory $BackendDir -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\uvicorn app.main:app --reload --port 8000"

Write-Host "Starting Study Pilot Frontend (Next.js on port 3000)..." -ForegroundColor Green
Start-Process powershell -WorkingDirectory $FrontendDir -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "`nStudy Pilot launched!"
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend API Docs: http://127.0.0.1:8000/docs"
