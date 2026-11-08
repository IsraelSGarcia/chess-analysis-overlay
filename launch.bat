@echo off
setlocal
cd /d "%~dp0"
title Chess Analysis Overlay

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please download and install Python version 3.10 or newer from https://www.python.org/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

python -c "import chess, PySide6, cv2, mss, PIL, numpy, chessvision, keyboard" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing or updating required dependencies...
    python -m pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

echo [*] Starting Chess Analysis Overlay...
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
