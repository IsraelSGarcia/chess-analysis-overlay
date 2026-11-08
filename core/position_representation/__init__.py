"""
core.position_representation
============================
Board models, coordinate transforms, and chess geometry.
"""

from .board_state import (
    square_to_coords,
    coords_to_square,
    square_to_rect,
    get_square_center,
    point_to_square,
)

__all__ = [
    "square_to_coords",
    "coords_to_square",
    "square_to_rect",
    "get_square_center",
    "point_to_square",
]
