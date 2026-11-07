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
    white_color: Tuple[int, int, int, int] = (45, 145, 255, 230)    # vibrant royal blue
    black_color: Tuple[int, int, int, int] = (245, 55,  55, 230)    # vibrant crimson red

    # Small sleek arrow geometry
    shaft_width_ratio: float = 0.045
    head_length_ratio: float = 0.17
    head_width_ratio:  float = 0.12
    opacity: float = 1.0

    overlay_visible: bool = True       # Master visibility toggle
    mode: str = "tactics"              # "tactics" or "captures"
    show_white: bool = True            # Player toggle
    show_black: bool = True            # Enemy toggle
    show_highlights: bool = True       # Square tints
    show_defense: bool = True          # Defending friendly pieces arrows
    show_hud: bool = False
    show_tactical_arrows: bool = True       # Color code arrows by tactical evaluation (SEE)
    show_tactical_highlights: bool = True   # Tactical square tints (hanging, motifs, checks)

    flipped: bool = False              # True when Black is at the bottom

    @property
    def square_size(self) -> int:
        return max(1, self.board_region[2] // 8)
