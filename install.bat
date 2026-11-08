@echo off
setlocal
title Chess Capture Visualizer - Setup

echo ========================================================
echo    Chess Capture Visualizer - One-Click Setup
echo ========================================================
echo.

REM 1. Check Python installation
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found on your system!
    echo.
    echo Please download and install Python (version 3.10 or newer) from:
    echo   https://www.python.org/downloads/
    echo.
    echo IMPORTANT: Make sure to check the box:
    echo   [x] "Add python.exe to PATH"
    echo during installation.
    echo.
    pause
    exit /b 1
)

echo [*] Python detected:
python --version
echo.

REM 2. Install dependencies
echo [*] Installing required packages...
python -m pip install --upgrade pip
python -m pip install -r "%~dp0requirements.txt"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Package installation failed. Please check your internet connection.
    pause
    exit /b 1
)

echo.
echo ========================================================
echo  [SUCCESS] All dependencies installed successfully!
echo ========================================================
echo.
echo Next steps:
echo   1. Open Chess.com or Lichess in your browser.
echo   2. Double-click "launch.bat" to start.
echo   3. The visualizer auto-detects your chessboard instantly!
echo.
pause
