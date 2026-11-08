"""
core.chess_rules
================
Chess rules enforcement, board validation, continuity verification, and turn inference.
"""

from .validator import is_valid_recognized_board
from .transitions import determine_turn_from_move, sanitize_board_transition

__all__ = [
    "is_valid_recognized_board",
    "determine_turn_from_move",
    "sanitize_board_transition",
]
