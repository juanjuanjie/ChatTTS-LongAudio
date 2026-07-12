@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist "logs" mkdir "logs"
call "%~dp0venv\Scripts\activate.bat"
python "%~dp0app.py" >"%~dp0logs\app_latest.log" 2>&1
