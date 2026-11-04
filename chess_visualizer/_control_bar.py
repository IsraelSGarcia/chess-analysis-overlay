"""
_control_bar.py
===============
Sleek floating control bar placed above the chessboard.

Provides 1-click controls:
- Toggle Blue (Player captures)
- Toggle Red (Enemy captures)
- Recalibrate board region
- Flip perspective (White / Black view)
- Close app
"""

from __future__ import annotations

from typing import Callable
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame,
)


class ControlBar(QWidget):
    """Floating toolbar with clickable controls and status indicators."""

    def __init__(
        self,
        on_toggle_white: Callable[[], None],
        on_toggle_black: Callable[[], None],
        on_recalibrate: Callable[[], None],
        on_flip: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(None)
        self.on_toggle_white = on_toggle_white
        self.on_toggle_black = on_toggle_black
        self.on_recalibrate = on_recalibrate
        self.on_flip = on_flip
        self.on_close = on_close

        self._drag_pos = QPoint()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(6)

        # Container frame with modern dark styling
        self.frame = QFrame()
        self.frame.setStyleSheet("""
            QFrame {
                background-color: rgba(22, 27, 34, 235);
                border: 1px solid rgba(80, 100, 130, 180);
                border-radius: 6px;
            }
        """)
        frame_layout = QHBoxLayout(self.frame)
        frame_layout.setContentsMargins(8, 3, 8, 3)
        frame_layout.setSpacing(8)

        # Title / Drag handle
        title = QLabel("♟ Capture Viz")
        title.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px;")
        frame_layout.addWidget(title)

        # Player (Blue) toggle button
        self.btn_player = QPushButton("🔵 You [F3]")
        self.btn_player.setCheckable(True)
        self.btn_player.setChecked(True)
        self.btn_player.clicked.connect(self.on_toggle_white)
        self._style_button(self.btn_player, active_color="#388bfd", text_color="#ffffff")
        frame_layout.addWidget(self.btn_player)

        # Enemy (Red) toggle button
        self.btn_enemy = QPushButton("🔴 Enemy [F4]")
        self.btn_enemy.setCheckable(True)
        self.btn_enemy.setChecked(True)
        self.btn_enemy.clicked.connect(self.on_toggle_black)
        self._style_button(self.btn_enemy, active_color="#f85149", text_color="#ffffff")
        frame_layout.addWidget(self.btn_enemy)

        # Flip button
        self.btn_flip = QPushButton("🔄 Playing: White [F6]")
        self.btn_flip.clicked.connect(self.on_flip)
        self._style_button(self.btn_flip, active_color="#30363d", text_color="#e6edf3")
        frame_layout.addWidget(self.btn_flip)

        # Calibrate button
        self.btn_cal = QPushButton("🎯 Calibrate [F2]")
        self.btn_cal.clicked.connect(self.on_recalibrate)
        self._style_button(self.btn_cal, active_color="#30363d", text_color="#e6edf3")
        frame_layout.addWidget(self.btn_cal)

        # Close button
        btn_close = QPushButton("✖")
        btn_close.setFixedWidth(24)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b949e;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #f85149;
            }
        """)
        btn_close.clicked.connect(self.on_close)
        frame_layout.addWidget(btn_close)

        layout.addWidget(self.frame)
        self.adjustSize()

    def update_states(self, show_player: bool, show_enemy: bool, flipped: bool) -> None:
        self.btn_player.setChecked(show_player)
        self.btn_enemy.setChecked(show_enemy)
        if not flipped:
            self.btn_player.setText("🔵 You (White) [F3]")
            self.btn_enemy.setText("🔴 Enemy (Black) [F4]")
            self.btn_flip.setText("🔄 Playing: White [F6]")
        else:
            self.btn_player.setText("🔵 You (Black) [F3]")
            self.btn_enemy.setText("🔴 Enemy (White) [F4]")
            self.btn_flip.setText("🔄 Playing: Black [F6]")

    def position_above_board(self, left: int, top: int, width: int) -> None:
        """Position the control bar centered right above the board."""
        bar_w = self.sizeHint().width()
        bar_x = max(10, left + (width - bar_w) // 2)
        bar_y = max(10, top - 38)
        self.move(bar_x, bar_y)

    def _style_button(self, btn: QPushButton, active_color: str, text_color: str) -> None:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(48, 54, 61, 200);
                color: {text_color};
                border: 1px solid rgba(110, 118, 129, 100);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 139, 253, 60);
                border-color: #58a6ff;
            }}
            QPushButton:checked {{
                background-color: {active_color};
                border-color: {active_color};
                color: #ffffff;
            }}
        """)

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
