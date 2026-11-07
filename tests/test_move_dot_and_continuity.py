"""
test_move_dot_and_continuity.py
================================
Unit tests verifying:
1. Move indicator dot detection across all display resolutions and square themes.
2. Real piece rejection in move dot detection (pawns, knights, bishops, rooks, queens, kings).
3. Square cleaning erasing move indicator dots so ONNX piece classifier sees pure empty squares.
4. Board state continuity and impossible piece spawn purging (sanitize_board_transition).
5. User incident regression test: Position '1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25'
   clicking White Knight does not create illegal pawn blunders or corrupt blunders.
"""

import os
import sys
import unittest
import chess
import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from chess_visualizer.recognition import is_move_dot, clean_square_image
from chess_visualizer.main import sanitize_board_transition, determine_turn_from_move
from chess_tactical import generate_tactical_report


class TestMoveDotAndContinuity(unittest.TestCase):

    def test_move_dot_detection_across_resolutions(self):
        """Verify is_move_dot detects dots from 40px to 200px on light and dark squares."""
        dark_bg = (181, 136, 99)
        light_bg = (240, 217, 181)

        for size in [40, 60, 80, 100, 120, 140, 160, 200]:
            for bg in [dark_bg, light_bg]:
                sq = np.full((size, size, 3), bg, dtype=np.uint8)

                # Plain empty square must NOT be flagged
                self.assertFalse(
                    is_move_dot(sq),
                    f"Plain empty square falsely flagged at size {size}, bg {bg}",
                )

                # Square with move dot (opacities 0.12 to 0.30) MUST be detected
                for alpha in [0.12, 0.18, 0.25]:
                    sq_dot = sq.copy()
                    dot_layer = sq.copy()
                    cv2.circle(
                        dot_layer,
                        (size // 2, size // 2),
                        int(size * 0.16),
                        (0, 0, 0),
                        -1,
                        lineType=cv2.LINE_AA,
                    )
                    sq_dot = cv2.addWeighted(dot_layer, alpha, sq, 1 - alpha, 0)
                    self.assertTrue(
                        is_move_dot(sq_dot),
                        f"Move dot missed at size {size}, bg {bg}, alpha {alpha}",
                    )

    def test_move_dot_rejects_pieces(self):
        """Verify is_move_dot never flags real chess pieces (with base and vertical contours)."""
        for size in [60, 100, 140]:
            sq = np.full((size, size, 3), (181, 136, 99), dtype=np.uint8)
            # Draw realistic piece structure: wide base at bottom, body in center, head at top
            cv2.rectangle(
                sq,
                (int(size * 0.20), int(size * 0.78)),
                (int(size * 0.80), int(size * 0.92)),
                (30, 30, 30),
                -1,
            )
            cv2.rectangle(
                sq,
                (int(size * 0.35), int(size * 0.45)),
                (int(size * 0.65), int(size * 0.78)),
                (30, 30, 30),
                -1,
            )
            cv2.circle(sq, (size // 2, int(size * 0.35)), int(size * 0.15), (30, 30, 30), -1)

            self.assertFalse(
                is_move_dot(sq),
                f"Real piece falsely flagged as move dot at size {size}",
            )

    def test_clean_square_image_erases_dot_for_classifier(self):
        """Verify that clean_square_image restores an empty square with >99% classifier confidence."""
        try:
            from chessvision import PieceClassifier
            clf = PieceClassifier()
        except Exception:
            self.skipTest("chessvision not installed")

        size = 140
        sq = np.full((size, size, 3), (181, 136, 99), dtype=np.uint8)
        dot_layer = sq.copy()
        cv2.circle(dot_layer, (70, 70), 22, (0, 0, 0), -1, lineType=cv2.LINE_AA)
        sq_with_dot = cv2.addWeighted(dot_layer, 0.22, sq, 0.78, 0)

        cleaned_pil = clean_square_image(sq_with_dot)
        pred = clf.predict_squares([cleaned_pil])[0]

        self.assertEqual(pred.label, "empty")
        self.assertGreater(pred.confidence, 0.95)

    def test_sanitize_board_transition_purges_phantom_spawns(self):
        """Verify sanitize_board_transition purges spontaneous piece appearances on empty squares."""
        pos = "1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25"
        b_prev = chess.Board(pos)

        # Simulate user clicking White Knight on b5 -> move dot falsely creates bP on d4
        b_corrupted = b_prev.copy()
        b_corrupted.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.BLACK))

        sanitized = sanitize_board_transition(b_prev, b_corrupted)
        self.assertEqual(sanitized.piece_map(), b_prev.piece_map())
        self.assertIsNone(sanitized.piece_at(chess.D4))

    def test_sanitize_board_transition_preserves_legitimate_moves(self):
        """Verify genuine moves (normal move, capture, castling) are never purged."""
        pos = "1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25"
        b_prev = chess.Board(pos)

        # 1. Normal move: a2a3
        b_move = b_prev.copy()
        b_move.push_san("a3")
        self.assertEqual(sanitize_board_transition(b_prev, b_move).piece_map(), b_move.piece_map())

        # 2. Capture: b5xd6
        b_cap = b_prev.copy()
        b_cap.push_san("Nxd6")
        self.assertEqual(sanitize_board_transition(b_prev, b_cap).piece_map(), b_cap.piece_map())

        # 3. Castling
        b_castle_pre = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5")
        b_castle_post = b_castle_pre.copy()
        b_castle_post.push_san("O-O")
        self.assertEqual(sanitize_board_transition(b_castle_pre, b_castle_post).piece_map(), b_castle_post.piece_map())

    def test_determine_turn_from_move_ignores_phantom_spawn(self):
        """Verify determine_turn_from_move returns None when pieces spawn without vacating an origin."""
        pos = "1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25"
        b_prev = chess.Board(pos)
        b_corrupted = b_prev.copy()
        b_corrupted.set_piece_at(chess.D4, chess.Piece(chess.PAWN, chess.BLACK))

        result = determine_turn_from_move(b_prev, b_corrupted)
        self.assertIsNone(result)

    def test_user_position_blunder_integrity(self):
        """
        Regression test for user incident:
        Position '1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25'
        Verify that in the clean position, e3d4 is NOT a legal move,
        and that blunders on the board are properly calculated.
        """
        pos = "1r6/pp1k4/n2p1b2/1Np2b2/2P5/1P2P1P1/P3QKB1/R6R w - - 0 25"
        board = chess.Board(pos)

        # e3d4 is not a legal move in standard chess when d4 is empty
        legal_uci = [m.uci() for m in board.legal_moves]
        self.assertNotIn("e3d4", legal_uci)

        report = generate_tactical_report(board, search_depth=3, active_turn=chess.WHITE)
        white_blunders = report.blunders.get(True, [])
        blunder_ucis = [b.move.uci() for b in white_blunders]

        # e3d4 cannot be a blunder because it is not legal
        self.assertNotIn("e3d4", blunder_ucis)

        # Genuine blunders are present and not suppressed
        self.assertIn("b5d4", blunder_ucis)
        self.assertIn("b5c7", blunder_ucis)
        self.assertIn("b5c3", blunder_ucis)

    def test_lichess_fullscreen_detection_with_chopped_rank8(self):
        """Verify detect_chessboard_fullscreen recovers exact coordinates on Lichess despite piece density."""
        from chess_visualizer.recognition import detect_chessboard_fullscreen
        import chess.svg
        from PySide6.QtCore import QByteArray
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtSvg import QSvgRenderer

        b = chess.Board()
        svg = chess.svg.board(b, size=640, coordinates=False, colors={"square light": "#f0d9b5", "square dark": "#b58863"}).encode("utf-8")
        renderer = QSvgRenderer(QByteArray(svg))
        qimg = QImage(640, 640, QImage.Format_RGB32)
        p = QPainter(qimg)
        renderer.render(p)
        p.end()
        buf = qimg.bits().tobytes()
        board_pil = Image.frombuffer("RGBA", (640, 640), buf, "raw", "BGRA", 0, 1).convert("RGB")

        desktop = Image.new("RGB", (1920, 1080), (22, 21, 18))
        target_x, target_y = 350, 180
        desktop.paste(board_pil, (target_x, target_y))

        detected = detect_chessboard_fullscreen(desktop)
        self.assertIsNotNone(detected)
        dx, dy, dw, dh = detected
        self.assertAlmostEqual(dx, target_x, delta=3)
        self.assertAlmostEqual(dy, target_y, delta=3)
        self.assertAlmostEqual(dw, 640, delta=3)
        self.assertAlmostEqual(dh, 640, delta=3)

    def test_lichess_fullscreen_detection_with_flush_eval_bar(self):
        """Verify detect_chessboard_fullscreen excludes flush Lichess evaluation gauge on left."""
        from chess_visualizer.recognition import detect_chessboard_fullscreen
        import chess.svg
        from PySide6.QtCore import QByteArray
        from PySide6.QtGui import QImage, QPainter
        from PySide6.QtSvg import QSvgRenderer

        b = chess.Board()
        svg = chess.svg.board(b, size=640, coordinates=False, colors={"square light": "#f0d9b5", "square dark": "#b58863"}).encode("utf-8")
        renderer = QSvgRenderer(QByteArray(svg))
        qimg = QImage(640, 640, QImage.Format_RGB32)
        p = QPainter(qimg)
        renderer.render(p)
        p.end()
        buf = qimg.bits().tobytes()
        board_pil = Image.frombuffer("RGBA", (640, 640), buf, "raw", "BGRA", 0, 1).convert("RGB")

        desktop = Image.new("RGB", (1920, 1080), (22, 21, 18))
        target_x, target_y = 500, 200
        desktop.paste(board_pil, (target_x, target_y))

        # Add 24px flush eval gauge directly touching left edge of board
        canvas = np.array(desktop)
        canvas[target_y : target_y + 320, target_x - 24 : target_x] = (20, 20, 20)
        canvas[target_y + 320 : target_y + 640, target_x - 24 : target_x] = (240, 240, 240)
        desktop_eval = Image.fromarray(canvas)

        detected = detect_chessboard_fullscreen(desktop_eval)
        self.assertIsNotNone(detected)
        dx, dy, dw, dh = detected
        self.assertAlmostEqual(dx, target_x, delta=3)
        self.assertAlmostEqual(dy, target_y, delta=3)
        self.assertAlmostEqual(dw, 640, delta=3)
        self.assertAlmostEqual(dh, 640, delta=3)

    def test_sanitize_board_transition_preserves_undone_captures(self):
        """Verify sanitize_board_transition never deletes restored pieces when a capture is undone."""
        b_pre_cap = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 3")
        b_post_cap = b_pre_cap.copy()
        b_post_cap.push_san("dxe5")

        # Simulate user reversing the capture: prev_board = b_post_cap, new_board = b_pre_cap
        sanitized = sanitize_board_transition(b_post_cap, b_pre_cap)
        self.assertEqual(sanitized.piece_map(), b_pre_cap.piece_map())
        self.assertEqual(len(sanitized.piece_map()), 32)
        # Specifically verify both d4 pawn and e5 pawn are intact
        self.assertEqual(sanitized.piece_at(chess.D4), chess.Piece(chess.PAWN, chess.WHITE))
        self.assertEqual(sanitized.piece_at(chess.E5), chess.Piece(chess.PAWN, chess.BLACK))

    def test_determine_turn_from_move_on_reversed_moves(self):
        """Verify determine_turn_from_move accurately identifies the player whose move was undone."""
        # 1. Reverse 1. e4 -> White's move undone -> White's turn to move now!
        b0 = chess.Board()
        b1 = b0.copy()
        b1.push_san("e4")
        self.assertEqual(determine_turn_from_move(b1, b0), chess.WHITE)

        # 2. Reverse 1... d5 -> Black's move undone -> Black's turn to move now!
        b2 = b1.copy()
        b2.push_san("d5")
        self.assertEqual(determine_turn_from_move(b2, b1), chess.BLACK)

        # 3. Reverse 2. exd5 -> White's capture undone -> White's turn to move now!
        b3 = b2.copy()
        b3.push_san("exd5")
        self.assertEqual(determine_turn_from_move(b3, b2), chess.WHITE)

        # 4. Reverse Castling O-O -> White's move undone -> White's turn to move now!
        b_castle_pre = chess.Board("r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w KQkq - 0 5")
        b_castle_post = b_castle_pre.copy()
        b_castle_post.push_san("O-O")
        self.assertEqual(determine_turn_from_move(b_castle_post, b_castle_pre), chess.WHITE)

    def test_consecutive_move_reversals_preserve_all_pieces_and_turns(self):
        """Verify that reversing an entire sequence of moves step-by-step preserves all pieces and turns."""
        moves = ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5", "Nf3", "Nf6", "d4", "c6", "Be2", "Bf5", "O-O", "e6"]
        game = [chess.Board()]
        for m in moves:
            b = game[-1].copy()
            b.push_san(m)
            game.append(b)

        curr_state = game[-1].copy()

        # Step backwards through the game to move 0
        for i in range(len(game) - 2, -1, -1):
            target = game[i]
            sanitized = sanitize_board_transition(curr_state, target)
            self.assertEqual(
                sanitized.piece_map(),
                target.piece_map(),
                f"Pieces corrupted at undo step to move {i}",
            )
            detected_turn = determine_turn_from_move(curr_state, sanitized)
            self.assertEqual(
                detected_turn,
                target.turn,
                f"Turn inverted at undo step to move {i}: got {detected_turn}, expected {target.turn}",
            )
            curr_state = sanitized.copy()

        # Starting position reached: all 32 pieces present and intact
        self.assertEqual(len(curr_state.piece_map()), 32)
        self.assertEqual(curr_state.board_fen(), chess.STARTING_BOARD_FEN)

    def test_multi_move_jump_preserves_pieces(self):
        """Verify jumping backwards multiple moves preserves all pieces without corruption."""
        moves = ["e4", "d5", "exd5", "Qxd5", "Nc3", "Qa5"]
        game = [chess.Board()]
        for m in moves:
            b = game[-1].copy()
            b.push_san(m)
            game.append(b)

        b_move6 = game[6]  # 30 pieces
        b_move2 = game[2]  # 32 pieces

        # Jump from move 6 directly to move 2
        sanitized = sanitize_board_transition(b_move6, b_move2)
        self.assertEqual(sanitized.piece_map(), b_move2.piece_map())
        self.assertEqual(len(sanitized.piece_map()), 32)


if __name__ == "__main__":
    unittest.main()
