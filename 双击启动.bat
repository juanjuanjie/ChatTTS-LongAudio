@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"

:: Stop existing app.py process to avoid port conflict
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

set "PYTHON_CMD="
py -3.11 --version >nul 2>&1 && set "PYTHON_CMD=py -3.11"
if not defined PYTHON_CMD py -3.10 --version >nul 2>&1 && set "PYTHON_CMD=py -3.10"
if not defined PYTHON_CMD py --version >nul 2>&1 && set "PYTHON_CMD=py"
if not defined PYTHON_CMD python --version >nul 2>&1 && set "PYTHON_CMD=python"

if not defined PYTHON_CMD (
    echo [ERROR] Python 3.10 or 3.11 was not found.
    echo Please install Python 3.10/3.11, then double-click this file again.
    pause
    exit /b 1
)

echo Using Python command: %PYTHON_CMD%
%PYTHON_CMD% "%~dp0bootstrap_run.py"
if errorlevel 1 (
    echo.
    echo [ERROR] Startup failed. See logs\app_latest.log if it exists.
    pause
    exit /b 1
)
