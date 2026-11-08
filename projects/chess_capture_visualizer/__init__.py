"""
projects.chess_capture_visualizer
=================================
Specialized analytical subproject responsible for identifying and visualizing
legal captures, attack rays, and defense relationships for both players.
"""

from .captures import (
    CaptureMove,
    MoveArrow,
    get_legal_captures,
    get_all_captures,
    get_all_captures_dict,
    get_all_moves,
    get_legal_moves,
)

__all__ = [
    "CaptureMove",
    "MoveArrow",
    "get_legal_captures",
    "get_all_captures",
    "get_all_captures_dict",
    "get_all_moves",
    "get_legal_moves",
]
