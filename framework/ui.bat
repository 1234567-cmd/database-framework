@echo off
rem Opens the dbintel web interface in your browser. Usage: ui.bat [--port 8765] [--no-open]
setlocal
cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" -m dbintel ui %*
