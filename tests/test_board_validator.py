"""
test_board_validator.py
=======================
Tests for board recognition plausibility validation.
Guarantees false-positive prevention and protects against corrupted crops.
"""

import unittest
import chess
from core.chess_rules.validator import is_valid_recognized_board


class TestBoardValidator(unittest.TestCase):

    def test_standard_starting_board(self):
        board = chess.Board()
        self.assertTrue(is_valid_recognized_board(board))

    def test_valid_sicilian_board(self):
        board = chess.Board("r1bqkbnr/pp1ppppp/2n5/2p5/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
        self.assertTrue(is_valid_recognized_board(board))

    def test_valid_endgame_board(self):
        # King + Rook vs King
        board = chess.Board("8/8/8/4k3/8/8/R7/4K3 w - - 0 1")
        self.assertTrue(is_valid_recognized_board(board))

    def test_reject_corrupted_16_rook_board(self):
        # Actual corrupted board that caused stack overflow crash
        board = chess.Board("rR3r2/rRpq1pk1/r1n2np1/b1rppp1p/RR1P3P/r1N1P1P1/RBPP1P2/R2QK1N1 b Q - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_missing_king(self):
        # No White King
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQ1BNR w - - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_multiple_kings(self):
        # Two White Kings
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNK w - - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_pawn_on_rank_1(self):
        # Pawn on a1 (impossible in chess, sign of shifted crop)
        board = chess.Board("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/PnBQKBNR w KQkq - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_pawn_on_rank_8(self):
        # Black Pawn on h8
        board = chess.Board("rnbqkbnP/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_more_than_16_pieces(self):
        # 17 White pieces
        board = chess.Board("rnbqkbnr/pppppppp/8/4P3/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_more_than_8_pawns(self):
        # 9 White pawns
        board = chess.Board("rnbqkbnr/8/8/8/8/1P6/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_empty_board(self):
        board = chess.Board(None)
        self.assertFalse(is_valid_recognized_board(board))

    def test_reject_both_kings_in_check(self):
        # White King on h1 attacked by Black Rook on a1; Black King on h8 attacked by White Rook on a8
        board = chess.Board("R6k/8/8/8/8/8/8/r6K w - - 0 1")
        self.assertFalse(is_valid_recognized_board(board))


if __name__ == "__main__":
    unittest.main()
