@echo off
title AeroPredict - Backend Server (Flask)
cd /d "%~dp0backend"
echo ========================================================
echo   Starting AeroPredict Flask Backend API Server...
echo ========================================================
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Python virtual environment not found in backend\venv.
    echo [INFO] Creating virtual environment and installing dependencies...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)
python app.py
pause
