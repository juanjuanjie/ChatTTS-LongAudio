@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"

:: 关闭已存在的 app.py 进程，避免端口被旧版本占用
powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*app.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

call "%~dp0venv\Scripts\activate.bat"
python -u app.py >> "%~dp0logs\app_latest.log" 2>&1
