@echo off
REM Launch Chess Capture Visualizer silently without console window
cd /d "%~dp0"
start "" pythonw -m chess_visualizer %*
exit
