"""
chess_visualizer
================
Windows desktop overlay for real-time chess capture and tactical intelligence visualization.

Architecture
------------
theme.py         – Unified design system, semantic palette & arrow geometry
validator.py     – Board plausibility and integrity verification
transitions.py   – Board physical continuity, click artifact sanitization & turn derivation
capture.py       – High-DPI screen capture with DWM capture exclusion
recognition.py   – Board detection, sub-pixel grid snapping & piece recognition
chess_logic.py   – Legal capture, attack, and defense calculations
overlay.py       – Overlay runtime configuration
_overlay_widget  – Antialiased transparent Qt overlay drawing engine
_hud_panel       – Real-time floating tactical analytics HUD
_control_bar     – Minimalist floating control bar
_tray            – Windows system tray integration
main.py          – Application orchestrator & live tracking loop
"""

from chess_visualizer.theme import Theme, THEME
from chess_visualizer.validator import is_valid_recognized_board
from chess_visualizer.transitions import (
    determine_turn_from_move,
    sanitize_board_transition,
    generate_candidate_moves,
)
from chess_visualizer.overlay import OverlayConfig
from chess_visualizer._overlay_widget import OverlayWidget
from chess_visualizer._control_bar import ControlBar
from chess_visualizer._hud_panel import HUDPanel
from chess_visualizer.capture import ScreenCapture, set_window_capture_exclusion
from chess_visualizer.recognition import Recognizer, detect_chessboard_fullscreen, detect_chessboard_in_crop

__version__ = "0.2.0"
__author__ = "chess-analysis-overlay"

__all__ = [
    "Theme",
    "THEME",
    "is_valid_recognized_board",
    "determine_turn_from_move",
    "sanitize_board_transition",
    "generate_candidate_moves",
    "OverlayConfig",
    "OverlayWidget",
    "ControlBar",
    "HUDPanel",
    "ScreenCapture",
    "set_window_capture_exclusion",
    "Recognizer",
    "detect_chessboard_fullscreen",
    "detect_chessboard_in_crop",
]
