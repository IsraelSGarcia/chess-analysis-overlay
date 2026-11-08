"""
test_positional.py
==================
Unit tests for positional structure analysis:
- Permanent Knight Outposts
- Pawn Structure Weaknesses (Isolated, Backward, Doubled pawns, Pawn Islands)
- Open & Semi-Open File Control
- Bad Bishop Detection
- Space Advantage Evaluation
"""

import unittest
import chess

from core.shared_analysis.attack_defense import AttackDefenseMap
from projects.chess_tactical_analyzer.positional.structure import (
    find_outposts,
    analyze_pawn_structure,
    analyze_open_files,
    evaluate_bishops,
    evaluate_space,
    generate_positional_report,
    OutpostInfo,
    BishopQuality,
)


class TestPositional(unittest.TestCase):
    def test_knight_outpost_detected(self):
        # White Knight on d5, protected by White pawn on e4.
        # Black has no pawns on c or e files that could ever challenge d5 (Black pawns on a7, b7, g7, h7).
        b = chess.Board("r1bq1rk1/pp4pp/8/3N4/4P3/8/PPP3PP/R2Q1RK1 w - - 0 15")
        adm = AttackDefenseMap(b)
        outposts = find_outposts(b, adm)
        outpost_sqs = [o.square for o in outposts if o.color == chess.WHITE]
        self.assertIn(chess.D5, outpost_sqs)
        d5_outpost = [o for o in outposts if o.square == chess.D5][0]
        self.assertTrue(d5_outpost.is_occupied)
        self.assertEqual(d5_outpost.occupant_piece_type, chess.KNIGHT)

    def test_pawn_structure_isolated_pawn(self):
        # White pawn on d4 with no pawns on c or e files
        b = chess.Board("8/8/8/8/3P4/8/PP4PP/4K2k w - - 0 1")
        ps = analyze_pawn_structure(b)
        self.assertIn(chess.D4, ps.isolated[chess.WHITE])

    def test_pawn_structure_doubled_pawns(self):
        # White pawns on c3 and c4
        b = chess.Board("8/8/8/8/2P5/2P5/P5PP/4K2k w - - 0 1")
        ps = analyze_pawn_structure(b)
        self.assertIn(chess.C3, ps.doubled[chess.WHITE])
        self.assertIn(chess.C4, ps.doubled[chess.WHITE])

    def test_pawn_structure_islands(self):
        # White pawns on a2, b2 (island 1) and f2, g2, h2 (island 2) -> 2 islands
        b = chess.Board("8/8/8/8/8/8/PP3PPP/4K2k w - - 0 1")
        ps = analyze_pawn_structure(b)
        self.assertEqual(ps.pawn_islands[chess.WHITE], 2)

    def test_open_files_and_rook_control(self):
        # Open e-file (no pawns on e-file) with White Rook on e1
        b = chess.Board("4r1k1/ppp2ppp/8/8/8/8/PPP2PPP/4R1K1 w - - 0 1")
        open_files = analyze_open_files(b)
        e_files = [f for f in open_files if f.file_idx == 4]  # e-file is file 4
        self.assertEqual(len(e_files), 1)
        ef = e_files[0]
        self.assertTrue(ef.is_completely_open)
        self.assertIn(chess.E1, ef.rooks_controlling[chess.WHITE])
        self.assertIn(chess.E8, ef.rooks_controlling[chess.BLACK])

    def test_semi_open_file(self):
        # c-file: White has no pawn on c-file, Black has pawn on c7 -> semi-open for White
        b = chess.Board("r1bqkb1r/pp1ppppp/2n5/8/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 0 4")
        open_files = analyze_open_files(b)
        c_files = [f for f in open_files if f.file_idx == 2]  # c-file is file 2
        self.assertEqual(len(c_files), 1)
        cf = c_files[0]
        self.assertFalse(cf.is_completely_open)
        self.assertEqual(cf.is_semi_open_for, chess.BLACK)

    def test_bad_bishop_detection(self):
        # White Dark-Squared Bishop on c1 with 4 friendly pawns on dark squares (a3, c3, e3, g3)
        b = chess.Board("8/8/8/8/8/P1P1P1P1/8/2B1K2k w - - 0 1")
        bishops = evaluate_bishops(b)
        self.assertEqual(len(bishops), 1)
        b_c1 = bishops[0]
        self.assertEqual(b_c1.square, chess.C1)
        self.assertFalse(b_c1.is_light_squared)
        self.assertTrue(b_c1.is_bad)
        self.assertGreaterEqual(b_c1.friendly_pawns_on_same_color, 4)

    def test_active_bishop_not_bad(self):
        # White Bishop on e3 with pawns on dark squares (c2, e4)
        b = chess.Board("8/8/8/8/4P3/4B3/2P5/4K2k w - - 0 1")
        bishops = evaluate_bishops(b)
        self.assertEqual(len(bishops), 1)
        self.assertFalse(bishops[0].is_bad)

    def test_space_control_evaluation(self):
        b = chess.Board()
        adm = AttackDefenseMap(b)
        space = evaluate_space(b, adm)
        # Starting position has some central square control on 4th / 5th rank
        self.assertIsInstance(space[chess.WHITE], int)
        self.assertIsInstance(space[chess.BLACK], int)

    def test_generate_positional_report(self):
        b = chess.Board("r1bq1rk1/pp4pp/8/3N4/4P3/8/PPP3PP/R2Q1RK1 w - - 0 15")
        adm = AttackDefenseMap(b)
        report = generate_positional_report(b, adm)
        self.assertIsNotNone(report)
        self.assertGreater(len(report.outposts), 0)
        self.assertIsNotNone(report.pawn_structure)
        self.assertIsInstance(report.open_files, list)


if __name__ == "__main__":
    unittest.main()
