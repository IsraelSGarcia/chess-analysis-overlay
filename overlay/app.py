"""
main.py
=======
Chess Capture Visualizer — Main Orchestration Loop.

Starts the live overlay, compact floating toolbar, screen capture,
piece recognition, and capture calculator.
"""

from __future__ import annotations

import argparse
import ctypes
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import chess
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from PySide6.QtWidgets import QApplication

# Configure file logging alongside console
LOG_FILE = Path(__file__).parent / "visualizer.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def _minimize_console() -> None:
    """Minimize console window only if launched via launch.bat."""
    try:
        if os.environ.get("CHESS_LAUNCHED_FROM_BAT") == "1":
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except Exception:
        pass


from core.chess_rules.validator import is_valid_recognized_board
from core.chess_rules.transitions import (
    determine_turn_from_move,
    sanitize_board_transition,
    generate_candidate_moves,
    _generate_candidate_moves,
)

__all__ = [
    "main",
    "is_valid_recognized_board",
    "determine_turn_from_move",
    "sanitize_board_transition",
    "_generate_candidate_moves",
]


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Live Chess Capture Visualizer")
    p.add_argument("--fen", type=str, default=None, help="Static FEN mode")
    p.add_argument("--calibrate", action="store_true", help="Launch calibration on startup")
    p.add_argument("--board-region", type=str, default=None, help="L,T,W,H")
    p.add_argument("--flip", action="store_true", help="Black is at the bottom")
    p.add_argument("--interval", type=float, default=0.5, help="Update interval in seconds")
    p.add_argument("--log", type=str, default="INFO", help="Log level")
    return p.parse_args()


class HotkeyBridge(QObject):
    """Thread-safe bridge dispatching global hotkey events to Qt main thread."""
    sig_toggle_master = Signal()
    sig_toggle_mode = Signal()
    sig_toggle_player = Signal()
    sig_toggle_enemy = Signal()
    sig_toggle_defense = Signal()
    sig_toggle_turn = Signal()
    sig_toggle_positional = Signal()
    sig_toggle_flip = Signal()
    sig_toggle_hl = Signal()
    sig_toggle_hud = Signal()
    sig_toggle_auto = Signal()
    sig_recalibrate = Signal()
    sig_close = Signal()


