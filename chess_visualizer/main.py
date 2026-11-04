"""
main.py
=======
Chess Capture Visualizer — Main Orchestration Loop.

Starts the live overlay, floating control bar, screen capture,
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


def main() -> None:
    _minimize_console()
    args = _parse_args()

    if args.log:
        logging.getLogger().setLevel(getattr(logging, args.log.upper(), logging.INFO))

    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer

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
            show_white=settings.show_white,
            show_black=settings.show_black,
            show_highlights=settings.show_highlights,
        )

    overlay = OverlayWidget(make_config())
    control_bar: Optional[ControlBar] = None

    def update_control_bar_position():
        if control_bar and settings.board_region:
            l, t, w, _ = settings.board_region
            control_bar.position_above_board(l, t, w)

    # -------------------------------------------------------------------------
    # Actions
    # -------------------------------------------------------------------------
    def toggle_player():
        settings.show_white = not settings.show_white
        settings.save()
        overlay.set_config(make_config())
        if control_bar:
            control_bar.update_states(settings.show_white, settings.show_black, settings.flipped)

    def toggle_enemy():
        settings.show_black = not settings.show_black
        settings.save()
        overlay.set_config(make_config())
        if control_bar:
            control_bar.update_states(settings.show_white, settings.show_black, settings.flipped)

    def toggle_flip():
        nonlocal last_fen
        settings.flipped = not settings.flipped
        settings.save()
        overlay.set_config(make_config())
        if control_bar:
            control_bar.update_states(settings.show_white, settings.show_black, settings.flipped)
        # Invalidate last_fen so update_loop recognizes the new perspective immediately
        last_fen = None
        # Run update_loop immediately so transition is instant with zero flicker
        update_loop()

    def toggle_highlights():
        settings.show_highlights = not settings.show_highlights
        settings.save()
        overlay.set_config(make_config())

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
            update_control_bar_position()
            logger.info("New board region calibrated: %s", cal.selected_region)

        overlay.show()
        if control_bar:
            control_bar.show()

    def close_app():
        if control_bar:
            control_bar.close()
        overlay.close()
        app.quit()

    # -------------------------------------------------------------------------
    # Create ControlBar
    # -------------------------------------------------------------------------
    control_bar = ControlBar(
        on_toggle_white=toggle_player,
        on_toggle_black=toggle_enemy,
        on_recalibrate=run_recalibrate,
        on_flip=toggle_flip,
        on_close=close_app,
    )
    control_bar.update_states(settings.show_white, settings.show_black, settings.flipped)

    # -------------------------------------------------------------------------
    # Initial Calibration if needed
    # -------------------------------------------------------------------------
    if args.calibrate or settings.board_region is None:
        run_recalibrate()

    overlay.show()
    control_bar.show()
    update_control_bar_position()

    # -------------------------------------------------------------------------
    # Global Hotkeys using 'keyboard' library
    # -------------------------------------------------------------------------
    try:
        import keyboard
        keyboard.add_hotkey("f2", run_recalibrate, suppress=False)
        keyboard.add_hotkey("f3", toggle_player, suppress=False)
        keyboard.add_hotkey("f4", toggle_enemy, suppress=False)
        keyboard.add_hotkey("f6", toggle_flip, suppress=False)
        keyboard.add_hotkey("f7", toggle_highlights, suppress=False)
        keyboard.add_hotkey("f9", close_app, suppress=False)
        keyboard.add_hotkey("ctrl+shift+w", toggle_player, suppress=False)
        keyboard.add_hotkey("ctrl+shift+b", toggle_enemy, suppress=False)
        keyboard.add_hotkey("ctrl+shift+c", run_recalibrate, suppress=False)
        keyboard.add_hotkey("ctrl+shift+q", close_app, suppress=False)
    except Exception as exc:
        logger.debug("Global keyboard hook failed: %s", exc)

    # -------------------------------------------------------------------------
    # Static FEN mode
    # -------------------------------------------------------------------------
    if args.fen:
        caps = get_all_captures_dict(args.fen, include_empty=True)
        overlay.set_captures(caps["white"], caps["black"])
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
        result = recognizer.recognize_board(frame, flipped=settings.flipped)

        if not result.success or not result.fen:
            logger.debug("Recognition failed: %s", result.error)
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
        logger.info("Position recognized: %s (confidence: %.1f%%)", fen, result.confidence * 100)

        # Calculate captures for all pieces, including empty squares
        try:
            captures = get_all_captures_dict(fen, include_empty=True)
            overlay.set_captures(captures["white"], captures["black"])
            logger.info("Drawn %d White capture arrows, %d Black capture arrows (flipped=%s)",
                        len(captures["white"]), len(captures["black"]), settings.flipped)
        except Exception as exc:
            logger.error("Capture calculation error: %s", exc)

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
