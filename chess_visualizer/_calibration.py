"""
_calibration.py
===============
Interactive drag-to-select calibration overlay with auto-grid snapping.

Features:
- Auto-Grid Recognition: Just drag a rough box over the board; the app
  automatically detects the exact 8x8 chessboard boundary and snaps to it.
- WDA_EXCLUDEFROMCAPTURE: Invisible to screen capture for pristine screenshots.
- Live 8x8 Grid Preview: Shows the exact square divisions locked to the board.
- Keyboard fine-tuning: Arrow keys to nudge (1px / Shift for 5px), +/- to resize.
- Enter/Space to confirm, ESC to cancel.
"""

from __future__ import annotations

import ctypes
import logging
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor
from PySide6.QtWidgets import QApplication, QWidget

from chess_visualizer.capture import ScreenCapture
from chess_visualizer.recognition import detect_chessboard_in_crop

logger = logging.getLogger(__name__)

# Windows display affinity: window excluded from desktop screenshots
WDA_EXCLUDEFROMCAPTURE = 0x00000011


class CalibrationWidget(QWidget):
    """Full-screen calibration overlay with automated chessboard grid snapping."""

    def __init__(self, screen_capture: Optional[ScreenCapture] = None) -> None:
        super().__init__()
        self.selected_region: Optional[Tuple[int, int, int, int]] = None
        self._cap = screen_capture or ScreenCapture()

        self._start: Optional[QPoint] = None
        self._current: Optional[QPoint] = None
        self._rect: Optional[QRect] = None
        self._is_snapped: bool = False
        self._status_text: str = "Drag a rough box over the chessboard — it auto-snaps to the grid"

        # Banner button hit-test rects
        self._btn_confirm_rect = QRect()
        self._btn_cancel_rect = QRect()

        self._setup_window()

    def _setup_window(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        # Exclude this overlay from screen capture so grab_region sees clean desktop
        try:
            hwnd = int(self.winId())
            ctypes.windll.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
        except Exception as exc:
            logger.debug("SetWindowDisplayAffinity failed: %s", exc)

        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    # -------------------------------------------------------------------------
    # Mouse events
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()

            # Check if clicked on Confirm button
            if self._rect and self._btn_confirm_rect.contains(pos):
                self._confirm()
                return

            # Check if clicked on Cancel button
            if self._btn_cancel_rect.contains(pos):
                self._cancel()
                return

            self._start = pos
            self._current = pos
            self._rect = None
            self._is_snapped = False
            self._status_text = "Selecting rough area..."
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._start is not None:
            self._current = event.pos()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._start is not None:
            self._current = event.pos()
            rough = QRect(self._start, self._current).normalized()
            self._start = None
            self._current = None

            if rough.width() >= 30 and rough.height() >= 30:
                self._snap_to_chessboard(rough)
            else:
                self._status_text = "Drag a rough box over the chessboard — it auto-snaps to the grid"

            self.update()

    # -------------------------------------------------------------------------
    # Auto-Snapping Algorithm
    # -------------------------------------------------------------------------

    def _snap_to_chessboard(self, rough_rect: QRect) -> None:
        """Capture rough region with padding and auto-snap to the exact 8x8 chessboard grid."""
        screen = QApplication.primaryScreen()
        if not screen:
            self._rect = self._force_square(rough_rect)
            return

        geo = screen.geometry()
        dpr = float(screen.devicePixelRatio())

        rx = rough_rect.left()
        ry = rough_rect.top()
        rw = rough_rect.width()
        rh = rough_rect.height()

        # Add ~18% padding around rough selection so full board is enclosed
        pad = max(24, int(max(rw, rh) * 0.18))
        exp_l = max(geo.x(), rx - pad)
        exp_t = max(geo.y(), ry - pad)
        exp_r = min(geo.x() + geo.width(), rx + rw + pad)
        exp_b = min(geo.y() + geo.height(), ry + rh + pad)
        exp_w = exp_r - exp_l
        exp_h = exp_b - exp_t

        if exp_w < 50 or exp_h < 50:
            self._rect = self._force_square(rough_rect)
            return

        # Grab clean desktop underneath this window
        crop_pil = self._cap.grab_region(exp_l, exp_t, exp_w, exp_h)
        if crop_pil is None:
            self._rect = self._force_square(rough_rect)
            self._is_snapped = False
            s = self._rect.width()
            self._status_text = f"Manual area ({s}×{s} px) • Press Enter to confirm"
            return

        # Physical rough box inside crop_pil
        rough_phys = (
            int(round((rx - exp_l) * dpr)),
            int(round((ry - exp_t) * dpr)),
            int(round(rw * dpr)),
            int(round(rh * dpr)),
        )

        detected_phys = detect_chessboard_in_crop(crop_pil, rough_phys)
        if detected_phys:
            pbx, pby, pbw, pbh = detected_phys
            # Convert physical crop pixels back to Qt logical screen coordinates
            log_x = exp_l + int(round(pbx / dpr))
            log_y = exp_t + int(round(pby / dpr))
            log_w = int(round(pbw / dpr))
            log_h = int(round(pbh / dpr))
            log_s = (log_w + log_h) // 2

            self._rect = QRect(log_x, log_y, log_s, log_s)
            self._is_snapped = True
            sq = log_s // 8
            self._status_text = f"✓ Snapped to 8×8 grid ({log_s}×{log_s} px, square {sq}px) • Press Enter to confirm"
            logger.info("Auto-snapped chessboard: %s", (log_x, log_y, log_s, log_s))
        else:
            self._rect = self._force_square(rough_rect)
            self._is_snapped = False
            s = self._rect.width()
            self._status_text = f"Manual area ({s}×{s} px) — no grid detected. Use arrows to nudge."

    @staticmethod
    def _force_square(rect: QRect) -> QRect:
        s = min(rect.width(), rect.height())
        if s < 40:
            s = max(rect.width(), rect.height())
        return QRect(rect.left(), rect.top(), s, s)

    # -------------------------------------------------------------------------
    # Keyboard & Confirmation
    # -------------------------------------------------------------------------

    def _confirm(self) -> None:
        if self._rect and self._rect.width() >= 40:
            self.selected_region = (
                self._rect.left(),
                self._rect.top(),
                self._rect.width(),
                self._rect.height(),
            )
        self.close()

    def _cancel(self) -> None:
        self.selected_region = None
        self.close()

    def keyPressEvent(self, event) -> None:
        key = event.key()
        step = 5 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._confirm()
            return

        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self._cancel()
            return

        # Nudge position with arrow keys
        if self._rect:
            x, y, w, h = self._rect.left(), self._rect.top(), self._rect.width(), self._rect.height()
            if key == Qt.Key.Key_Left:
                self._rect = QRect(x - step, y, w, h)
            elif key == Qt.Key.Key_Right:
                self._rect = QRect(x + step, y, w, h)
            elif key == Qt.Key.Key_Up:
                self._rect = QRect(x, y - step, w, h)
            elif key == Qt.Key.Key_Down:
                self._rect = QRect(x, y + step, w, h)
            elif key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                self._rect = QRect(x, y, w + step, h + step)
            elif key in (Qt.Key.Key_Minus, Qt.Key.Key_Underscore):
                if w > 40:
                    self._rect = QRect(x, y, w - step, h - step)
            self._status_text = f"Adjusted: ({self._rect.width()}×{self._rect.height()} px) • Press Enter to confirm"
            self.update()

    # -------------------------------------------------------------------------
    # Paint Event
    # -------------------------------------------------------------------------

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Subtle dark translucent veil over the desktop
        p.fillRect(self.rect(), QColor(0, 0, 0, 115))

        # 2. Sleek floating pill toolbar at the top center
        pill_w = 660
        pill_h = 42
        pill_x = (self.width() - pill_w) // 2
        pill_y = 18
        pill_rect = QRect(pill_x, pill_y, pill_w, pill_h)

        # Background
        p.setPen(QPen(QColor(255, 255, 255, 30), 1))
        p.setBrush(QColor(18, 20, 24, 245))
        p.drawRoundedRect(pill_rect, 10, 10)

        # Icon
        p.setPen(QColor(0, 210, 255))
        font_icon = QFont("Segoe UI", 12)
        font_icon.setBold(True)
        p.setFont(font_icon)
        p.drawText(pill_x + 14, pill_y + 27, "♟")

        # Status text
        if self._is_snapped:
            p.setPen(QColor(56, 217, 169))  # Emerald/cyan for successful snap
        else:
            p.setPen(QColor(220, 225, 235))
        font_status = QFont("Segoe UI", 9)
        p.setFont(font_status)
        p.drawText(pill_x + 38, pill_y + 26, self._status_text)

        # Right buttons inside pill
        btn_w = 80
        btn_h = 28
        btn_confirm_x = pill_x + pill_w - (btn_w * 2 + 18)
        btn_cancel_x = pill_x + pill_w - (btn_w + 10)
        btn_y = pill_y + 7

        self._btn_confirm_rect = QRect(btn_confirm_x, btn_y, btn_w, btn_h)
        self._btn_cancel_rect = QRect(btn_cancel_x, btn_y, btn_w, btn_h)

        # Confirm button
        has_selection = self._rect is not None and self._rect.width() >= 40
        btn_confirm_bg = QColor(31, 111, 235) if has_selection else QColor(40, 44, 52)
        btn_confirm_fg = QColor(255, 255, 255) if has_selection else QColor(120, 125, 135)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(btn_confirm_bg)
        p.drawRoundedRect(self._btn_confirm_rect, 6, 6)
        p.setPen(btn_confirm_fg)
        font_btn = QFont("Segoe UI", 9)
        font_btn.setBold(True)
        p.setFont(font_btn)
        p.drawText(self._btn_confirm_rect, Qt.AlignmentFlag.AlignCenter, "Confirm ↵")

        # Cancel button
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(33, 38, 45))
        p.drawRoundedRect(self._btn_cancel_rect, 6, 6)
        p.setPen(QColor(200, 205, 215))
        font_btn.setBold(False)
        p.setFont(font_btn)
        p.drawText(self._btn_cancel_rect, Qt.AlignmentFlag.AlignCenter, "Cancel")

        # 3. Active rough dragging preview
        if self._start and self._current:
            drag_rect = QRect(self._start, self._current).normalized()
            if drag_rect.width() >= 5 and drag_rect.height() >= 5:
                # Translucent fill
                p.fillRect(drag_rect, QColor(0, 210, 255, 25))
                # Dashed border
                p.setPen(QPen(QColor(0, 210, 255, 180), 1.5, Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(drag_rect)
                # Size tag
                p.setPen(QColor(0, 210, 255))
                p.setFont(QFont("Consolas", 9))
                p.drawText(drag_rect.left(), max(pill_y + pill_h + 16, drag_rect.top() - 6),
                           f"Rough area: {drag_rect.width()}×{drag_rect.height()} px (Release to snap)")

        # 4. Final Snapped / Selected Board Box
        elif self._rect and self._rect.width() >= 10:
            rx, ry, rw, rh = (
                self._rect.left(),
                self._rect.top(),
                self._rect.width(),
                self._rect.height(),
            )

            # Clear translucent veil inside the board area so it's 100% crystal clear
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            p.fillRect(self._rect, Qt.GlobalColor.transparent)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)

            # Outer crisp cyan boundary
            accent_color = QColor(0, 210, 255) if self._is_snapped else QColor(88, 166, 255)
            p.setPen(QPen(accent_color, 2))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(self._rect)

            # High-tech corner viewfinder brackets
            bracket_len = min(16, rw // 8)
            p.setPen(QPen(accent_color, 3))
            # Top-left
            p.drawLine(rx, ry, rx + bracket_len, ry)
            p.drawLine(rx, ry, rx, ry + bracket_len)
            # Top-right
            p.drawLine(rx + rw, ry, rx + rw - bracket_len, ry)
            p.drawLine(rx + rw, ry, rx + rw, ry + bracket_len)
            # Bottom-left
            p.drawLine(rx, ry + rh, rx + bracket_len, ry + rh)
            p.drawLine(rx, ry + rh, rx, ry + rh - bracket_len)
            # Bottom-right
            p.drawLine(rx + rw, ry + rh, rx + rw - bracket_len, ry + rh)
            p.drawLine(rx + rw, ry + rh, rx + rw, ry + rh - bracket_len)

            # 8x8 internal grid lines
            pen_grid = QPen(QColor(0, 210, 255, 100), 1, Qt.PenStyle.DashLine)
            p.setPen(pen_grid)
            sq_w = rw / 8.0
            sq_h = rh / 8.0
            for i in range(1, 8):
                gx = rx + int(round(i * sq_w))
                p.drawLine(gx, ry, gx, ry + rh)
                gy = ry + int(round(i * sq_h))
                p.drawLine(rx, gy, rx + rw, gy)

            # Floating tag pill above the board
            tag_text = (
                f"✓ 8×8 Grid Snapped: {rw}×{rh} px (Square: {rw // 8} px)"
                if self._is_snapped
                else f"Grid Box: {rw}×{rh} px"
            )
            tag_w = len(tag_text) * 7 + 24
            tag_h = 22
            tag_x = rx
            tag_y = max(pill_y + pill_h + 8, ry - tag_h - 6)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(18, 20, 24, 230))
            p.drawRoundedRect(QRect(tag_x, tag_y, tag_w, tag_h), 4, 4)

            p.setPen(accent_color)
            p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            p.drawText(QRect(tag_x, tag_y, tag_w, tag_h), Qt.AlignmentFlag.AlignCenter, tag_text)

        p.end()
