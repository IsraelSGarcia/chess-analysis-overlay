"""
_calibration.py
===============
Interactive drag-to-select calibration overlay.

Features:
- Live transparent view: you see your chessboard live underneath.
- 8x8 Grid preview: displays internal 64-square grid lines while dragging,
  allowing perfect alignment with the chessboard squares.
- Fine-tuning: arrow keys to nudge position (1px / Shift+arrow for 5px),
  '+' / '-' keys to expand or shrink size.
- Press Enter or click Confirm to accept, ESC to cancel.
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from PySide6.QtCore import Qt, QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtWidgets import QApplication, QWidget

logger = logging.getLogger(__name__)


class CalibrationWidget(QWidget):
    """Live full-screen calibration overlay with 8x8 grid alignment."""

    def __init__(self) -> None:
        super().__init__()
        self.selected_region: Optional[Tuple[int, int, int, int]] = None
        self._start: Optional[QPoint] = None
        self._current: Optional[QPoint] = None
        self._rect: Optional[QRect] = None
        self._confirmed: bool = False

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
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    # -------------------------------------------------------------------------
    # Mouse events
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._start = event.pos()
            self._current = event.pos()
            self._rect = None
            self.update()

    def mouseMoveEvent(self, event) -> None:
        if self._start is not None:
            self._current = event.pos()
            self._update_rect()
            self.update()

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton and self._start is not None:
            self._current = event.pos()
            self._update_rect()
            self._start = None
            self._current = None
            self.update()

    def _update_rect(self) -> None:
        if self._start and self._current:
            r = QRect(self._start, self._current).normalized()
            # Force square
            size = min(r.width(), r.height())
            if size >= 10:
                self._rect = QRect(r.left(), r.top(), size, size)

    # -------------------------------------------------------------------------
    # Keyboard controls (fine-tuning & confirmation)
    # -------------------------------------------------------------------------

    def keyPressEvent(self, event) -> None:
        key = event.key()
        step = 5 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            if self._rect and self._rect.width() >= 40:
                self.selected_region = (
                    self._rect.left(),
                    self._rect.top(),
                    self._rect.width(),
                    self._rect.height(),
                )
            self.close()
            return

        if key in (Qt.Key.Key_Escape, Qt.Key.Key_Q):
            self.selected_region = None
            self.close()
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
            self.update()

    # -------------------------------------------------------------------------
    # Paint
    # -------------------------------------------------------------------------

    def paintEvent(self, _) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        # Subtle dark translucent veil over the rest of the screen
        p.fillRect(self.rect(), QColor(0, 0, 0, 110))

        # Header instructions banner
        banner_h = 56
        p.fillRect(QRect(0, 0, self.width(), banner_h), QColor(20, 24, 32, 230))
        p.setPen(QColor(0, 210, 255))
        font_title = QFont("Segoe UI", 13)
        font_title.setBold(True)
        p.setFont(font_title)
        p.drawText(24, 26, "CHESSBOARD CALIBRATION")

        p.setPen(QColor(220, 225, 235))
        font_desc = QFont("Segoe UI", 10)
        p.setFont(font_desc)
        p.drawText(
            24, 46,
            "1. Drag a box over your chessboard  |  2. Arrow keys to nudge (Shift=fast), +/- to resize  |  3. ENTER = Confirm, ESC = Cancel"
        )

        # Draw selected box with 8x8 alignment grid
        if self._rect and self._rect.width() >= 10:
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

            # Draw outer cyan box
            pen_box = QPen(QColor(0, 220, 255), 2)
            p.setPen(pen_box)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRect(self._rect)

            # Draw 8x8 internal grid lines
            pen_grid = QPen(QColor(0, 220, 255, 120), 1, Qt.PenStyle.DashLine)
            p.setPen(pen_grid)
            sq_w = rw / 8.0
            sq_h = rh / 8.0
            for i in range(1, 8):
                # Vertical grid line
                gx = rx + int(round(i * sq_w))
                p.drawLine(gx, ry, gx, ry + rh)
                # Horizontal grid line
                gy = ry + int(round(i * sq_h))
                p.drawLine(rx, gy, rx + rw, gy)

            # Dimension tag above box
            p.setPen(QColor(0, 220, 255))
            font_tag = QFont("Consolas", 10)
            font_tag.setBold(True)
            p.setFont(font_tag)
            tag_text = f"{rw} x {rh} px (Square size: {rw // 8} px)  [Press ENTER to Confirm]"
            p.drawText(rx, max(banner_h + 16, ry - 8), tag_text)

        p.end()
