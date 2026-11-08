"""
core.position_representation.board_state
========================================
Chess position representation and geometric coordinate mappings for the 8x8 grid.
"""

from __future__ import annotations

from typing import Optional, Tuple
import chess


def square_to_coords(sq: int, flipped: bool = False) -> Tuple[int, int]:
    """
    Convert a square index (0..63) to (col, row) on the 8x8 board.
    
    If flipped is False (White at bottom):
      col 0 = a, col 7 = h
      row 0 = rank 8, row 7 = rank 1
    If flipped is True (Black at bottom):
      col 0 = h, col 7 = a
      row 0 = rank 1, row 7 = rank 8
    """
    file_idx = chess.square_file(sq)
    rank_idx = chess.square_rank(sq)

    if not flipped:
        col = file_idx
        row = 7 - rank_idx
    else:
        col = 7 - file_idx
        row = rank_idx

    return col, row


def coords_to_square(col: int, row: int, flipped: bool = False) -> Optional[int]:
    """
    Convert (col, row) on screen grid (0..7, 0..7) back to chess square index.
    """
    if not (0 <= col <= 7 and 0 <= row <= 7):
        return None

    if not flipped:
        file_idx = col
        rank_idx = 7 - row
    else:
        file_idx = 7 - col
        rank_idx = row

    return chess.square(file_idx, rank_idx)


def square_to_rect(
    sq: int,
    board_width: float,
    board_height: float,
    flipped: bool = False,
) -> Tuple[float, float, float, float]:
    """
    Calculate (x, y, width, height) of square sq within a board of dimensions (board_width, board_height).
    Uses exact float interpolation to prevent integer discretization drift.
    """
    col, row = square_to_coords(sq, flipped)
    x0 = col * board_width / 8.0
    x1 = (col + 1) * board_width / 8.0
    y0 = row * board_height / 8.0
    y1 = (row + 1) * board_height / 8.0

    return x0, y0, x1 - x0, y1 - y0


def get_square_center(
    sq: int,
    board_width: float,
    board_height: float,
    flipped: bool = False,
) -> Tuple[float, float]:
    """Return the center (cx, cy) of square sq."""
    x, y, w, h = square_to_rect(sq, board_width, board_height, flipped)
    return x + w / 2.0, y + h / 2.0


def point_to_square(
    x: float,
    y: float,
    board_width: float,
    board_height: float,
    flipped: bool = False,
) -> Optional[int]:
    """Given pixel coordinates (x, y) relative to board top-left, return square index or None."""
    if not (0.0 <= x <= board_width and 0.0 <= y <= board_height):
        return None

    col = int(x / (board_width / 8.0))
    row = int(y / (board_height / 8.0))
    col = min(7, max(0, col))
    row = min(7, max(0, row))

    return coords_to_square(col, row, flipped)