def main() -> None:
    _minimize_console()
    args = _parse_args()

    if args.log:
        logging.getLogger().setLevel(getattr(logging, args.log.upper(), logging.INFO))

    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from overlay.configuration.settings import Settings
    from overlay.configuration.overlay_config import OverlayConfig
    from overlay.rendering.overlay_widget import OverlayWidget
    from overlay.interface.control_bar import ControlBar
    from overlay.interface.hud_panel import HUDPanel
    from overlay.interface.tray import AppTrayIcon, create_app_icon
    from projects.chess_capture_visualizer.captures import get_all_captures_dict
    from core.board_recognition.capture import ScreenCapture
    from core.board_recognition.recognition import Recognizer, detect_chessboard_fullscreen, detect_chessboard_in_crop
    from projects.chess_tactical_analyzer.report import generate_tactical_report

    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("chess_analysis_overlay.app.v1")
    except Exception:
        pass

    app.setWindowIcon(create_app_icon())

    settings = Settings.load()
    # Ensure overlay is visible by default unless explicitly hidden
    if not hasattr(settings, 'overlay_visible'):
        settings.overlay_visible = True

    if args.board_region:
        try:
            parts = [int(x.strip()) for x in args.board_region.split(",")]
            settings.board_region = tuple(parts)
        except ValueError:
            pass
    if args.flip:
        settings.flipped = True
    if args.interval:
        settings.update_interval = args.interval

    # -------------------------------------------------------------------------
    # Setup Overlay, ControlBar, and Tactical HUD
    # -------------------------------------------------------------------------
    def make_config() -> OverlayConfig:
        region = settings.board_region or (100, 100, 640, 640)
        return OverlayConfig(
            board_region=region,
            opacity=settings.opacity,
            mode=settings.active_mode,
            flipped=settings.flipped,
            overlay_visible=settings.overlay_visible,
            show_white=settings.show_white,
            show_black=settings.show_black,
            show_highlights=settings.show_highlights,
            show_defense=settings.show_defense,
            show_tactical_arrows=settings.show_tactical_arrows,
            show_tactical_highlights=settings.show_highlights,
        )

    overlay = OverlayWidget(make_config())
    control_bar: Optional[ControlBar] = None
    hud_panel: Optional[HUDPanel] = None
    tray_icon: Optional[AppTrayIcon] = None

    # Core state tracking variables (initialized before UI refresh and event callbacks)
    current_active_turn: bool = chess.WHITE
    current_flipped: Optional[bool] = None
    manual_turn_override: bool = False
    last_fen: Optional[str] = None
    last_pieces_fen: Optional[str] = None
    last_board_state: Optional[chess.Board] = None

    def trigger_immediate_update():
        nonlocal last_fen
        last_fen = None
        if "update_loop" in locals() or "update_loop" in globals():
            try:
                update_loop()
            except Exception as e:
                logger.debug("Immediate update deferred: %s", e)

    def refresh_ui_states():
        if control_bar:
            control_bar.update_states(
                overlay_visible=settings.overlay_visible,
                mode=settings.active_mode,
                show_player=settings.show_white,
                show_enemy=settings.show_black,
                show_defense=settings.show_defense,
                show_highlights=settings.show_highlights,
                show_hud=settings.show_hud,
                auto_track=(settings.auto_track and not settings.manual_locked),
                flipped=settings.flipped,
                active_turn=(current_active_turn == chess.WHITE),
            )
        if tray_icon:
            tray_icon.update_states(
                overlay_visible=settings.overlay_visible,
                mode=settings.active_mode,
                hud_visible=settings.show_hud,
                auto_track=(settings.auto_track and not settings.manual_locked),
            )

    # -------------------------------------------------------------------------
    # Actions (Executed safely on Qt main thread)
    # -------------------------------------------------------------------------
    def toggle_master():
        """Master toggle: Show / Hide overlay arrows and highlights."""
        settings.overlay_visible = not settings.overlay_visible
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()

    def toggle_mode():
        """Cycle between Tactics -> Captures -> Positional -> Tactics modes."""
        modes = ["tactics", "captures", "positional"]
        current_idx = modes.index(settings.active_mode) if settings.active_mode in modes else 0
        settings.active_mode = modes[(current_idx + 1) % len(modes)]
        settings.save()
        overlay.set_config(make_config())
        if settings.active_mode in ("tactics", "positional"):
            if hud_panel and settings.show_hud:
                hud_panel.show()
        else:
            if hud_panel:
                hud_panel.hide()
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_positional():
        """Directly toggle Positional Analysis mode (Ctrl+Alt+P)."""
        if settings.active_mode == "positional":
            settings.active_mode = "tactics"
        else:
            settings.active_mode = "positional"
        settings.save()
        overlay.set_config(make_config())
        if settings.active_mode in ("tactics", "positional"):
            if hud_panel and settings.show_hud:
                hud_panel.show()
        else:
            if hud_panel:
                hud_panel.hide()
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_player():
        settings.show_white = not settings.show_white
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()

    def toggle_enemy():
        settings.show_black = not settings.show_black
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()

    def toggle_defense():
        settings.show_defense = not settings.show_defense
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_active_turn():
        """Explicitly toggle active player turn between White and Black."""
        nonlocal current_active_turn, last_fen, last_board_state, manual_turn_override
        manual_turn_override = True
        current_active_turn = not current_active_turn
        logger.info("Active turn explicitly toggled to: %s", "White" if current_active_turn == chess.WHITE else "Black")
        last_fen = None
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_flip():
        nonlocal current_flipped
        settings.flipped = not settings.flipped
        current_flipped = settings.flipped
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_highlights():
        settings.show_highlights = not settings.show_highlights
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()

    def toggle_hud():
        settings.show_hud = not settings.show_hud
        settings.save()
        if hud_panel:
            if settings.show_hud:
                hud_panel.show()
            else:
                hud_panel.hide()
        refresh_ui_states()

    def toggle_auto():
        """Toggle between full-screen auto-tracking and manual locked mode."""
        if settings.manual_locked:
            settings.manual_locked = False
            settings.auto_track = True
            settings.board_region = None
            logger.info("Switched to Full Automatic Board Detection & Tracking")
        else:
            settings.auto_track = not settings.auto_track
            if settings.auto_track:
                settings.board_region = None
            logger.info("Auto-track toggled: %s", settings.auto_track)
        settings.save()
        refresh_ui_states()
        trigger_immediate_update()

    def run_recalibrate():
        """Manual calibration fallback: drag a box over the board."""
        from core.board_recognition.calibration import CalibrationWidget
        overlay.hide()
        if control_bar:
            control_bar.hide()
        if hud_panel:
            hud_panel.hide()

        cal = CalibrationWidget()
        cal.show()
        while cal.isVisible():
            app.processEvents()
            time.sleep(0.02)

        if cal.selected_region:
            settings.board_region = cal.selected_region
            settings.manual_locked = True
            settings.save()
            overlay.set_config(make_config())
            if control_bar:
                l, t, w, _ = settings.board_region
                control_bar.position_above_board(l, t, w)
            if hud_panel and not settings.hud_pos:
                l, t, w, h = settings.board_region
                hud_panel.position_beside_board(l, t, w, h)
            logger.info("Manual board region locked: %s", cal.selected_region)

        refresh_ui_states()
        if settings.overlay_visible:
            overlay.show()
        if control_bar:
            control_bar.show()
        if hud_panel and settings.show_hud:
            hud_panel.show()

    def close_app():
        if tray_icon:
            tray_icon.hide()
        if control_bar:
            settings.control_bar_pos = (control_bar.x(), control_bar.y())
            control_bar.close()
        if hud_panel:
            settings.hud_pos = (hud_panel.x(), hud_panel.y())
            hud_panel.close()
        settings.save()
        overlay.close()
        app.quit()

    # -------------------------------------------------------------------------
    # Create Compact ControlBar, Tactical HUD Panel, and System Tray Icon
    # -------------------------------------------------------------------------
    control_bar = ControlBar(
        on_toggle_master=toggle_master,
        on_toggle_mode=toggle_mode,
        on_toggle_white=toggle_player,
        on_toggle_black=toggle_enemy,
        on_toggle_defense=toggle_defense,
        on_flip=toggle_flip,
        on_toggle_highlights=toggle_highlights,
        on_toggle_hud=toggle_hud,
        on_toggle_auto=toggle_auto,
        on_recalibrate=run_recalibrate,
        on_close=close_app,
        on_toggle_turn=toggle_active_turn,
    )

    hud_panel = HUDPanel(on_close=toggle_hud, on_toggle_turn=toggle_active_turn)

    tray_icon = AppTrayIcon(
        on_toggle_master=toggle_master,
        on_toggle_mode=toggle_mode,
        on_toggle_hud=toggle_hud,
        on_toggle_auto=toggle_auto,
        on_recalibrate=run_recalibrate,
        on_exit=close_app,
    )
    tray_icon.show()
    refresh_ui_states()

    # Position ControlBar: restore saved position or place above board, or center at top
    if settings.control_bar_pos:
        control_bar.move(*settings.control_bar_pos)
    elif settings.board_region:
        l, t, w, _ = settings.board_region
        control_bar.position_above_board(l, t, w)
    else:
        screen = app.primaryScreen()
        if screen:
            geo = screen.geometry()
            cb_w = control_bar.sizeHint().width()
            control_bar.move(geo.x() + (geo.width() - cb_w) // 2, geo.y() + 20)

    # Position HUD Panel: restore saved position or place beside board
    if settings.hud_pos:
        hud_panel.move(*settings.hud_pos)
    elif settings.board_region:
        l, t, w, h = settings.board_region
        hud_panel.position_beside_board(l, t, w, h)

    # -------------------------------------------------------------------------
    # Initial Calibration ONLY if explicitly launched via --calibrate
    # -------------------------------------------------------------------------
    if args.calibrate:
        run_recalibrate()

    # Always show ControlBar immediately so the user has visual confirmation & taskbar access
    control_bar.show()
    control_bar.raise_()
    control_bar.activateWindow()
    if tray_icon:
        tray_icon.notify("Chess Analysis Overlay", "Active and searching for chessboard on screen.")

    # In manual mode with saved region, show overlay and hud right away
    if settings.manual_locked and settings.board_region:
        if settings.overlay_visible:
            overlay.show()
        if settings.show_hud:
            hud_panel.show()
        control_bar.set_status("Manual", mode="manual")
        tray_icon.set_status_text("Manual Region Locked")
    else:
        control_bar.set_status("Searching...", mode="searching")
        tray_icon.set_status_text("Searching for chessboard...")

    # -------------------------------------------------------------------------
    # Thread-Safe Global Hotkeys via Signal Bridge
    # Conflict-free shortcuts: Ctrl+Alt+[Key]
    # -------------------------------------------------------------------------
    bridge = HotkeyBridge()
    bridge.sig_toggle_master.connect(toggle_master)
    bridge.sig_toggle_mode.connect(toggle_mode)
    bridge.sig_toggle_positional.connect(toggle_positional)
    bridge.sig_toggle_player.connect(toggle_player)
    bridge.sig_toggle_enemy.connect(toggle_enemy)
    bridge.sig_toggle_defense.connect(toggle_defense)
    bridge.sig_toggle_turn.connect(toggle_active_turn)
    bridge.sig_toggle_flip.connect(toggle_flip)
    bridge.sig_toggle_hl.connect(toggle_highlights)
    bridge.sig_toggle_hud.connect(toggle_hud)
    bridge.sig_toggle_auto.connect(toggle_auto)
    bridge.sig_recalibrate.connect(run_recalibrate)
    bridge.sig_close.connect(close_app)

    try:
        import keyboard
        # Conflict-free shortcuts using Ctrl+Alt modifiers
        keyboard.add_hotkey("ctrl+alt+x", bridge.sig_toggle_master.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+m", bridge.sig_toggle_mode.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+p", bridge.sig_toggle_positional.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+a", bridge.sig_toggle_player.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+s", bridge.sig_toggle_enemy.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+d", bridge.sig_toggle_defense.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+w", bridge.sig_toggle_turn.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+f", bridge.sig_toggle_flip.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+h", bridge.sig_toggle_hl.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+t", bridge.sig_toggle_hud.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+b", bridge.sig_toggle_auto.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+c", bridge.sig_recalibrate.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+q", bridge.sig_close.emit, suppress=False)
    except Exception as exc:
        logger.debug("Global keyboard hook failed: %s", exc)

    # -------------------------------------------------------------------------
    # Static FEN mode
    # -------------------------------------------------------------------------
    if args.fen:
        test_b = chess.Board(args.fen)
        caps = get_all_captures_dict(args.fen, include_empty=True, include_defense=settings.show_defense)
        overlay.set_captures(caps["white"], caps["black"], board_flipped=args.flip)
        try:
            tac_report = generate_tactical_report(test_b, search_depth=3)
            overlay.set_tactical_report(tac_report)
            if hud_panel:
                hud_panel.update_report(tac_report)
        except Exception as t_exc:
            logger.debug("Tactical analysis error in FEN mode: %s", t_exc)
        overlay.show()
        control_bar.show()
        if settings.show_hud:
            hud_panel.show()
        sys.exit(app.exec())

    # -------------------------------------------------------------------------
    # Live Recognition & Automatic Board Tracking Loop
    # -------------------------------------------------------------------------
    cap = ScreenCapture()
    recognizer = Recognizer()
    miss_count = 0
    screen = app.primaryScreen()
    dpr = float(screen.devicePixelRatio()) if screen else 1.0

    def hide_all_ui():
        overlay.hide()
        if hud_panel:
            hud_panel.hide()
        if control_bar:
            control_bar.set_status("Searching...", mode="searching")
        if tray_icon:
            tray_icon.set_status_text("Searching for chessboard...")

    def show_all_ui():
        if settings.overlay_visible:
            overlay.show()
        if settings.active_mode in ("tactics", "positional") and settings.show_hud and hud_panel:
            hud_panel.set_mode(settings.active_mode)
            hud_panel.show()
        elif settings.active_mode not in ("tactics", "positional") and hud_panel:
            hud_panel.hide()
        if control_bar:
            control_bar.show()
            if settings.manual_locked:
                control_bar.set_status("Manual", mode="manual")
                if tray_icon:
                    tray_icon.set_status_text("Manual Region Locked")
            else:
                control_bar.set_status("Locked", mode="locked")
                if tray_icon:
                    tray_icon.set_status_text("Board Locked")

    def process_recognized_position(
        test_b: chess.Board,
        fen: str,
        flipped: bool,
        confidence: float,
        active_turn: Optional[bool] = None,
        force_redraw: bool = False,
    ):
        nonlocal last_fen, last_pieces_fen, last_board_state, current_active_turn, current_flipped, manual_turn_override

        # Piece placement part of FEN (e.g. "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR")
        pieces_part = fen.split(" ")[0]

        # Check if either king is in check (forced turn by chess rules)
        wk = test_b.king(chess.WHITE)
        bk = test_b.king(chess.BLACK)
        w_in_check = bool(test_b.attackers(chess.BLACK, wk)) if wk is not None else False
        b_in_check = bool(test_b.attackers(chess.WHITE, bk)) if bk is not None else False
        forced_turn = None
        if b_in_check and not w_in_check:
            forced_turn = chess.BLACK
        elif w_in_check and not b_in_check:
            forced_turn = chess.WHITE

        # 1. First recognition or forced redraw (board reset/switch)
        # Initialize turn directly from physical board detector instead of hardcoded default
        if last_board_state is None or force_redraw:
            current_flipped = flipped
            manual_turn_override = False
            if forced_turn is not None:
                current_active_turn = forced_turn
            elif active_turn is not None:
                current_active_turn = active_turn
            elif test_b.turn is not None:
                current_active_turn = test_b.turn
            test_b.turn = current_active_turn
            last_board_state = test_b.copy()
            refresh_ui_states()
        else:
            # Check board continuity and sanitize any impossible phantom piece spawns
            sanitized_b = sanitize_board_transition(last_board_state, test_b)
            if sanitized_b.piece_map() != test_b.piece_map():
                test_b = sanitized_b
                pieces_part = test_b.board_fen()
                fen_parts = fen.split(" ")
                fen_parts[0] = pieces_part
                fen = " ".join(fen_parts)

            # Check for transient piece drag frame (piece lifted from square, not yet dropped)
            prev_map = last_board_state.piece_map()
            new_map = test_b.piece_map()
            if prev_map != new_map:
                prev_w = {sq: p for sq, p in prev_map.items() if p.color == chess.WHITE}
                new_w = {sq: p for sq, p in new_map.items() if p.color == chess.WHITE}
                prev_b = {sq: p for sq, p in prev_map.items() if p.color == chess.BLACK}
                new_b = {sq: p for sq, p in new_map.items() if p.color == chess.BLACK}

                w_vacated = set(prev_w.keys()) - set(new_w.keys())
                b_vacated = set(prev_b.keys()) - set(new_b.keys())
                w_new_squares = set(new_w.keys()) - set(prev_w.keys())
                b_new_squares = set(new_b.keys()) - set(prev_b.keys())

                # Exactly one friendly piece vanished from its square with no arrival destination
                # and no opponent move. This is a transient mouse drag frame on Lichess/Chess.com.
                if (len(w_vacated) == 1 and not w_new_squares and not b_new_squares and not b_vacated) or \
                   (len(b_vacated) == 1 and not b_new_squares and not w_new_squares and not w_vacated):
                    logger.debug("Transient piece drag frame ignored; preserving established board state.")
                    return

            # 2. Subsequent frames on the same board
            if test_b.piece_map() == last_board_state.piece_map():
                # Pieces are on the exact same squares (selection click, idle, or manual turn toggle)
                if forced_turn is not None:
                    if current_active_turn != forced_turn:
                        current_active_turn = forced_turn
                        manual_turn_override = False
                        refresh_ui_states()
                    test_b.turn = current_active_turn
                elif manual_turn_override:
                    # User explicitly chose the turn via button/hotkey; preserve without automated override!
                    test_b.turn = current_active_turn
                else:
                    if active_turn is not None and active_turn != current_active_turn:
                        # Square highlights clearly detected active player selection or move
                        current_active_turn = active_turn
                        refresh_ui_states()
                    test_b.turn = current_active_turn
            else:
                # Pieces physically moved
                manual_turn_override = False
                if forced_turn is not None:
                    current_active_turn = forced_turn
                    test_b.turn = forced_turn
                    last_board_state = test_b.copy()
                    refresh_ui_states()
                elif test_b.board_fen() == chess.STARTING_BOARD_FEN:
                    current_active_turn = chess.WHITE
                    test_b.turn = chess.WHITE
                    last_board_state = test_b.copy()
                    refresh_ui_states()
                else:
                    next_turn = determine_turn_from_move(last_board_state, test_b)
                    if next_turn is not None:
                        current_active_turn = next_turn
                        test_b.turn = next_turn
                        last_board_state = test_b.copy()
                        refresh_ui_states()
                    elif active_turn is not None:
                        current_active_turn = active_turn
                        test_b.turn = current_active_turn
                        last_board_state = test_b.copy()
                        refresh_ui_states()
                    else:
                        test_b.turn = current_active_turn
                        last_board_state = test_b.copy()

        last_pieces_fen = pieces_part
        fen_parts = fen.split(" ")
        fen_parts[1] = "w" if current_active_turn == chess.WHITE else "b"
        fen = " ".join(fen_parts)

        if not force_redraw and fen == last_fen:
            return

        last_fen = fen
        conf_pct = int(confidence * 100)
        logger.info("Position recognized: %s (confidence: %d%%)", fen, conf_pct)

        try:
            captures = get_all_captures_dict(fen, include_empty=True, include_defense=True)
            overlay.set_captures(captures["white"], captures["black"], board_flipped=flipped)
            w_count, b_count = len(captures["white"]), len(captures["black"])
            logger.info("Drawn %d White arrows, %d Black arrows (defense=%s)",
                        w_count, b_count, settings.show_defense)

            try:
                tac_report = generate_tactical_report(test_b, search_depth=3, active_turn=current_active_turn)
                overlay.set_tactical_report(tac_report)
                if hud_panel:
                    hud_panel.update_report(tac_report)
            except Exception as t_exc:
                logger.debug("Tactical analysis error: %s", t_exc)
        except Exception as exc:
            logger.error("Capture calculation error: %s", exc)

    def _grab_clean(grab_func, *args):
        """Execute screen capture cleanly and reliably.

        SCREEN CAPTURE ISOLATION INVARIANT:
        When OS-level DWM capture exclusion (WDA_EXCLUDEFROMCAPTURE) is active,
        captures directly with zero overhead and zero visual flickering because
        Windows excludes the overlay at the compositor level.
        If OS exclusion is unavailable or inactive, momentarily hides the overlay
        during the grab so overlay annotations NEVER contaminate board recognition.
        """
        if getattr(overlay, "is_capture_excluded", False):
            return grab_func(*args)

        was_visible = overlay.isVisible()
        if was_visible:
            overlay.hide()
            app.processEvents()
        try:
            return grab_func(*args)
        finally:
            if was_visible:
                overlay.show()
                app.processEvents()

    def update_loop():
        nonlocal last_fen, miss_count, current_flipped

        # ---------------------------------------------------------------------
        # 1. Manual Locked Mode (user manually calibrated / fixed region)
        # ---------------------------------------------------------------------
        if settings.manual_locked and settings.board_region:
            region = settings.board_region
            left, top, w, h = region
            frame = _grab_clean(cap.grab_region, left, top, w, h)
            if frame is None:
                return

            result = recognizer.recognize_board(frame, flipped=current_flipped, current_turn=current_active_turn)
            if not result.success or not result.fen:
                return

            try:
                test_b = chess.Board(result.fen)
                if not is_valid_recognized_board(test_b) or result.confidence < 0.60:
                    return
            except Exception:
                return

            show_all_ui()
            process_recognized_position(test_b, result.fen, result.flipped, result.confidence)
            return

        # ---------------------------------------------------------------------
        # 2. Fully Automatic Detection & Tracking Mode
        # ---------------------------------------------------------------------
        # Fast path: If we are already locked on a region, directly verify board pieces
        if settings.board_region:
            left, top, w, h = settings.board_region
            frame = _grab_clean(cap.grab_region, left, top, w, h)
            if frame is not None:
                result = recognizer.recognize_board(frame, flipped=current_flipped, current_turn=current_active_turn)
                if result.success and result.fen:
                    try:
                        test_b = chess.Board(result.fen)
                        if is_valid_recognized_board(test_b) and result.confidence >= 0.65:
                            miss_count = 0
                            show_all_ui()
                            process_recognized_position(
                                test_b,
                                result.fen,
                                result.flipped,
                                result.confidence,
                                active_turn=result.active_turn,
                            )
                            return
                    except Exception:
                        pass

        # Slow path / Board moved or absent: Scan full screen
        full_data = _grab_clean(cap.grab_fullscreen)
        if full_data is None:
            miss_count += 1
            if miss_count >= 3:
                if not settings.manual_locked:
                    settings.board_region = None
                overlay.clear()
                hide_all_ui()
                last_fen = None
            return

        screen_pil, geo_x, geo_y = full_data
        detected_phys = detect_chessboard_fullscreen(screen_pil)

        if detected_phys is None:
            miss_count += 1
            if miss_count >= 3:
                if not settings.manual_locked:
                    settings.board_region = None
                overlay.clear()
                hide_all_ui()
                last_fen = None
            return

        pbx, pby, pbw, pbh = detected_phys
        # Convert physical pixels to Qt logical coordinates
        log_x = geo_x + int(round(pbx / dpr))
        log_y = geo_y + int(round(pby / dpr))
        log_w = int(round(pbw / dpr))
        log_h = int(round(pbh / dpr))
        log_s = (log_w + log_h) // 2

        new_region = (log_x, log_y, log_s, log_s)

        # Verify candidate by cropping and classifying pieces
        board_crop = screen_pil.crop((pbx, pby, pbx + pbw, pby + pbh))
        verif = recognizer.recognize_board(board_crop, flipped=None, current_turn=current_active_turn)

        if not verif.success or not verif.fen:
            miss_count += 1
            if miss_count >= 3:
                if not settings.manual_locked:
                    settings.board_region = None
                overlay.clear()
                hide_all_ui()
                last_fen = None
            return

        try:
            test_b = chess.Board(verif.fen)
            if not is_valid_recognized_board(test_b) or verif.confidence < 0.65:
                miss_count += 1
                if miss_count >= 3:
                    if not settings.manual_locked:
                        settings.board_region = None
                    overlay.clear()
                    hide_all_ui()
                    last_fen = None
                return
        except Exception:
            miss_count += 1
            if miss_count >= 3:
                if not settings.manual_locked:
                    settings.board_region = None
                overlay.clear()
                hide_all_ui()
                last_fen = None
            return

        # Real chessboard verified!
        miss_count = 0
        region_changed = False
        if settings.board_region is None:
            region_changed = True
        else:
            rx, ry, rw, rh = settings.board_region
            nx, ny, nw, nh = new_region
            if abs(rx - nx) > 4 or abs(ry - ny) > 4 or abs(rw - nw) > 4:
                region_changed = True

        if region_changed:
            settings.board_region = new_region
            last_fen = None
            last_pieces_fen = None
            last_board_state = None
            current_flipped = None
            manual_turn_override = False
            overlay.set_config(make_config())
            if not settings.control_bar_pos:
                control_bar.position_above_board(log_x, log_y, log_s)
            if not settings.hud_pos:
                hud_panel.position_beside_board(log_x, log_y, log_s, log_s)

        show_all_ui()
        process_recognized_position(
            test_b,
            verif.fen,
            verif.flipped,
            verif.confidence,
            active_turn=verif.active_turn,
            force_redraw=region_changed,
        )

    interval_ms = max(250, int(settings.update_interval * 1000))
    timer = QTimer()
    timer.timeout.connect(update_loop)
    timer.start(interval_ms)

    # Immediately trigger the first detection pass without waiting for timer interval
    QTimer.singleShot(10, update_loop)

    exit_code = app.exec()
    try:
        import keyboard
        keyboard.unhook_all()
    except Exception:
        pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
