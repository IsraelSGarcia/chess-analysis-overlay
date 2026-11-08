"""
values.py
=========
Standard piece values, material evaluation constants, and exchange classifications.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict
import chess


# Standard piece values in centipawns (1 pawn = 100 centipawns)
PIECE_VALUES: Dict[chess.PieceType, int] = {
    chess.PAWN: 100,
    chess.KNIGHT: 305,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 20000,
}

# Short display names
PIECE_NAMES: Dict[chess.PieceType, str] = {
    chess.PAWN: "Pawn",
    chess.KNIGHT: "Knight",
    chess.BISHOP: "Bishop",
    chess.ROOK: "Rook",
    chess.QUEEN: "Queen",
    chess.KING: "King",
}

PIECE_SYMBOLS_UNICODE: Dict[tuple[chess.PieceType, chess.Color], str] = {
    (chess.PAWN, chess.WHITE): "♙",
    (chess.KNIGHT, chess.WHITE): "♘",
    (chess.BISHOP, chess.WHITE): "♗",
    (chess.ROOK, chess.WHITE): "♖",
    (chess.QUEEN, chess.WHITE): "♕",
    (chess.KING, chess.WHITE): "♔",
    (chess.PAWN, chess.BLACK): "♟",
    (chess.KNIGHT, chess.BLACK): "♞",
    (chess.BISHOP, chess.BLACK): "♝",
    (chess.ROOK, chess.BLACK): "♜",
    (chess.QUEEN, chess.BLACK): "♛",
    (chess.KING, chess.BLACK): "♚",
}


class ExchangeCategory(Enum):
    """Categorization of an evaluated capture/exchange."""
    WINNING = "winning"        # Net material gain (> 50 cp) -> Green
    EQUAL = "equal"            # Even trade (-50 to +50 cp)   -> Blue / Neutral
    LOSING = "losing"          # Net material loss (< -50 cp) -> Red
    FREE_PIECE = "free_piece"  # Opponent piece is completely undefended -> Bright Green


def get_piece_value(piece_type: chess.PieceType) -> int:
    """Return piece value in centipawns."""
    return PIECE_VALUES.get(piece_type, 0)
