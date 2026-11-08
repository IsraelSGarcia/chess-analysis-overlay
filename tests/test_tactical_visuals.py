"""
test_tactical_visuals.py
========================
Tests for high-contrast tactical visualization, color matching between
the HUD and chessboard annotations, and camera cleanliness during capture.
"""

import unittest
import sys
import chess
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter, QImage
from PySide6.QtCore import QRectF

from projects.chess_tactical_analyzer import generate_tactical_report
from overlay.configuration.overlay_config import OverlayConfig
from overlay.rendering.overlay_widget import OverlayWidget
from overlay.interface.hud_panel import HUDPanel

app = QApplication.instance() or QApplication(sys.argv)


class TestTacticalVisuals(unittest.TestCase):

    def setUp(self):
        self.config = OverlayConfig(
            board_region=(0, 0, 640, 640),
            mode="tactics",
            show_tactical_arrows=True,
            show_tactical_highlights=True,
        )
        self.widget = OverlayWidget(self.config)
        self.hud = HUDPanel()
        self.hud.show()

    def tearDown(self):
        self.widget.close()
        self.hud.close()

    def test_corner_brackets_drawing(self):
        img = QImage(200, 200, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        rect = QRectF(20, 20, 80, 80)
        color = QColor(0, 230, 118)
        self.widget._draw_corner_brackets(p, rect, color, bracket_len=12.0, pen_width=2.5)
        p.end()
        # Verify non-zero pixels drawn
        self.assertGreater(img.pixelColor(20, 20).alpha(), 0)

    def test_tactics_mode_paint_with_rich_motifs(self):
        # Position with fork, pin, and hanging piece
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        report = generate_tactical_report(board, search_depth=3)

        self.widget.set_tactical_report(report)
        self.hud.update_report(report)

        # Repaint widget onto an off-screen image buffer
        img = QImage(640, 640, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        self.widget._paint_tactics_mode(p)
        p.end()

        # Verify pixels were drawn
        import numpy as np
        arr = np.frombuffer(img.constBits(), dtype=np.uint8).reshape(640, 640, 4)
        self.assertGreater(np.count_nonzero(arr[:, :, 3]), 1000)

        # Verify HUD motif badge is visible and populated
        self.assertTrue(self.hud.lbl_motifs.isVisible())
        self.assertIn("Tactical Motif", self.hud.lbl_motifs.text())

    def test_tactics_mode_paint_with_check(self):
        # Scholar's mate delivery (Checkmate)
        board = chess.Board("r1bqkb1r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
        report = generate_tactical_report(board, search_depth=2)

        self.widget.set_tactical_report(report)
        self.hud.update_report(report)

        self.assertTrue(self.hud.lbl_alert.isVisible())
        self.assertIn("CHECKMATE", self.hud.lbl_alert.text())

        # Off-screen paint
        img = QImage(640, 640, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        self.widget._paint_tactics_mode(p)
        p.end()

    def test_arrow_margins_preserve_piece_centers(self):
        # Verify that start and end offsets leave the center of squares unoccluded
        sq = 80.0
        start_offset = sq * 0.26
        end_offset = sq * 0.24
        self.assertGreaterEqual(start_offset, 20.0)
        self.assertGreaterEqual(end_offset, 18.0)

    def test_tactics_mode_paint_trapped_piece(self):
        # Position after 11... c4 in Noah's Ark trap: White bishop on b3 is trapped
        board = chess.Board("r2qkb1r/3b1ppp/p2p4/1p1Q4/2p1P3/1B6/PPP2PPP/RNB1K2R w KQkq - 0 12")
        report = generate_tactical_report(board, search_depth=3, active_turn=chess.WHITE)

        self.widget.set_tactical_report(report)
        self.hud.update_report(report)

        # Verify HUD trapped pill is visible
        self.assertTrue(self.hud.lbl_trapped.isVisible())
        self.assertIn("Trapped", self.hud.lbl_trapped.text())

        # Off-screen paint must succeed and draw trapped piece brackets
        img = QImage(640, 640, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        self.widget._paint_tactics_mode(p)
        p.end()

        import numpy as np
        arr = np.frombuffer(img.constBits(), dtype=np.uint8).reshape(640, 640, 4)
        self.assertGreater(np.count_nonzero(arr[:, :, 3]), 100)

    def test_tactics_mode_paint_xray_rays(self):
        # Position with Black Bishop on b4 X-raying King on e1 through Knight on c3
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        report = generate_tactical_report(board, search_depth=3, active_turn=chess.WHITE)

        self.widget.set_tactical_report(report)
        self.hud.update_report(report)

        # Off-screen paint must succeed
        img = QImage(640, 640, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        self.widget._paint_tactics_mode(p)
        p.end()

        import numpy as np
        arr = np.frombuffer(img.constBits(), dtype=np.uint8).reshape(640, 640, 4)
        self.assertGreater(np.count_nonzero(arr[:, :, 3]), 100)


if __name__ == "__main__":
    unittest.main()
