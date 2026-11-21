@echo off
title AeroPredict - Frontend Client (React Vite)
cd /d "%~dp0frontend"
echo ========================================================
echo   Starting AeroPredict React Frontend (Vite)...
echo ========================================================
if not exist "node_modules\" (
    echo [INFO] node_modules not found. Running npm install...
    call npm install
)
call npm run dev
pause
