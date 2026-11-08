@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please double-click "install.bat" to set up prerequisites.
    pause
    exit /b 1
)

start "" pythonw main.py %*
if %ERRORLEVEL% NEQ 0 (
    python main.py %*
    pause
)
exit
