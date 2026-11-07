"""
test_auto_detect.py
===================
Unit tests verifying full-screen automatic chessboard detection and disappearance.
"""

import os
import sys
import unittest
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer.recognition import detect_chessboard_fullscreen


class TestAutoDetection(unittest.TestCase):

    def test_fullscreen_detection_locates_board(self):
        """Verifies that a board placed anywhere on a 1920x1080 canvas is located accurately."""
        desktop = Image.new("RGB", (1920, 1080), (35, 40, 48))
        test_board_path = os.path.join(os.path.dirname(__file__), "test_board_starting.png")
        board = Image.open(test_board_path)

        # Paste board at (350, 180)
        target_x, target_y = 350, 180
        desktop.paste(board, (target_x, target_y))

        detected = detect_chessboard_fullscreen(desktop)
        self.assertIsNotNone(detected)

        dx, dy, dw, dh = detected
        # Allow +/- 3px tolerance for edge contrast refinement
        self.assertAlmostEqual(dx, target_x, delta=4)
        self.assertAlmostEqual(dy, target_y, delta=4)
        self.assertAlmostEqual(dw, board.width, delta=4)
        self.assertAlmostEqual(dh, board.height, delta=4)

    def test_fullscreen_detection_returns_none_when_no_board(self):
        """When no chessboard is on screen, detect_chessboard_fullscreen returns None."""
        desktop = Image.new("RGB", (1920, 1080), (30, 30, 30))
        detected = detect_chessboard_fullscreen(desktop)
        self.assertIsNone(detected)


if __name__ == "__main__":
    unittest.main()
