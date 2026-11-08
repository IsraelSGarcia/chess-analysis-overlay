"""
test_theme.py
=============
Unit tests for the centralized design system and color palette.
"""

import unittest
from PySide6.QtGui import QColor
from overlay.configuration.theme import THEME, VisualTheme, Theme


class TestTheme(unittest.TestCase):

    def test_theme_singleton_and_aliases(self):
        self.assertIsInstance(THEME, VisualTheme)
        self.assertEqual(Theme, VisualTheme)

    def test_tactical_colors_valid_and_distinct(self):
        # All colors must have valid alpha and RGB components
        colors = [
            THEME.WINNING_TRADE,
            THEME.HANGING,
            THEME.MOTIF,
            THEME.TRAPPED,
            THEME.XRAY,
            THEME.BLUNDER,
            THEME.DEFENSE,
        ]
        for c in colors:
            self.assertIsInstance(c, QColor)
            self.assertTrue(c.isValid())
            self.assertGreater(c.alpha(), 0)

    def test_blunder_color_is_thin_and_subtle(self):
        # Verify blunder alpha is reduced (~110 / 43% opacity) and width is 0.55
        self.assertEqual(THEME.BLUNDER.alpha(), 110)
        self.assertEqual(THEME.WIDTH_BLUNDER, 0.55)

    def test_badge_css_generation(self):
        css = THEME.get_badge_css(THEME.WINNING_TRADE_HEX)
        self.assertIn(THEME.WINNING_TRADE_HEX, css)
        self.assertIn("rgba(", css)
        self.assertIn("border-radius:", css)


if __name__ == "__main__":
    unittest.main()
