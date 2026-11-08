"""
test_blunders.py
================
Unit tests for blunder detection across various tactical positions.
"""

import unittest
import chess
from projects.chess_tactical_analyzer.blunders import find_all_blunders, BlunderMove
from projects.chess_tactical_analyzer.report import generate_tactical_report


class TestBlunderDetection(unittest.TestCase):
    def test_losing_capture_blunder(self):
        # White queen on d3, Black pawn on d5 defended by knight on f6
        # If White plays Qxd5, Queen is lost for a pawn -> blunder
        board = chess.Board("rnbqkb1r/ppp1pppp/5n2/3p4/8/3Q4/PPP1PPPP/RNB1KBNR w KQkq - 0 1")
        blunders = find_all_blunders(board, chess.WHITE)
        qxd5_blunders = [b for b in blunders if board.san(b.move) == "Qxd5"]
        self.assertEqual(len(qxd5_blunders), 1)
        self.assertLess(qxd5_blunders[0].score_loss, -500)
        self.assertFalse(qxd5_blunders[0].is_mate_allowed)

    def test_quiet_move_hanging_piece_blunder(self):
        # White knight on f3 moves to e5 where Black d6 pawn can take it for free
        board = chess.Board("rnbqkb1r/ppp1pppp/3p4/8/8/5N2/PPPPPPPP/RNBQKB1R w KQkq - 0 1")
        blunders = find_all_blunders(board, chess.WHITE)
        ne5_blunders = [b for b in blunders if board.san(b.move) == "Ne5"]
        self.assertEqual(len(ne5_blunders), 1)
        self.assertLessEqual(ne5_blunders[0].score_loss, -300)
        self.assertIn("Hangs piece", ne5_blunders[0].description)

    def test_mate_in_one_blunder(self):
        # Fool's mate setup: 1. f3 e5. If White plays 2. g4, Black has 2... Qh4#
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/8/5P2/PPPPP1PP/RNBQKBNR w KQkq - 0 2")
        blunders = find_all_blunders(board, chess.WHITE)
        g4_blunders = [b for b in blunders if board.san(b.move) == "g4"]
        self.assertEqual(len(g4_blunders), 1)
        self.assertTrue(g4_blunders[0].is_mate_allowed)
        self.assertIn("mate in 1", g4_blunders[0].description)

    def test_abandoning_defender_blunder(self):
        # White Bishop on c4 is under attack by Black Rook on c8.
        # Playing a3 leaves Bishop to be captured by Rxc4.
        board = chess.Board("2r1k2r/pp1ppppp/8/8/2B5/8/PPPPPPPP/3QK2R w Kk - 0 1")
        blunders = find_all_blunders(board, chess.WHITE)
        a3_blunders = [b for b in blunders if board.san(b.move) == "a3"]
        self.assertEqual(len(a3_blunders), 1)
        self.assertLessEqual(a3_blunders[0].score_loss, -300)

    def test_capture_allowing_counter_loss_blunder(self):
        # White plays cxd5 capturing a pawn (+100 cp), but ignores Black Queen on a2
        # which can play Qxa1+ winning a Rook (-500 cp). cxd5 must be detected as a blunder.
        board = chess.Board("4k3/3p4/8/3p4/2P5/8/q7/R3K3 w - - 0 1")
        blunders = find_all_blunders(board, chess.WHITE)
        cxd5_blunders = [b for b in blunders if board.san(b.move) == "cxd5"]
        self.assertEqual(len(cxd5_blunders), 1)
        self.assertLessEqual(cxd5_blunders[0].score_loss, -400)
        # Winning capture Rxa2 must NOT be flagged as a blunder
        rxa2_blunders = [b for b in blunders if board.san(b.move) == "Rxa2"]
        self.assertEqual(len(rxa2_blunders), 0)

    def test_safe_moves_not_flagged(self):
        # Starting position: normal opening moves should not be flagged as blunders
        board = chess.Board()
        blunders = find_all_blunders(board, chess.WHITE)
        self.assertEqual(len(blunders), 0)

    def test_report_includes_blunders(self):
        # In a position with blunders, report includes them for both colors
        board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/8/5P2/PPPPP1PP/RNBQKBNR w KQkq - 0 2")
        report = generate_tactical_report(board)
        self.assertIn(chess.WHITE, report.blunders)
        white_blunders = report.blunders[chess.WHITE]
        self.assertTrue(any(b.move == chess.Move.from_uci("g2g4") for b in white_blunders))


if __name__ == "__main__":
    unittest.main()
