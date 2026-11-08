"""
validator.py
============
Chessboard recognition plausibility and validity verification.

Guarantees that recognized board states represent legal physical setups
before triggering calculations or overlay annotations.
"""

from __future__ import annotations

import chess


def is_valid_recognized_board(board: chess.Board) -> bool:
    """
    Validate that a recognized board has plausible chess piece counts.

    Requirements:
    - Exactly 1 White King and 1 Black King.
    - At most 16 pieces per side.
    - At most 8 pawns per side.
    - No pawns on rank 1 or rank 8 (physically impossible in chess rules).
    - Both kings cannot be in check simultaneously.

    Guards against misaligned crops, desktop background noise, and prevents
    false-positive flickering.
    """
    piece_map = board.piece_map()
    pieces = list(piece_map.values())
    if len(pieces) < 2:
        return False

    white_kings = sum(1 for p in pieces if p.piece_type == chess.KING and p.color == chess.WHITE)
    black_kings = sum(1 for p in pieces if p.piece_type == chess.KING and p.color == chess.BLACK)
    if white_kings != 1 or black_kings != 1:
        return False

    white_pieces = sum(1 for p in pieces if p.color == chess.WHITE)
    black_pieces = sum(1 for p in pieces if p.color == chess.BLACK)
    if white_pieces > 16 or black_pieces > 16:
        return False

    white_pawns = sum(1 for p in pieces if p.piece_type == chess.PAWN and p.color == chess.WHITE)
    black_pawns = sum(1 for p in pieces if p.piece_type == chess.PAWN and p.color == chess.BLACK)
    if white_pawns > 8 or black_pawns > 8:
        return False

    for sq, p in piece_map.items():
        if p.piece_type == chess.PAWN:
            rank = chess.square_rank(sq)
            if rank == 0 or rank == 7:
                return False

    # In legal chess, both Kings can never be attacked/checked at the same time
    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)
    if white_king_sq is not None and black_king_sq is not None:
        white_in_check = board.is_attacked_by(chess.BLACK, white_king_sq)
        black_in_check = board.is_attacked_by(chess.WHITE, black_king_sq)
        if white_in_check and black_in_check:
            return False

    return True
