"""
test_tactical.py
================
Unit tests for the standalone chess_tactical analytical engine:
- Static Exchange Evaluation (SEE)
- Attack and defense maps & square control
- Pin & skewer detection
- Hanging piece detection
- Fork & discovered attack detection
- Forcing sequence search
"""

import unittest
import chess

from projects.chess_tactical_analyzer import (
    ExchangeCategory,
    evaluate_exchange,
    evaluate_all_captures,
    AttackDefenseMap,
    find_hanging_pieces,
    scan_all_motifs,
    find_forks,
    find_skewers,
    find_back_rank_weaknesses,
    find_mating_threats,
    find_removing_the_defender,
    find_deflection_tactics,
    MotifType,
    calculate_tactical_sequences,
    find_trapped_pieces,
    find_xray_rays,
    generate_tactical_report,
)


class TestStaticExchangeEvaluation(unittest.TestCase):
    """Test Static Exchange Evaluation (SEE) accuracy."""

    def test_free_piece_capture(self):
        # White Queen on e2 captures undefended Black Knight on e4
        board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/4n3/8/PPPPQPPP/RNB1KBNR w KQkq - 0 1")
        move = chess.Move.from_uci("e2e4")
        result = evaluate_exchange(board, move)

        self.assertTrue(result.is_favorable)
        self.assertEqual(result.category, ExchangeCategory.FREE_PIECE)
        self.assertGreaterEqual(result.score, 300)

    def test_losing_exchange(self):
        # White Knight on f3 captures defended Black Pawn on e5 (defended by d6 pawn)
        board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
        # Add pawn on d6 to defend e5
        board.set_piece_at(chess.D6, chess.Piece(chess.PAWN, chess.BLACK))
        move = chess.Move.from_uci("f3e5")
        result = evaluate_exchange(board, move)

        self.assertTrue(result.is_dangerous)
        self.assertEqual(result.category, ExchangeCategory.LOSING)
        self.assertLess(result.score, -100)

    def test_equal_trade(self):
        # White Bishop on b5 captures Black Knight on c6 defended by b7 pawn
        board = chess.Board("r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 1")
        move = chess.Move.from_uci("b5c6")
        result = evaluate_exchange(board, move)

        # Bishop (330) traded for Knight (305) -> net delta is roughly -25 cp (equal trade)
        self.assertTrue(result.is_equal)
        self.assertIn("bxc6", result.sequence)

    def test_en_passant_see(self):
        # White pawn on e5, Black pawn just moved d7-d5
        board = chess.Board("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 2")
        move = chess.Move.from_uci("e5d6")
        result = evaluate_exchange(board, move)

        # Black pawn on d5 was free, or defended by c7/e7/Qd8
        self.assertEqual(result.target_piece_type, chess.PAWN)
        self.assertIn("exd6", result.sequence)


class TestAttackDefenseMap(unittest.TestCase):
    """Test attack/defense tracking, pins, and discovered attacks."""

    def test_attack_and_defense_counts(self):
        # Starting position: e4 square is attacked by White (Bf1, Ng1 if moved, etc.)
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        am = AttackDefenseMap(board)

        # e4 is defended by White Knight c3 and White Pawn d3
        self.assertIn(chess.C3, am.squares[chess.E4].white_attackers)
        self.assertIn(chess.D3, am.squares[chess.E4].white_attackers)

    def test_absolute_pin_detection(self):
        # Black Bishop on b4 pins White Knight on c3 to White King on e1
        board = chess.Board("r1bqk2r/pppp1ppp/5n2/4p3/1b2P3/2NP4/PPP1BPPP/R1BQK2R b KQkq - 0 1")
        am = AttackDefenseMap(board)

        # Pin should be identified
        pins = [p for p in am.pins if p.pinned_square == chess.C3 and p.is_absolute]
        self.assertEqual(len(pins), 1)
        self.assertEqual(pins[0].pinner_square, chess.B4)
        self.assertEqual(pins[0].shielded_square, chess.E1)

    def test_relative_pin_detection(self):
        # White Bishop on g5 pins Black Knight on f6 to Black Queen on d8
        board = chess.Board("rnbqkb1r/pppp1ppp/5n2/4p1B1/4P3/3P4/PPP2PPP/RN1QKBNR b KQkq - 0 1")
        am = AttackDefenseMap(board)

        pins = [p for p in am.pins if p.pinned_square == chess.F6 and not p.is_absolute]
        self.assertEqual(len(pins), 1)
        self.assertEqual(pins[0].pinner_square, chess.G5)
        self.assertEqual(pins[0].shielded_square, chess.D8)


