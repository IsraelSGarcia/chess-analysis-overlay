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
LOG_FILE = Path(__file__).parent.parent / "visualizer.log"
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
    """Minimize console window if launched via cmd/terminal."""
    try:
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
    except Exception:
        pass


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
    sig_toggle_player = Signal()
    sig_toggle_enemy = Signal()
    sig_toggle_defense = Signal()
    sig_toggle_flip = Signal()
    sig_toggle_hl = Signal()
    sig_recalibrate = Signal()
    sig_close = Signal()


def main() -> None:
    _minimize_console()
    args = _parse_args()

    if args.log:
        logging.getLogger().setLevel(getattr(logging, args.log.upper(), logging.INFO))

    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    from chess_visualizer.settings import Settings
    from chess_visualizer.overlay import OverlayConfig
    from chess_visualizer._overlay_widget import OverlayWidget
    from chess_visualizer._control_bar import ControlBar
    from chess_visualizer.chess_logic import get_all_captures_dict
    from chess_visualizer.capture import ScreenCapture
    from chess_visualizer.recognition import Recognizer

    settings = Settings.load()

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
    # Setup Overlay and ControlBar
    # -------------------------------------------------------------------------
    def make_config() -> OverlayConfig:
        region = settings.board_region or (100, 100, 640, 640)
        return OverlayConfig(
            board_region=region,
            opacity=settings.opacity,
            flipped=settings.flipped,
            overlay_visible=settings.overlay_visible,
            show_white=settings.show_white,
            show_black=settings.show_black,
            show_highlights=settings.show_highlights,
            show_defense=settings.show_defense,
        )

    overlay = OverlayWidget(make_config())
    control_bar: Optional[ControlBar] = None

    def refresh_ui_states():
        if control_bar:
            control_bar.update_states(
                overlay_visible=settings.overlay_visible,
                show_player=settings.show_white,
                show_enemy=settings.show_black,
                show_defense=settings.show_defense,
                show_highlights=settings.show_highlights,
                flipped=settings.flipped,
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

    def toggle_flip():
        settings.flipped = not settings.flipped
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()
        trigger_immediate_update()

    def toggle_highlights():
        settings.show_highlights = not settings.show_highlights
        settings.save()
        overlay.set_config(make_config())
        refresh_ui_states()

    def run_recalibrate():
        from chess_visualizer._calibration import CalibrationWidget
        overlay.hide()
        if control_bar:
            control_bar.hide()

        cal = CalibrationWidget()
        cal.show()
        while cal.isVisible():
            app.processEvents()
            time.sleep(0.02)

        if cal.selected_region:
            settings.board_region = cal.selected_region
            settings.save()
            overlay.set_config(make_config())
            if control_bar:
                l, t, w, _ = settings.board_region
                control_bar.position_above_board(l, t, w)
            logger.info("New board region calibrated: %s", cal.selected_region)

        overlay.show()
        if control_bar:
            control_bar.show()

    def close_app():
        if control_bar:
            settings.control_bar_pos = (control_bar.x(), control_bar.y())
            settings.save()
            control_bar.close()
        overlay.close()
        app.quit()

    # -------------------------------------------------------------------------
    # Create Compact ControlBar
    # -------------------------------------------------------------------------
    control_bar = ControlBar(
        on_toggle_master=toggle_master,
        on_toggle_white=toggle_player,
        on_toggle_black=toggle_enemy,
        on_toggle_defense=toggle_defense,
        on_flip=toggle_flip,
        on_toggle_highlights=toggle_highlights,
        on_recalibrate=run_recalibrate,
        on_close=close_app,
    )
    refresh_ui_states()

    # Position ControlBar: restore saved position or place above board
    if settings.control_bar_pos:
        control_bar.move(*settings.control_bar_pos)
    elif settings.board_region:
        l, t, w, _ = settings.board_region
        control_bar.position_above_board(l, t, w)

    # -------------------------------------------------------------------------
    # Initial Calibration if needed
    # -------------------------------------------------------------------------
    if args.calibrate or settings.board_region is None:
        run_recalibrate()

    overlay.show()
    control_bar.show()

    # -------------------------------------------------------------------------
    # Thread-Safe Global Hotkeys via Signal Bridge
    # Conflict-free shortcuts: Ctrl+Alt+[Key]
    # -------------------------------------------------------------------------
    bridge = HotkeyBridge()
    bridge.sig_toggle_master.connect(toggle_master)
    bridge.sig_toggle_player.connect(toggle_player)
    bridge.sig_toggle_enemy.connect(toggle_enemy)
    bridge.sig_toggle_defense.connect(toggle_defense)
    bridge.sig_toggle_flip.connect(toggle_flip)
    bridge.sig_toggle_hl.connect(toggle_highlights)
    bridge.sig_recalibrate.connect(run_recalibrate)
    bridge.sig_close.connect(close_app)

    try:
        import keyboard
        # Conflict-free shortcuts using Ctrl+Alt modifiers
        keyboard.add_hotkey("ctrl+alt+x", bridge.sig_toggle_master.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+a", bridge.sig_toggle_player.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+s", bridge.sig_toggle_enemy.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+d", bridge.sig_toggle_defense.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+f", bridge.sig_toggle_flip.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+h", bridge.sig_toggle_hl.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+c", bridge.sig_recalibrate.emit, suppress=False)
        keyboard.add_hotkey("ctrl+alt+q", bridge.sig_close.emit, suppress=False)
    except Exception as exc:
        logger.debug("Global keyboard hook failed: %s", exc)

    # -------------------------------------------------------------------------
    # Static FEN mode
    # -------------------------------------------------------------------------
    if args.fen:
        caps = get_all_captures_dict(args.fen, include_empty=True, include_defense=settings.show_defense)
        overlay.set_captures(caps["white"], caps["black"], board_flipped=args.flip)
        sys.exit(app.exec())

    # -------------------------------------------------------------------------
    # Live Recognition Loop
    # -------------------------------------------------------------------------
    cap = ScreenCapture()
    recognizer = Recognizer()
    last_fen: Optional[str] = None

    def update_loop():
        nonlocal last_fen

        region = settings.board_region
        if not region:
            return

        left, top, w, h = region
        frame = cap.grab_region(left, top, w, h)
        if frame is None:
            return

        # Direct board recognition on the cropped board image
        # Let recognizer auto-infer physical orientation so FEN and squares are always physically aligned
        result = recognizer.recognize_board(frame, flipped=None)

        if not result.success or not result.fen:
            return

        fen = result.fen

        # Ignore empty boards (e.g. during screen minimize or page transitions)
        try:
            test_b = chess.Board(fen)
            if len(test_b.piece_map()) < 2:
                return
        except Exception:
            return

        if fen == last_fen:
            return

        last_fen = fen
        conf_pct = int(result.confidence * 100)
        logger.info("Position recognized: %s (confidence: %d%%)", fen, conf_pct)

        # Calculate captures and defense for all pieces
        try:
            captures = get_all_captures_dict(fen, include_empty=True, include_defense=True)
            overlay.set_captures(captures["white"], captures["black"], board_flipped=result.flipped)
            w_count, b_count = len(captures["white"]), len(captures["black"])
            logger.info("Drawn %d White arrows, %d Black arrows (defense=%s)",
                        w_count, b_count, settings.show_defense)
        except Exception as exc:
            logger.error("Capture calculation error: %s", exc)

    def trigger_immediate_update():
        nonlocal last_fen
        last_fen = None
        update_loop()

    interval_ms = max(250, int(settings.update_interval * 1000))
    timer = QTimer()
    timer.timeout.connect(update_loop)
    timer.start(interval_ms)

    exit_code = app.exec()
    try:
        import keyboard
        keyboard.unhook_all()
    except Exception:
        pass
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
