@echo off
title AeroPredict Windows Launcher
echo ========================================================
echo   AeroPredict - Full Stack System Launcher
echo ========================================================
echo.
echo [1/2] Starting Flask Backend API on http://localhost:5000...
start "AeroPredict Backend" "%~dp0start_backend.bat"

echo.
echo Waiting 3 seconds for backend initialization...
timeout /t 3 /nobreak >nul

echo.
echo [2/2] Starting React Vite Frontend on http://localhost:5173...
start "AeroPredict Frontend" "%~dp0start_frontend.bat"

echo.
echo ========================================================
echo   AeroPredict is running!
echo   Open your browser at: http://localhost:5173
echo ========================================================
echo.
pause
