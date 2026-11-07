"""
test_transitions.py
===================
Unit tests for board physical continuity, state transition sanitization,
and turn determination using transitions.py.
"""

import unittest
import chess
from chess_visualizer.transitions import (
    determine_turn_from_move,
    sanitize_board_transition,
    generate_candidate_moves,
)


class TestTransitions(unittest.TestCase):

    def test_forward_move_turn_determination(self):
        b0 = chess.Board()
        b1 = b0.copy()
        b1.push_san("e4")

        # White moved e4 -> Black's turn next
        self.assertEqual(determine_turn_from_move(b0, b1), chess.BLACK)

    def test_undo_move_turn_determination(self):
        b0 = chess.Board()
        b1 = b0.copy()
        b1.push_san("e4")

        # Going from b1 back to b0 is an undo -> White's turn again
        self.assertEqual(determine_turn_from_move(b1, b0), chess.WHITE)

    def test_sanitize_phantom_move_dots(self):
        b0 = chess.Board()
        b1 = b0.copy()
        # Phantom piece appears on d4 without any piece leaving
        b1.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.WHITE))

        sanitized = sanitize_board_transition(b0, b1)
        self.assertIsNone(sanitized.piece_at(chess.D4))
        self.assertEqual(sanitized.piece_map(), b0.piece_map())

    def test_candidate_moves_en_passant(self):
        # White pawn on e5, Black pawn on d5 with ep square available
        b = chess.Board("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
        moves = list(generate_candidate_moves(b))
        ep_move = chess.Move.from_uci("e5d6")
        self.assertIn(ep_move, moves)


if __name__ == "__main__":
    unittest.main()
