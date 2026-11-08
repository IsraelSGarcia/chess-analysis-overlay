"""
test_monorepo_architecture.py
==============================
Validates that the monorepo package layout (umbrella: chess-analysis-overlay)
with core, projects, and overlay subpackages imports and functions properly.
"""

import unittest
import chess


class TestMonorepoArchitecture(unittest.TestCase):
    def test_core_imports(self):
        # 1. board_recognition
        from core.board_recognition import (
            ScreenCapture,
            set_window_capture_exclusion,
            detect_chessboard_fullscreen,
            detect_chessboard_in_crop,
            Recognizer,
            CalibrationWidget,
        )
        self.assertIsNotNone(ScreenCapture)
        self.assertTrue(callable(set_window_capture_exclusion))
        self.assertTrue(callable(detect_chessboard_fullscreen))

        # 2. chess_rules
        from core.chess_rules import (
            is_valid_recognized_board,
            determine_turn_from_move,
            sanitize_board_transition,
        )
        b = chess.Board()
        self.assertTrue(is_valid_recognized_board(b))

        # 3. position_representation
        from core.position_representation import (
            square_to_coords,
            coords_to_square,
            square_to_rect,
            get_square_center,
            point_to_square,
        )
        col, row = square_to_coords(chess.E4, flipped=False)
        self.assertEqual(coords_to_square(col, row, flipped=False), chess.E4)
        x, y, w, h = square_to_rect(chess.E4, 800, 800, flipped=False)
        self.assertAlmostEqual(w, 100.0)
        self.assertEqual(point_to_square(x + 50, y + 50, 800, 800, flipped=False), chess.E4)

        # 4. shared_analysis
        from core.shared_analysis import (
            PIECE_VALUES,
            get_piece_value,
            AttackDefenseMap,
            evaluate_exchange,
        )
        self.assertEqual(get_piece_value(chess.QUEEN), 900)
        adm = AttackDefenseMap(b)
        self.assertIn(chess.E4, adm.squares)

    def test_projects_capture_visualizer(self):
        from projects.chess_capture_visualizer import (
            CaptureMove,
            get_legal_captures,
            get_all_captures,
            get_all_captures_dict,
        )
        b = chess.Board()
        caps = get_all_captures_dict(b)
        self.assertIn("white", caps)
        self.assertIn("black", caps)

    def test_projects_tactical_analyzer(self):
        from projects.chess_tactical_analyzer import (
            TacticalMotif,
            MotifType,
            find_forks,
            find_skewers,
            find_back_rank_weaknesses,
            find_mating_threats,
            find_removing_the_defender,
            find_hanging_pieces,
            find_trapped_pieces,
            find_xray_rays,
            find_all_blunders,
            generate_tactical_report,
            identify_opening_from_moves,
            is_opening_phase,
            detect_opening_traps,
            evaluate_runaway_passed_pawns,
            detect_king_opposition,
            classify_passed_pawns,
            is_endgame,
            generate_positional_report,
        )
        b = chess.Board("r1bqkb1r/pppp1ppp/2n5/4p3/2B1n3/5N2/PPPP1PPP/RNBQK2R w KQkq - 0 5")
        report = generate_tactical_report(b, active_turn=chess.WHITE)
        self.assertIsNotNone(report)
        self.assertEqual(report.board.fen(), b.fen())
        self.assertIn(MotifType.MATING_THREAT, [m for m in MotifType])
        self.assertIn(MotifType.REMOVING_DEFENDER, [m for m in MotifType])
        self.assertIsNotNone(report.positional)

    def test_overlay_imports(self):
        from overlay.configuration import THEME, VisualTheme, Settings, OverlayConfig
        self.assertIsNotNone(THEME.WINNING_TRADE)
        cfg = OverlayConfig()
        self.assertEqual(cfg.mode, "tactics")

        from overlay.interface import ControlBar, HUDPanel, AppTrayIcon
        self.assertIsNotNone(ControlBar)
        self.assertIsNotNone(HUDPanel)
        self.assertIsNotNone(AppTrayIcon)

        from overlay.rendering import OverlayWidget
        self.assertIsNotNone(OverlayWidget)


if __name__ == "__main__":
    unittest.main()
