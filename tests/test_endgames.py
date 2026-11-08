"""
test_endgames.py
================
Unit tests for 0-ply endgame geometric principles:
- Rule of the Square (Runaway passed pawn promotion races)
- King Opposition (Direct, Distant, Diagonal)
- Passed Pawn Classification (Protected, Outside, Connected)
"""

import unittest
import chess

from projects.chess_tactical_analyzer.endgames.rules import (
    is_endgame,
    is_passed_pawn,
    evaluate_runaway_passed_pawns,
    detect_king_opposition,
    classify_passed_pawns,
    RunawayPawnInfo,
    OppositionInfo,
)


class TestEndgames(unittest.TestCase):
    def test_is_endgame(self):
        # Starting position is not endgame
        b = chess.Board()
        self.assertFalse(is_endgame(b))

        # 4 pieces on board is endgame
        b_kpk = chess.Board("8/8/4k3/8/4P3/8/8/4K3 w - - 0 1")
        self.assertTrue(is_endgame(b_kpk))

        # 14 pieces with no queens is endgame
        b_no_queens = chess.Board("4k2r/pp3ppp/8/8/8/8/PP3PPP/4R1K1 w - - 0 25")
        self.assertTrue(is_endgame(b_no_queens))

    def test_rule_of_the_square_runaway_pawn(self):
        # White pawn on a5, Black king far away on h8.
        # Square of a5 extends to file e, ranks 5..8. Black king on h8 is OUTSIDE.
        b = chess.Board("7k/8/8/P7/8/8/8/4K3 w - - 0 1")
        runaways = evaluate_runaway_passed_pawns(b)
        self.assertEqual(len(runaways), 1)
        r = runaways[0]
        self.assertEqual(r.pawn_square, chess.A5)
        self.assertFalse(r.is_king_inside)
        self.assertTrue(r.can_promote_unstoppably)

    def test_rule_of_the_square_king_inside(self):
        # White pawn on a5, Black king on b7 (directly inside the square)
        b = chess.Board("8/1k6/8/P7/8/8/8/4K3 w - - 0 1")
        runaways = evaluate_runaway_passed_pawns(b)
        self.assertEqual(len(runaways), 1)
        r = runaways[0]
        self.assertTrue(r.is_king_inside)
        self.assertFalse(r.can_promote_unstoppably)

    def test_rule_of_the_square_rank2_double_jump(self):
        # White pawn on a2 (rank index 1). Because of double jump, its effective rank is 2 (a3).
        # Distance to rank 7 (8th rank) is 7 - 2 = 5 squares.
        # Black king on g7: file 6, rank 6.
        b = chess.Board("8/6k1/8/8/8/8/P7/4K3 w - - 0 1")
        runaways = evaluate_runaway_passed_pawns(b)
        self.assertEqual(len(runaways), 1)
        r = runaways[0]
        # Since White is on move, distance is reduced by 1
        self.assertEqual(r.pawn_square, chess.A2)

    def test_direct_opposition(self):
        # White King on e4, Black King on e6. 2 squares apart along e-file.
        b = chess.Board("8/8/4k3/8/4K3/8/8/8 b - - 0 1")
        opp = detect_king_opposition(b)
        self.assertIsNotNone(opp)
        self.assertEqual(opp.kind, "direct")
        # Since it is Black's turn (b), White holds the opposition
        self.assertEqual(opp.holder_color, chess.WHITE)

    def test_distant_opposition(self):
        # White King on e3, Black King on e7. 4 squares apart along e-file.
        b = chess.Board("8/4k3/8/8/8/4K3/8/8 w - - 0 1")
        opp = detect_king_opposition(b)
        self.assertIsNotNone(opp)
        self.assertEqual(opp.kind, "distant")
        # Since it is White's turn (w), Black holds the opposition
        self.assertEqual(opp.holder_color, chess.BLACK)

    def test_diagonal_opposition(self):
        # White King on d4, Black King on f6. 2 squares away diagonally.
        b = chess.Board("8/8/5k2/8/3K4/8/8/8 w - - 0 1")
        opp = detect_king_opposition(b)
        self.assertIsNotNone(opp)
        self.assertEqual(opp.kind, "diagonal")

    def test_classify_passed_pawns(self):
        # White pawn on e5 defended by d4 pawn -> "protected"
        # White pawn on a5 with no neighbors on a-file -> "outside"
        b = chess.Board("8/8/8/P3P3/3P4/8/8/4K2k w - - 0 1")
        passers = classify_passed_pawns(b)
        categories = {p.square: p.category for p in passers}
        self.assertEqual(categories.get(chess.E5), "protected")
        self.assertEqual(categories.get(chess.A5), "outside")


if __name__ == "__main__":
    unittest.main()