class TestHangingPieces(unittest.TestCase):
    """Test detection of genuinely hanging pieces."""

    def test_undefended_hanging_piece(self):
        # Black Knight on e4 is completely undefended and attacked by White Queen on e2
        board = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/4n3/8/PPPPQPPP/RNB1KBNR w KQkq - 0 1")
        hanging = find_hanging_pieces(board, color=chess.BLACK)

        self.assertEqual(len(hanging), 1)
        self.assertEqual(hanging[0].square, chess.E4)
        self.assertTrue(hanging[0].is_undefended)
        self.assertTrue(hanging[0].is_tactically_vulnerable)

    def test_defended_piece_not_hanging(self):
        # 1. e4 e5 2. Nf3 Nc6 -> Black pawn on e5 defended by Nc6
        board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1")
        hanging = find_hanging_pieces(board, color=chess.BLACK)

        # e5 should NOT be reported as hanging
        e5_hanging = [h for h in hanging if h.square == chess.E5]
        self.assertEqual(len(e5_hanging), 0)


class TestTacticalMotifs(unittest.TestCase):
    """Test tactical pattern recognition."""

    def test_knight_fork(self):
        # White Knight on c7 forks Black Rook on a8 and King on e8
        board = chess.Board("r1b1k2r/ppNp1ppp/8/4p3/1b2P3/3P1N2/PPPB1PPP/R3KB1R b KQkq - 0 1")
        am = AttackDefenseMap(board)
        forks = find_forks(board, am)

        self.assertTrue(any(f.source_square == chess.C7 for f in forks))

    def test_skewer(self):
        # White Rook on e1 skewers Black King on e5 in front of Black Queen on e7
        board = chess.Board("8/4q3/8/4k3/8/8/8/4R1K1 w - - 0 1")
        skewers = find_skewers(board)

        self.assertEqual(len(skewers), 1)
        self.assertEqual(skewers[0].source_square, chess.E1)
        self.assertEqual(skewers[0].target_squares, (chess.E5, chess.E7))

    def test_back_rank_weakness(self):
        # Black King on g8 behind f7, g7, h7 pawns, White Rook on a1 can infiltrate
        board = chess.Board("6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
        weaknesses = find_back_rank_weaknesses(board)

        self.assertTrue(len(weaknesses) >= 1)
        self.assertEqual(weaknesses[0].target_squares, (chess.G8,))
    def test_back_rank_weakness_resolved_by_luft(self):
        # Black King on g8 has luft on h7 because h6 pawn was pushed; White Rook on a1 cannot exploit
        board = chess.Board("6k1/5pp1/7p/8/8/8/8/R3K3 w - - 0 1")
        weaknesses = find_back_rank_weaknesses(board)
        self.assertEqual(len(weaknesses), 0)


class TestAdvancedMotifs(unittest.TestCase):
    """Test mating threats, removing defender, and deflection tactics."""

    def test_immediate_mating_threat(self):
        # Scholar's mate setup: White Queen on h5 and Bishop on c4 attack f7
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4")
        threats = find_mating_threats(board)
        mating_moves = [t for t in threats if t.color == chess.WHITE]
        self.assertTrue(any(t.target_squares == (chess.F7,) for t in mating_moves))

    def test_opponent_mating_threat(self):
        # Same setup, but it is Black to move: Black must see White's imminent threat against f7
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR b KQkq - 4 4")
        threats = find_mating_threats(board)
        white_threats = [t for t in threats if t.color == chess.WHITE]
        self.assertTrue(any(t.target_squares == (chess.F7,) for t in white_threats))

    def test_removing_the_defender(self):
        # White Knight on f3 defends Bishop on d4. Black Rook on f8 attacks Knight on f3.
        # White Bishop on d4 is attacked by Black Queen on d8.
        board = chess.Board("3q1rk1/6pp/8/8/3B4/5N2/8/4K3 b - - 0 1")
        attack_map = AttackDefenseMap(board)
        motifs = find_removing_the_defender(board, attack_map)
        matching = [
            m for m in motifs
            if m.motif_type == MotifType.REMOVING_DEFENDER
            and m.source_square == chess.F8
            and m.target_squares == (chess.F3, chess.D4)
        ]
        self.assertEqual(len(matching), 1)

    def test_deflection_tactic(self):
        # White Queen on e2 defends Knight on e4 which is attacked by Black Rook on e8.
        # Black Bishop on g4 attacks White Queen on e2 (deflecting Queen away from e4).
        board = chess.Board("4r1k1/5ppp/8/8/4N1b1/8/4QPPP/4K3 b - - 0 1")
        attack_map = AttackDefenseMap(board)
        deflections = find_deflection_tactics(board, attack_map)
        matching = [
            d for d in deflections
            if d.motif_type == MotifType.DEFLECTION
            and d.source_square == chess.G4
            and d.target_squares == (chess.E2, chess.E4)
        ]
        self.assertEqual(len(matching), 1)



class TestForcingTacticalSearch(unittest.TestCase):
    """Test forcing move tactical calculations."""

    def test_back_rank_mate_in_one(self):
        board = chess.Board("6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1")
        seqs = calculate_tactical_sequences(board, color=chess.WHITE, max_depth=3)

        self.assertTrue(len(seqs) >= 1)
        self.assertTrue(seqs[0].is_mate)
        self.assertEqual(seqs[0].root_move, chess.Move.from_uci("a1a8"))

    def test_scholar_mate(self):
        # 1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 ?? Qxf7#
        board = chess.Board("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 0 1")
        seqs = calculate_tactical_sequences(board, color=chess.WHITE, max_depth=3)

        self.assertTrue(len(seqs) >= 1)
        self.assertEqual(seqs[0].root_move, chess.Move.from_uci("h5f7"))
        self.assertTrue(seqs[0].is_mate)


class TestTacticalReport(unittest.TestCase):
    """Test the integrated TacticalReport."""

    def test_full_report_generation(self):
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        report = generate_tactical_report(board, search_depth=3)

        self.assertIsNotNone(report.attack_map)
        self.assertIn(chess.WHITE, report.captures)
        self.assertIn(chess.BLACK, report.captures)
        self.assertIsInstance(report.summary_lines(), list)
        self.assertGreater(len(report.summary_lines()), 0)
        self.assertIn(chess.WHITE, report.trapped_pieces)
        self.assertIn(chess.BLACK, report.trapped_pieces)
        self.assertIsInstance(report.xray_rays, list)
        # Verify multi-ply forcing minimax sequences are disabled per 0-ply pure non-engine geometric design
        self.assertEqual(len(report.forcing_sequences[chess.WHITE]), 0)
        self.assertEqual(len(report.forcing_sequences[chess.BLACK]), 0)


class TestTrappedPieces(unittest.TestCase):
    """Test trapped piece detection."""

    def test_noahs_ark_trapped_bishop(self):
        # Position after 11... c4 in Noah's Ark trap: White bishop on b3 is trapped
        board = chess.Board("r2qkb1r/3b1ppp/p2p4/1p1Q4/2p1P3/1B6/PPP2PPP/RNB1K2R w KQkq - 0 12")
        trapped = find_trapped_pieces(board)
        white_trapped = trapped[chess.WHITE]
        self.assertEqual(len(white_trapped), 1)
        self.assertEqual(white_trapped[0].square, chess.B3)
        self.assertEqual(white_trapped[0].piece_type, chess.BISHOP)

    def test_trapped_knight_on_rim(self):
        # Black knight trapped on h1
        board = chess.Board("r1b1k2r/pppp1ppp/8/8/8/8/PPP2PPP/RNB1K2n w Qkq - 0 1")
        trapped = find_trapped_pieces(board)
        black_trapped = trapped[chess.BLACK]
        self.assertEqual(len(black_trapped), 1)
        self.assertEqual(black_trapped[0].square, chess.H1)
        self.assertEqual(black_trapped[0].piece_type, chess.KNIGHT)

    def test_starting_position_no_trapped_pieces(self):
        board = chess.Board()
        trapped = find_trapped_pieces(board)
        self.assertEqual(len(trapped[chess.WHITE]), 0)
        self.assertEqual(len(trapped[chess.BLACK]), 0)

    def test_pinned_piece_not_falsely_trapped(self):
        # White knight on c3 is pinned to King on e1; it should not be reported as trapped
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        trapped = find_trapped_pieces(board)
        c3_trapped = [t for t in trapped[chess.WHITE] if t.square == chess.C3]
        self.assertEqual(len(c3_trapped), 0)


class TestXRayRays(unittest.TestCase):
    """Test slider X-ray ray detection."""

    def test_bishop_xray_on_enemy_king(self):
        # Black bishop on b4 X-rays King on e1 through Knight on c3
        board = chess.Board("r1bqk2r/pppp1ppp/2n5/4p3/1bB1P1n1/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 1")
        rays = find_xray_rays(board)
        matching = [
            r for r in rays
            if r.slider_square == chess.B4
            and r.intervening_square == chess.C3
            and r.target_square == chess.E1
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].slider_type, chess.BISHOP)
        self.assertEqual(matching[0].target_type, chess.KING)

    def test_queen_open_file_xray(self):
        # White Queen on d1 X-rays Black Queen on d8 through pawn on d7
        board = chess.Board("r1bqk2r/pp1p1pbp/2n1p1p1/8/4P3/1PN5/PBP2PPP/R2QKB1R w KQkq - 0 9")
        rays = find_xray_rays(board)
        matching = [
            r for r in rays
            if r.slider_square == chess.D1
            and r.target_square == chess.D8
        ]
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].intervening_square, chess.D7)


if __name__ == "__main__":
    unittest.main()
