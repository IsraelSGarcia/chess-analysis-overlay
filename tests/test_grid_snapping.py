"""
test_grid_snapping.py
=====================
Tests for automated chessboard grid detection and snapping.
Verifies that rough area selections snap accurately to the exact 8x8 chessboard boundary.
"""

import unittest
import sys
import os
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer.recognition import (
    refine_grid_box,
    detect_chessboard_in_crop,
)

TESTS_DIR = Path(__file__).parent


class TestGridSnapping(unittest.TestCase):

    def setUp(self):
        self.starting_board_path = TESTS_DIR / "test_board_starting.png"
        self.sicilian_board_path = TESTS_DIR / "test_board_sicilian.png"

    def test_refine_grid_box_exact_on_starting_board(self):
        """refine_grid_box preserves or snaps to exact coordinates on starting board."""
        img = Image.open(self.starting_board_path)
        arr = np.array(img.convert("L"))
        refined = refine_grid_box(arr, 0, 0, 640, 640)
        self.assertEqual(refined, (0, 0, 640, 640))

    def test_refine_grid_box_exact_on_sicilian_board(self):
        """refine_grid_box preserves or snaps to exact coordinates on sicilian board."""
        img = Image.open(self.sicilian_board_path)
        arr = np.array(img.convert("L"))
        refined = refine_grid_box(arr, 0, 0, 720, 720)
        self.assertEqual(refined, (0, 0, 720, 720))

    def test_detect_chessboard_direct(self):
        """detect_chessboard_in_crop finds direct starting board."""
        img = Image.open(self.starting_board_path)
        box = detect_chessboard_in_crop(img)
        self.assertIsNotNone(box)
        self.assertEqual(box, (0, 0, 640, 640))

    def test_detect_chessboard_from_rough_larger_area(self):
        """detect_chessboard_in_crop snaps from a rough area larger than the board."""
        img = Image.open(self.starting_board_path)
        # Paste board inside a canvas with 60px padding
        canvas = Image.new("RGB", (760, 760), (32, 34, 38))
        canvas.paste(img, (60, 60))

        # Rough drag with 30px offset inside the crop
        rough = (40, 40, 680, 680)
        box = detect_chessboard_in_crop(canvas, rough)
        self.assertIsNotNone(box)
        self.assertEqual(box, (60, 60, 640, 640))

    def test_detect_chessboard_from_rough_smaller_area(self):
        """detect_chessboard_in_crop snaps when user dragged slightly smaller inside the board."""
        img = Image.open(self.sicilian_board_path)
        canvas = Image.new("RGB", (900, 900), (45, 48, 55))
        tx, ty = 90, 90
        canvas.paste(img, (tx, ty))

        # Simulated user rough selection: only 650x650 of the 720x720 board
        rough = (tx + 30, ty + 20, 650, 660)
        box = detect_chessboard_in_crop(canvas, rough)
        self.assertIsNotNone(box)
        self.assertEqual(box, (tx, ty, 720, 720))

    def test_detect_chessboard_with_exterior_coordinates(self):
        """Outside coordinates (rank 1-8, file a-h) are excluded from the snapped grid."""
        img = Image.open(self.starting_board_path)
        canvas = Image.new("RGB", (840, 840), (30, 30, 30))
        tx, ty = 100, 100
        canvas.paste(img, (tx, ty))

        # Draw coordinate text outside the board
        draw = ImageDraw.Draw(canvas)
        for i, ch in enumerate("abcdefgh"):
            draw.text((tx + i * 80 + 35, ty + 645), ch, fill=(180, 180, 180))
        for i, num in enumerate("87654321"):
            draw.text((tx - 25, ty + i * 80 + 35), num, fill=(180, 180, 180))

        box = detect_chessboard_in_crop(canvas, (tx - 30, ty - 20, 700, 700))
        self.assertIsNotNone(box)
        self.assertEqual(box, (tx, ty, 640, 640))

    def test_detect_chessboard_on_blank_image_returns_none(self):
        """Blank image returns None without crashing."""
        blank = Image.new("RGB", (500, 500), (40, 40, 40))
        box = detect_chessboard_in_crop(blank)
        self.assertIsNone(box)


if __name__ == "__main__":
    unittest.main()
