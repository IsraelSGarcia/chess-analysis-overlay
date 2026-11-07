"""
_calibration.py
===============
Interactive drag-to-select calibration overlay with auto-grid snapping.

Features:
- Auto-Grid Recognition: Drag a rough area over the board; the app
  automatically detects the exact 8x8 chessboard boundary and snaps to it.
- Minimalist, monochrome UI with zero emojis.
- WDA_EXCLUDEFROMCAPTURE: Invisible to screen capture for pristine screenshots.
- Live 8x8 Grid Preview: Shows exact square divisions locked to the board.
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

from chess_visualizer.capture import ScreenCapture, set_window_capture_exclusion
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
        self._status_text: str = "Drag a rough box over the board to auto-snap"

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
        set_window_capture_exclusion(self)

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
            self._status_text = "Selecting area..."
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
                self._status_text = "Drag a rough box over the board to auto-snap"

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
        exp_l = max(geo.x(), geo.x() + rx - pad)
        exp_t = max(geo.y(), geo.y() + ry - pad)
        exp_r = min(geo.x() + geo.width(), geo.x() + rx + rw + pad)
        exp_b = min(geo.y() + geo.height(), geo.y() + ry + rh + pad)
        exp_w = exp_r - exp_l
        exp_h = exp_b - exp_t

        if exp_w < 50 or exp_h < 50:
            self._rect = self._force_square(rough_rect)
            return

        crop_pil = self._cap.grab_region(exp_l, exp_t, exp_w, exp_h)
        if crop_pil is None:
            self._rect = self._force_square(rough_rect)
            self._is_snapped = False
            s = self._rect.width()
            self._status_text = f"Manual area: {s}×{s}"
            return

        rough_phys = (
            int(round((geo.x() + rx - exp_l) * dpr)),
            int(round((geo.y() + ry - exp_t) * dpr)),
            int(round(rw * dpr)),
            int(round(rh * dpr)),
        )

        detected_phys = detect_chessboard_in_crop(crop_pil, rough_phys)
        if detected_phys:
            pbx, pby, pbw, pbh = detected_phys
            # Convert physical crop pixels back to Qt screen logical coordinates
            log_x = exp_l + int(round(pbx / dpr)) - geo.x()
            log_y = exp_t + int(round(pby / dpr)) - geo.y()
            log_w = int(round(pbw / dpr))
            log_h = int(round(pbh / dpr))
            log_s = (log_w + log_h) // 2

            self._rect = QRect(log_x, log_y, log_s, log_s)
            self._is_snapped = True
            sq = log_s // 8
            self._status_text = f"Snapped: {log_s}×{log_s} (Square: {sq}px)"
            logger.info("Auto-snapped chessboard: %s", (log_x, log_y, log_s, log_s))
        else:
            self._rect = self._force_square(rough_rect)
            self._is_snapped = False
            s = self._rect.width()
            self._status_text = f"Manual area: {s}×{s}"

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
            screen = QApplication.primaryScreen()
            gx = screen.geometry().x() if screen else 0
            gy = screen.geometry().y() if screen else 0
            self.selected_region = (
                gx + self._rect.left(),
                gy + self._rect.top(),
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
            self._status_text = f"Adjusted: {self._rect.width()}×{self._rect.height()}"
            self.update()

    # -------------------------------------------------------------------------
    # Paint Event
    # -------------------------------------------------------------------------

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # 1. Subtle dark translucent veil over desktop
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))

        # 2. Minimalist floating pill toolbar at the top center (monochrome)
        pill_w = 540
        pill_h = 38
        pill_x = (self.width() - pill_w) // 2
        pill_y = 16
        pill_rect = QRect(pill_x, pill_y, pill_w, pill_h)

        p.setPen(QPen(QColor(255, 255, 255, 22), 1))
        p.setBrush(QColor(20, 22, 26, 245))
        p.drawRoundedRect(pill_rect, 6, 6)

        # Grip dots
        p.setPen(QColor(75, 82, 96))
        font_grip = QFont("Consolas", 10, QFont.Weight.Bold)
        p.setFont(font_grip)
        p.drawText(pill_x + 12, pill_y + 23, "::")

        # Status text
        p.setPen(QColor(220, 225, 235))
        font_status = QFont("Segoe UI", 9)
        p.setFont(font_status)
        p.drawText(pill_x + 36, pill_y + 24, self._status_text)

        # Right buttons inside pill
        btn_w = 70
        btn_h = 26
        btn_confirm_x = pill_x + pill_w - (btn_w * 2 + 14)
        btn_cancel_x = pill_x + pill_w - (btn_w + 8)
        btn_y = pill_y + 6

        self._btn_confirm_rect = QRect(btn_confirm_x, btn_y, btn_w, btn_h)
        self._btn_cancel_rect = QRect(btn_cancel_x, btn_y, btn_w, btn_h)

        # Confirm button (minimal monochrome)
        has_selection = self._rect is not None and self._rect.width() >= 40
        btn_confirm_bg = QColor(255, 255, 255, 28) if has_selection else QColor(255, 255, 255, 10)
        btn_confirm_fg = QColor(255, 255, 255) if has_selection else QColor(110, 116, 128)
        p.setPen(QPen(QColor(255, 255, 255, 45) if has_selection else QColor(255, 255, 255, 15), 1))
        p.setBrush(btn_confirm_bg)
        p.drawRoundedRect(self._btn_confirm_rect, 4, 4)
        p.setPen(btn_confirm_fg)
        font_btn = QFont("Segoe UI", 9, QFont.Weight.DemiBold if has_selection else QFont.Weight.Normal)
        p.setFont(font_btn)
        p.drawText(self._btn_confirm_rect, Qt.AlignmentFlag.AlignCenter, "Confirm")

        # Cancel button (minimal monochrome)
        p.setPen(QPen(QColor(255, 255, 255, 15), 1))
        p.setBrush(QColor(255, 255, 255, 10))
        p.drawRoundedRect(self._btn_cancel_rect, 4, 4)
        p.setPen(QColor(180, 185, 195))
        p.setFont(font_btn)
        p.drawText(self._btn_cancel_rect, Qt.AlignmentFlag.AlignCenter, "Cancel")

        # 3. Active rough dragging preview
        if self._start and self._current:
            drag_rect = QRect(self._start, self._current).normalized()
            if drag_rect.width() >= 5 and drag_rect.height() >= 5:
                p.fillRect(drag_rect, QColor(255, 255, 255, 18))
                p.setPen(QPen(QColor(255, 255, 255, 160), 1, Qt.PenStyle.DashLine))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawRect(drag_rect)

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

            # Crisp minimalist boundary
            border_color = QColor(240, 245, 255) if self._is_snapped else QColor(180, 190, 205)
            p.setPen(QPen(border_color, 1.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(self._rect)

            # 8x8 internal grid lines using exact floating-point divisions
            pen_grid = QPen(QColor(255, 255, 255, 75), 1, Qt.PenStyle.DashLine)
            p.setPen(pen_grid)
            sq_w = rw / 8.0
            sq_h = rh / 8.0
            for i in range(1, 8):
                gx = rx + int(round(i * sq_w))
                p.drawLine(gx, ry, gx, ry + rh)
                gy = ry + int(round(i * sq_h))
                p.drawLine(rx, gy, rx + rw, gy)

            # Floating tag pill above the board
            tag_text = f"{rw}×{rh}"
            tag_w = len(tag_text) * 7 + 16
            tag_h = 20
            tag_x = rx
            tag_y = max(pill_y + pill_h + 8, ry - tag_h - 4)

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(20, 22, 26, 230))
            p.drawRoundedRect(QRect(tag_x, tag_y, tag_w, tag_h), 4, 4)

            p.setPen(QColor(220, 225, 235))
            p.setFont(QFont("Segoe UI", 8, QFont.Weight.DemiBold))
            p.drawText(QRect(tag_x, tag_y, tag_w, tag_h), Qt.AlignmentFlag.AlignCenter, tag_text)

        p.end()
