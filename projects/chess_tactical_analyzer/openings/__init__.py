"""
projects.chess_tactical_analyzer.openings
=========================================
Opening identification, ECO classification, and opening trap detection.
"""

from .book import (
    OpeningInfo,
    identify_opening,
    identify_opening_from_moves,
    is_opening_phase,
)
from .traps import OpeningTrap, detect_opening_traps

__all__ = [
    "OpeningInfo",
    "identify_opening",
    "identify_opening_from_moves",
    "is_opening_phase",
    "OpeningTrap",
    "detect_opening_traps",
]
