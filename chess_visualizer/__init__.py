"""
chess_visualizer
================
Windows desktop overlay that shows legal capture arrows on any chess board.

Modules
-------
capture.py      – Screen capture (DXcam / mss / Pillow)
recognition.py  – Board and piece recognition → FEN
chess_logic.py  – Legal capture calculation for both colours
overlay.py      – Transparent Qt overlay window
main.py         – Entry point connecting all modules
"""

__version__ = "0.1.0"
__author__  = "chess-capture-visualizer"
