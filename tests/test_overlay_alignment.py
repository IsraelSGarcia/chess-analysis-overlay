"""
test_overlay_alignment.py
=========================
Verifies that OverlayWidget computes square boundaries and centers
without integer truncation drift, ensuring exact alignment with the 8x8 grid.
"""

import os
import sys
import unittest
from PySide6.QtWidgets import QApplication
import chess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from overlay.configuration.overlay_config import OverlayConfig
from overlay.rendering.overlay_widget import OverlayWidget

app = QApplication.instance() or QApplication(sys.argv)


class TestOverlayAlignment(unittest.TestCase):

    def setUp(self):
        # Test with an awkward non-divisible board size (e.g. 557x557)
        self.config = OverlayConfig(board_region=(100, 100, 557, 557))
        self.widget = OverlayWidget(self.config)

    def test_square_rect_partition(self):
        """Verify that all 8 columns and 8 rows span the full board without drift."""
        w = float(self.widget.width())
        h = float(self.widget.height())

        sq_w = w / 8.0
        sq_h = h / 8.0

        for sq in range(64):
            rect = self.widget._get_square_rect(sq)
            file_ = chess.square_file(sq)
            rank_ = chess.square_rank(sq)

            # Not flipped: col = file, row = 7 - rank
            expected_x1 = file_ * sq_w
            expected_y1 = (7 - rank_) * sq_h

            # rect is inset by 1px
            self.assertAlmostEqual(rect.left(), expected_x1 + 1.0, delta=0.01)
            self.assertAlmostEqual(rect.top(), expected_y1 + 1.0, delta=0.01)

    def test_square_centres(self):
        """Verify arrow origin and target centers match the exact square center."""
        w = float(self.widget.width())
        h = float(self.widget.height())

        sq_w = w / 8.0
        sq_h = h / 8.0

        for sq in range(64):
            cx, cy = self.widget._get_square_centre(sq)
            file_ = chess.square_file(sq)
            rank_ = chess.square_rank(sq)

            expected_cx = (file_ + 0.5) * sq_w
            expected_cy = (7 - rank_ + 0.5) * sq_h

            self.assertAlmostEqual(cx, expected_cx, delta=0.01)
            self.assertAlmostEqual(cy, expected_cy, delta=0.01)

    def test_flipped_orientation_alignment(self):
        """When board is physically flipped (Black at bottom), squares map cleanly."""
        self.widget.set_board_flipped(True)
        w = float(self.widget.width())
        h = float(self.widget.height())
        sq_w = w / 8.0
        sq_h = h / 8.0

        # a1 (file 0, rank 0) on flipped board is at bottom-right (col 7, row 0)
        cx, cy = self.widget._get_square_centre(chess.A1)
        expected_cx = (7 + 0.5) * sq_w
        expected_cy = (0 + 0.5) * sq_h

        self.assertAlmostEqual(cx, expected_cx, delta=0.01)
        self.assertAlmostEqual(cy, expected_cy, delta=0.01)


if __name__ == "__main__":
    unittest.main()
