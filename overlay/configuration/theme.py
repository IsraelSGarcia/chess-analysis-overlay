"""
theme.py
========
Unified Design System and Color Palette for Chess Analysis Overlay.

Centralizes:
- Tactical arrow colors, opacities, and width multipliers
- Corner bracket styling and perimeter indicators
- Square control tinting
- HUD badge and card styling templates
"""

from __future__ import annotations

from PySide6.QtGui import QColor


class VisualTheme:
    """Consolidated visual design specifications."""

    # -------------------------------------------------------------------------
    # Tactical Mode Palette (High Contrast, Distinct Semantic Meaning)
    # -------------------------------------------------------------------------
    # Winning Trades (SEE > 0): Bold Emerald Green
    WINNING_TRADE: QColor = QColor(0, 230, 118, 255)
    WINNING_TRADE_HEX: str = "#00e676"

    # Hanging / Undefended Pieces: Radiant Bright Orange
    HANGING: QColor = QColor(255, 109, 0, 220)
    HANGING_OUTLINE: QColor = QColor(255, 109, 0, 140)
    HANGING_HEX: str = "#ff6d00"

    # Tactical Motifs (Forks, Pins, Skewers): Electric Purple
    MOTIF: QColor = QColor(213, 0, 249, 240)
    MOTIF_DASHED: QColor = QColor(213, 0, 249, 190)
    MOTIF_HEX: str = "#d500f9"

    # Trapped Pieces: Ice Cyan
    TRAPPED: QColor = QColor(0, 229, 255, 240)
    TRAPPED_OUTLINE: QColor = QColor(0, 229, 255, 140)
    TRAPPED_HEX: str = "#00e5ff"

    # Slider X-Ray Rays: Thin Dashed Ice Cyan Laser
    XRAY: QColor = QColor(0, 229, 255, 160)
    XRAY_HEX: str = "#00e5ff"

    # Checks & Checkmate Alert: High-Visibility Crimson Red (Solid)
    CHECK: QColor = QColor(255, 23, 68, 245)
    CHECK_HEX: str = "#ff1744"

    # Blunder Moves: Crimson Red (43% Opacity, Thin, Unobtrusive)
    BLUNDER: QColor = QColor(255, 23, 68, 110)
    BLUNDER_HEX: str = "#ff1744"

    # Defended Pieces & Connections: Sky Blue
    DEFENSE: QColor = QColor(0, 176, 255, 210)
    DEFENSE_HEX: str = "#00b0ff"

    # Back-Rank Infiltration Threats: Crimson Red
    BACK_RANK: QColor = QColor(255, 23, 68, 220)

    # -------------------------------------------------------------------------
    # Captures Mode Palette
    # -------------------------------------------------------------------------
    PLAYER_CAPTURE: QColor = QColor(41, 121, 255, 200)
    ENEMY_CAPTURE: QColor = QColor(245, 55, 55, 200)

    # -------------------------------------------------------------------------
    # Square Control Highlights
    # -------------------------------------------------------------------------
    SQUARE_PLAYER: QColor = QColor(45, 145, 255, 60)
    SQUARE_PLAYER_BORDER: QColor = QColor(60, 160, 255, 185)
    SQUARE_ENEMY: QColor = QColor(245, 55, 55, 60)
    SQUARE_ENEMY_BORDER: QColor = QColor(255, 75, 75, 185)
    SQUARE_CONTESTED: QColor = QColor(180, 75, 240, 65)
    SQUARE_CONTESTED_BORDER: QColor = QColor(210, 100, 255, 185)

    # High-contrast arrow outline and origin dot
    ARROW_OUTLINE: QColor = QColor(10, 14, 20, 220)
    ARROW_ORIGIN_PEN: QColor = QColor(10, 14, 20, 200)

    # -------------------------------------------------------------------------
    # Arrow Geometry & Multipliers
    # -------------------------------------------------------------------------
    WIDTH_WINNING: float = 1.35
    WIDTH_FORK: float = 1.25
    WIDTH_MOTIF: float = 1.20
    WIDTH_HANGING: float = 1.10
    WIDTH_STANDARD: float = 1.00
    WIDTH_XRAY: float = 0.85
    WIDTH_BLUNDER: float = 0.55

    # Center Occlusion Margins (preserves piece centers)
    START_OFFSET_RATIO: float = 0.26
    END_OFFSET_RATIO: float = 0.24

    # Corner Brackets
    BRACKET_LEN: float = 11.0
    BRACKET_PEN_WIDTH: float = 2.2

    @staticmethod
    def get_badge_css(hex_color: str, bg_alpha: float = 0.18, border_alpha: float = 0.70) -> str:
        """Generate consistent floating HUD badge stylesheet."""
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        return (
            f"background-color: rgba({r}, {g}, {b}, {bg_alpha:.2f});\n"
            f"color: {hex_color};\n"
            f"border: 1px solid rgba({r}, {g}, {b}, {border_alpha:.2f});\n"
            "border-radius: 4px;\n"
            "padding: 3px 6px;\n"
            "font-size: 10px;\n"
            "font-weight: 600;"
        )


THEME = VisualTheme()
Theme = VisualTheme
