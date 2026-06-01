@echo off
echo Iniciando MediPlus...

start "Backend - MediPlus" cmd /k "cd /d %~dp0backend && ..\venv\Scripts\python.exe -m uvicorn api:app --reload --port 8000"

timeout /t 3 /nobreak >nul

start "Frontend - MediPlus" cmd /k "cd /d %~dp0frontend-react && npm run dev"

timeout /t 4 /nobreak >nul

start http://localhost:5173
