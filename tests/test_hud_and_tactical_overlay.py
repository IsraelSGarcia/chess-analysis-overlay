"""
test_hud_and_tactical_overlay.py
================================
Unit tests verifying HUDPanel updates and OverlayWidget tactical rendering.
"""

import os
import sys
import unittest
import chess
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from overlay.configuration.overlay_config import OverlayConfig
from overlay.rendering.overlay_widget import OverlayWidget
from overlay.interface.hud_panel import HUDPanel
from projects.chess_tactical_analyzer import generate_tactical_report

app = QApplication.instance() or QApplication(sys.argv)


class TestHUDAndTacticalOverlay(unittest.TestCase):

    def setUp(self):
        self.config = OverlayConfig(
            board_region=(100, 100, 600, 600),
            show_tactical_arrows=True,
            show_tactical_highlights=True,
        )
        self.widget = OverlayWidget(self.config)
        self.hud = HUDPanel()
        self.hud.show()

    def tearDown(self):
        self.widget.close()
        self.hud.close()

    def test_hud_update_with_tactical_report(self):
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        report = generate_tactical_report(board, search_depth=3)

        self.hud.update_report(report)

        # Check that material label is updated
        self.assertIn("Material: Equal", self.hud.lbl_material.text())
        # Check that motifs are surfaced
        self.assertFalse(self.hud.lbl_motifs.isHidden())
        self.assertIn("pins", self.hud.lbl_motifs.text())

    def test_hud_positional_intelligence_mode(self):
        """Verify Positional Mode strictly isolates positional analytics from tactical badges."""
        # French Defense Advance Variation: White pawn on e5, Black pawn on d5, bad light-squared bishop on c8
        board = chess.Board("rnbqk1nr/ppp2ppp/4p3/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3")
        report = generate_tactical_report(board, search_depth=2)

        # Switch HUD to positional mode
        self.hud.set_mode("positional")
        self.hud.update_report(report)

        # 1. Header title must reflect Positional Intelligence
        self.assertEqual(self.hud.lbl_title.text(), "Positional Intelligence")

        # 2. Positional badges must be visible
        self.assertTrue(self.hud.lbl_pos_outposts.isVisible())
        self.assertTrue(self.hud.lbl_pos_files.isVisible())
        self.assertTrue(self.hud.lbl_pos_pawns.isVisible())
        self.assertTrue(self.hud.lbl_pos_bishops.isVisible())
        self.assertTrue(self.hud.lbl_pos_space.isVisible())

        # 3. Positional badges must contain substantive evaluation text
        self.assertIn("Outposts", self.hud.lbl_pos_outposts.text())
        self.assertIn("Files", self.hud.lbl_pos_files.text())
        self.assertIn("Pawns", self.hud.lbl_pos_pawns.text())
        self.assertIn("Bad Bishop", self.hud.lbl_pos_bishops.text())
        self.assertIn("Space", self.hud.lbl_pos_space.text())

        # 4. Tactical badges must be strictly hidden
        self.assertFalse(self.hud.lbl_trades.isVisible())
        self.assertFalse(self.hud.lbl_motifs.isVisible())
        self.assertFalse(self.hud.lbl_hanging.isVisible())

        # 5. Switching back to Tactics mode toggles badges cleanly
        self.hud.set_mode("tactics")
        self.hud.update_report(report)
        self.assertEqual(self.hud.lbl_title.text(), "Tactical Intelligence")
        self.assertFalse(self.hud.lbl_pos_outposts.isVisible())
        self.assertFalse(self.hud.lbl_pos_files.isVisible())
        self.assertFalse(self.hud.lbl_pos_pawns.isVisible())
        self.assertFalse(self.hud.lbl_pos_bishops.isVisible())
        self.assertFalse(self.hud.lbl_pos_space.isVisible())

    def test_overlay_receives_tactical_report(self):
        board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/4n3/8/PPPPQPPP/RNB1KBNR w KQkq - 0 1")
        report = generate_tactical_report(board, search_depth=3)

        self.widget.set_tactical_report(report)
        self.assertIsNotNone(self.widget._tactical_report)

        # Trigger paint in tactics mode
        self.widget.set_config(OverlayConfig(mode="tactics", board_region=(100, 100, 600, 600)))
        self.widget.repaint()

        # Trigger paint in captures mode
        self.widget.set_config(OverlayConfig(mode="captures", board_region=(100, 100, 600, 600)))
        self.widget.repaint()

        # Trigger paint in positional mode
        self.widget.set_config(OverlayConfig(mode="positional", board_region=(100, 100, 600, 600)))
        self.widget.repaint()

    def test_overlay_clear(self):
        board = chess.Board()
        report = generate_tactical_report(board, search_depth=1)
        self.widget.set_tactical_report(report)
        self.assertIsNotNone(self.widget._tactical_report)

        self.widget.clear()
        self.assertIsNone(self.widget._tactical_report)
        self.assertEqual(len(self.widget._white_captures), 0)
        self.assertEqual(len(self.widget._black_captures), 0)

    def test_hud_none_report_handling(self):
        self.hud.update_report(None)
        self.assertIn("Waiting", self.hud.lbl_material.text())


if __name__ == "__main__":
    unittest.main()
