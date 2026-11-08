"""
test_openings.py
================
Unit tests for Opening Book classification, ECO code detection,
and opening trap recognition.
"""

import unittest
import chess

from projects.chess_tactical_analyzer.openings.book import (
    identify_opening,
    identify_opening_from_moves,
    is_opening_phase,
    OpeningInfo,
)
from projects.chess_tactical_analyzer.openings.traps import (
    detect_opening_traps,
    OpeningTrap,
)


class TestOpenings(unittest.TestCase):
    def test_identify_sicilian_najdorf(self):
        moves = ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "B90")
        self.assertIn("Sicilian", info.name)
        self.assertIn("Najdorf", info.variation)

    def test_identify_ruy_lopez_berlin(self):
        moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5", "g8f6"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "C65")
        self.assertIn("Ruy Lopez", info.name)
        self.assertIn("Berlin", info.variation)

    def test_identify_french_defense(self):
        moves = ["e2e4", "e7e6", "d2d4", "d7d5"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "C00")
        self.assertIn("French Defense", info.name)

    def test_identify_caro_kann(self):
        moves = ["e2e4", "c7c6", "d2d4", "d7d5"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "B12")
        self.assertIn("Caro-Kann", info.name)

    def test_identify_queens_gambit(self):
        moves = ["d2d4", "d7d5", "c2c4"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "D06")
        self.assertIn("Queen's Gambit", info.name)

    def test_identify_kings_indian(self):
        moves = ["d2d4", "g8f6", "c2c4", "g7g6", "b1c3", "f8g7", "e2e4", "d7d6"]
        info = identify_opening_from_moves(moves)
        self.assertIsNotNone(info)
        self.assertEqual(info.eco, "E70")
        self.assertIn("King's Indian", info.name)

    def test_identify_empty_moves_returns_none(self):
        self.assertIsNone(identify_opening_from_moves([]))

    def test_identify_from_board_fen_without_move_stack(self):
        # Starting position with no moves
        b0 = chess.Board()
        info0 = identify_opening(b0)
        self.assertIsNotNone(info0)
        self.assertIn("Starting Position", info0.name)

        # 1. e4 c5 Sicilian Defense
        b_sic = chess.Board("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        info_sic = identify_opening(b_sic)
        self.assertIsNotNone(info_sic)
        self.assertEqual(info_sic.eco, "B20")
        self.assertIn("Sicilian", info_sic.name)

        # 1. e4 e6 French Defense
        b_fr = chess.Board("rnbqkbnr/pppp1ppp/4p3/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        info_fr = identify_opening(b_fr)
        self.assertIsNotNone(info_fr)
        self.assertEqual(info_fr.eco, "C00")

    def test_opening_phase_detection(self):
        # Starting position is in opening phase
        b = chess.Board()
        self.assertTrue(is_opening_phase(b))

        # Position at move 25 is not opening phase
        b.fullmove_number = 25
        self.assertFalse(is_opening_phase(b))

        # Position with only 10 pieces left is not opening phase
        endgame_b = chess.Board("8/8/4k3/8/8/4K3/4P3/8 w - - 0 40")
        self.assertFalse(is_opening_phase(endgame_b))

    def test_noahs_ark_trap(self):
        # White Bishop trapped on b3 by Black pawns c4, b5, a6, d6
        b = chess.Board("r1bq1rk1/2p2ppp/p2p4/1p6/2P1P3/1B6/PP1P1PPP/RNBQK2R w KQ - 0 10")
        b.set_piece_at(chess.C4, chess.Piece(chess.PAWN, chess.BLACK))
        traps = detect_opening_traps(b)
        names = [t.name for t in traps]
        self.assertIn("Noah's Ark Trap", names)

    def test_fishing_pole_trap(self):
        # White King on g1 with h3; Black Ng4, h5 pawn, h8 rook
        b = chess.Board("r1bqk2r/pppp1pp1/2n5/4p3/2B1P1n1/3P1P1P/PPP3P1/RNBQ1RK1 b kq - 0 7")
        b.set_piece_at(chess.H5, chess.Piece(chess.PAWN, chess.BLACK))
        b.set_piece_at(chess.G4, chess.Piece(chess.KNIGHT, chess.BLACK))
        b.set_piece_at(chess.H3, chess.Piece(chess.PAWN, chess.WHITE))
        traps = detect_opening_traps(b)
        names = [t.name for t in traps]
        self.assertIn("Fishing Pole Trap", names)

    def test_legal_trap(self):
        # White Bc4, Ne5; Black Bg4, Ke8, f7 pawn
        b = chess.Board("r2qk2r/ppp2ppp/2np4/2b1N3/2B1P1b1/2NP4/PPP2PPP/R1BQK2R b KQkq - 0 7")
        traps = detect_opening_traps(b)
        names = [t.name for t in traps]
        self.assertIn("Légal Trap", names)


if __name__ == "__main__":
    unittest.main()
