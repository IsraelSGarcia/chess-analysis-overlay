@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please download and install Python (3.10+) from https://www.python.org/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b 1
)

python -c "import chess, PySide6, cv2, mss, PIL, numpy" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [*] Installing required dependencies...
    python -m pip install -r "%~dp0requirements.txt"
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Dependency installation failed.
        pause
        exit /b 1
    )
)

start "" pythonw main.py %*
if %ERRORLEVEL% NEQ 0 (
    python main.py %*
    pause
)
exit
