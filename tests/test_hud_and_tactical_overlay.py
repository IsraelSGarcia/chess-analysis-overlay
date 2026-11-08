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

    def test_hud_check_alert(self):
        # White King on e1 in check from Black Queen on h4
        board = chess.Board("rnb1kbnr/ppppqppp/8/8/3P4/8/PPPP1PPP/RNBQKBNR w KQkq - 1 3")
        self.assertTrue(board.is_check())
        report = generate_tactical_report(board, search_depth=1)
        self.hud.update_report(report)

        self.assertTrue(self.hud.lbl_alert.isVisible())
        self.assertIn("CHECK!", self.hud.lbl_alert.text())
        self.assertIn("White King under attack", self.hud.lbl_alert.text())

    def test_hud_stalemate_alert(self):
        # Classic stalemate position
        board = chess.Board("k7/8/1Q6/8/8/8/8/7K b - - 0 1")
        self.assertTrue(board.is_stalemate())
        report = generate_tactical_report(board, search_depth=1)
        self.hud.update_report(report)

        self.assertTrue(self.hud.lbl_alert.isVisible())
        self.assertIn("STALEMATE", self.hud.lbl_alert.text())



if __name__ == "__main__":
    unittest.main()
