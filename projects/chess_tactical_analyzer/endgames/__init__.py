"""
projects.chess_tactical_analyzer.endgames
=========================================
0-ply endgame principles:
- Rule of the Square for runaway pawns
- King Opposition
- Passed Pawn Classification
"""

from .rules import (
    RunawayPawnInfo,
    OppositionInfo,
    PassedPawnInfo,
    is_endgame,
    is_passed_pawn,
    evaluate_runaway_passed_pawns,
    detect_king_opposition,
    classify_passed_pawns,
)

__all__ = [
    "RunawayPawnInfo",
    "OppositionInfo",
    "PassedPawnInfo",
    "is_endgame",
    "is_passed_pawn",
    "evaluate_runaway_passed_pawns",
    "detect_king_opposition",
    "classify_passed_pawns",
]
