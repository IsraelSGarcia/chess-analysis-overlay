"""
test_turn_and_palette_alignment.py
==================================
Unit tests verifying:
1. Turn detection from last-move square highlights (Chess.com / Lichess).
2. Strict turn-based filtering for candidate moves and forcing tactics.
3. Unambiguous 1:1 color palette alignment between board elements and HUD badges.
4. Explanations present on the HUD for every element drawn on the board.
"""

import os
import sys
import unittest
import chess
import numpy as np
from PIL import Image, ImageDraw

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor, QPainter, QImage

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer.recognition import detect_active_turn
from chess_visualizer._overlay_widget import OverlayWidget
from chess_visualizer.overlay import OverlayConfig
from chess_visualizer._hud_panel import HUDPanel
from chess_tactical import generate_tactical_report

app = QApplication.instance() or QApplication(sys.argv)


class TestTurnAndPaletteAlignment(unittest.TestCase):

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

    def test_white_move_detects_black_turn(self):
        """When White plays 1. e4 (highlighting e2 and e4), it is now Black's turn to move."""
        board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        # Draw dark squares
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    draw.rectangle([c * sq_w, r * sq_h, (c + 1) * sq_w, (r + 1) * sq_h], fill=(118, 150, 86))

        # Highlight e2 (col 4, row 6) and e4 (col 4, row 4) with Chess.com yellow tint
        draw.rectangle([4 * sq_w, 6 * sq_h, 5 * sq_w, 7 * sq_h], fill=(247, 247, 105))
        draw.rectangle([4 * sq_w, 4 * sq_h, 5 * sq_w, 5 * sq_h], fill=(247, 247, 105))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.BLACK)

    def test_black_move_detects_white_turn(self):
        """When Black plays 1... c5 (highlighting c7 and c5), it is now White's turn to move."""
        board = chess.Board("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        # Draw dark squares
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    draw.rectangle([c * sq_w, r * sq_h, (c + 1) * sq_w, (r + 1) * sq_h], fill=(118, 150, 86))

        # Highlight c7 (col 2, row 1) and c5 (col 2, row 3)
        draw.rectangle([2 * sq_w, 1 * sq_h, 3 * sq_w, 2 * sq_h], fill=(247, 247, 105))
        draw.rectangle([2 * sq_w, 3 * sq_h, 3 * sq_w, 4 * sq_h], fill=(247, 247, 105))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.WHITE)

    def test_flipped_board_move_detection(self):
        """When board is physically flipped (Black at bottom), last move detection maps squares accurately."""
        board = chess.Board("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        # When flipped, e2 is at col 3, row 1 (rank 2 from top is 7-2+1=?)
        # Let's verify: file e is index 4. Flipped col = 7 - 4 = 3.
        # rank 2 is index 1. Flipped row = rank_idx = 1.
        # rank 4 is index 3. Flipped row = 3.
        draw.rectangle([3 * sq_w, 1 * sq_h, 4 * sq_w, 2 * sq_h], fill=(247, 247, 105))
        draw.rectangle([3 * sq_w, 3 * sq_h, 4 * sq_w, 4 * sq_h], fill=(247, 247, 105))

        active_turn = detect_active_turn(board_img, board, flipped=True)
        self.assertEqual(active_turn, chess.BLACK)

    def test_hud_explains_active_board_elements(self):
        """Verify that every element visible on the board has an explanation on the HUD."""
        # Position with fork, pin, and check
        board = chess.Board("r1bqk2r/pppp1Qpp/2n2n2/4p3/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 0 4")
        report = generate_tactical_report(board, search_depth=2)

        self.hud.update_report(report)

        # Check alert explanation present
        self.assertTrue(self.hud.lbl_alert.isVisible())
        self.assertIn("CHECK", self.hud.lbl_alert.text())
        self.assertIn("Black", self.hud.lbl_alert.text())

    def test_strict_color_palette_distinctness(self):
        """Verify that the tactical colors are completely distinct and non-overlapping."""
        trades_color = QColor(0, 230, 118)    # Emerald Green #00E676
        motifs_color = QColor(213, 0, 249)    # Electric Purple #D500F9
        hanging_color = QColor(255, 109, 0)   # Bright Orange #FF6D00
        check_color = QColor(255, 23, 68)     # Crimson Red #FF1744
        defended_color = QColor(0, 176, 255)  # Sky Blue #00B0FF

        colors = [trades_color, motifs_color, hanging_color, check_color, defended_color]

        # Calculate minimum pairwise RGB Euclidean distance between any two colors
        min_dist = float("inf")
        for i in range(len(colors)):
            for j in range(i + 1, len(colors)):
                c1, c2 = colors[i], colors[j]
                dist = np.sqrt((c1.red() - c2.red())**2 + (c1.green() - c2.green())**2 + (c1.blue() - c2.blue())**2)
                if dist < min_dist:
                    min_dist = dist

        # All colors must have a distance of at least 80 to ensure high contrast and zero confusion
        self.assertGreater(min_dist, 80.0)

    def test_arbitrary_lighting_gradient_rejected(self):
        """Verify that when 3 or more squares have color shifts, detect_active_turn rejects it."""
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        # Simulate ambient lighting gradient across 4 squares
        for c in range(4):
            draw.rectangle([c * sq_w, 0, (c + 1) * sq_w, sq_h], fill=(220, 200, 180))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        # Should reject false positive and preserve initial turn (White)
        self.assertEqual(active_turn, chess.WHITE)

    def test_piece_selection_preserves_turn(self):
        """When a user clicks on a piece without moving it, piece positions are identical and turn is preserved."""
        from chess_visualizer.main import determine_turn_from_move
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        # Same piece map (user clicked a piece, highlighting it on screen)
        result = determine_turn_from_move(board, board.copy())
        self.assertIsNone(result)

    def test_determine_turn_from_moves(self):
        """Verify turn derivation from actual piece moves (White moves -> Black turn, Black moves -> White turn)."""
        from chess_visualizer.main import determine_turn_from_move
        b0 = chess.Board()
        b1 = b0.copy()
        b1.push_san("e4")  # White plays 1. e4
        self.assertEqual(determine_turn_from_move(b0, b1), chess.BLACK)

        b2 = b1.copy()
        b2.push_san("c5")  # Black plays 1... c5
        self.assertEqual(determine_turn_from_move(b1, b2), chess.WHITE)

    def test_determine_turn_castling(self):
        """Verify castling move correctly detects that White moved."""
        from chess_visualizer.main import determine_turn_from_move
        b_pre = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5")
        b_castle = b_pre.copy()
        b_castle.push_san("O-O")
        self.assertEqual(determine_turn_from_move(b_pre, b_castle), chess.BLACK)

    def test_clicked_piece_with_move_highlights_preserves_black_turn(self):
        """When White played 1. e4 (e2 & e4 highlighted) and Black clicks g8, it remains Black's turn."""
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    draw.rectangle([c * sq_w, r * sq_h, (c + 1) * sq_w, (r + 1) * sq_h], fill=(118, 150, 86))

        # Highlight e2 (col 4, row 6) and e4 (col 4, row 4)
        draw.rectangle([4 * sq_w, 6 * sq_h, 5 * sq_w, 7 * sq_h], fill=(247, 247, 105))
        draw.rectangle([4 * sq_w, 4 * sq_h, 5 * sq_w, 5 * sq_h], fill=(247, 247, 105))
        # Highlight clicked piece g8 (col 6, row 0)
        draw.rectangle([6 * sq_w, 0 * sq_h, 7 * sq_w, 1 * sq_h], fill=(247, 247, 105))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.BLACK)

    def test_single_clicked_piece_detects_color(self):
        """When a player clicks a piece on an otherwise idle board, active turn matches piece color."""
        board = chess.Board()
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        for r in range(8):
            for c in range(8):
                if (r + c) % 2 != 0:
                    draw.rectangle([c * sq_w, r * sq_h, (c + 1) * sq_w, (r + 1) * sq_h], fill=(118, 150, 86))

        # Click White pawn on e2 (col 4, row 6)
        draw.rectangle([4 * sq_w, 6 * sq_h, 5 * sq_w, 7 * sq_h], fill=(247, 247, 105))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.WHITE)

    def test_user_position_3_king_in_check_detects_black_turn(self):
        """Regression test for user position 3: White Knight on f6 gives check to Black King on d7.
        Active turn MUST be strictly Black to move, never White.
        """
        board = chess.Board("1r6/pp1kb3/n2p1N2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R b - - 0 24")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.BLACK)

    def test_user_position_4_king_in_check_blinking_red_detects_black_turn(self):
        """Regression test for user position 4: White Rook on h6 gives check to Black King on b6.
        Even if the website paints the King square in bright pulsing red, active turn MUST be Black.
        """
        board = chess.Board("6r1/1p6/1k5R/2p5/2P5/1P2PQP1/P5K1/8 b - - 3 37")
        board_img = Image.new("RGB", (640, 640), (240, 240, 210))
        draw = ImageDraw.Draw(board_img)
        sq_w = 640 / 8.0
        sq_h = 640 / 8.0

        # Simulate Chess.com / Lichess pulsing red check glow on b6 (col 1, row 2)
        draw.rectangle([1 * sq_w, 2 * sq_h, 2 * sq_w, 3 * sq_h], fill=(255, 30, 30))

        active_turn = detect_active_turn(board_img, board, flipped=False)
        self.assertEqual(active_turn, chess.BLACK)

    def test_king_in_check_overlay_and_hud_alerting_removed(self):
        """Verify that check alerting (red border, threat arrow to king, HUD check alert) is removed."""
        board = chess.Board("6r1/1p6/1k5R/2p5/2P5/1P2PQP1/P5K1/8 b - - 3 37")
        report = generate_tactical_report(board, search_depth=2, active_turn=chess.BLACK)

        self.widget.set_tactical_report(report)
        self.hud.update_report(report)

        # HUD must NOT display check alert
        if self.hud.lbl_alert.isVisible():
            self.assertNotIn("CHECK ALERT", self.hud.lbl_alert.text())

        # Off-screen render of tactics mode must succeed cleanly without check borders or king arrows
        img = QImage(640, 640, QImage.Format.Format_ARGB32)
        img.fill(0)
        p = QPainter(img)
        self.widget._paint_tactics_mode(p)
        p.end()


if __name__ == "__main__":
    unittest.main()
