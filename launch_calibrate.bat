@echo off
REM Launch with interactive board calibration without console window
cd /d "%~dp0"
start "" pythonw -m chess_visualizer --calibrate %*
exit
