"""
overlay.py
==========
Configuration dataclass for the overlay renderer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class OverlayConfig:
    """All runtime parameters controlling overlay appearance and position."""

    board_region: Tuple[int, int, int, int] = (0, 0, 800, 800)

    # Arrow colours (RGBA)
    white_color: Tuple[int, int, int, int] = (45,  145, 255, 230)    # vibrant blue
    black_color: Tuple[int, int, int, int] = (245,  55,  55, 230)    # vibrant red

    # Small sleek arrow geometry (fractions of square size)
    shaft_width_ratio: float = 0.05    # 5% of square width (clean & clearly visible)
    head_length_ratio: float = 0.18    # 18% of square width
    head_width_ratio:  float = 0.13    # 13% of square width

    opacity: float = 1.0

    show_white: bool = True
    show_black: bool = True
    show_highlights: bool = True
    show_hud: bool = False

    flipped: bool = False              # True when Black is at the bottom

    @property
    def square_size(self) -> int:
        return max(1, self.board_region[2] // 8)
