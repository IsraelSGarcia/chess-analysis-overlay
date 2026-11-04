"""
_control_bar.py
===============
Minimalist floating toolbar for Chess Capture Visualizer.

Sleek, compact single-row design with comfortable drag area
and clean pill-style buttons.
"""

from __future__ import annotations

from typing import Callable
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QCursor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame,
)


class ControlBar(QWidget):
    """Compact floating pill toolbar with easy drag space and clean buttons."""

    def __init__(
        self,
        on_toggle_master: Callable[[], None],
        on_toggle_white: Callable[[], None],
        on_toggle_black: Callable[[], None],
        on_toggle_defense: Callable[[], None],
        on_flip: Callable[[], None],
        on_toggle_highlights: Callable[[], None],
        on_recalibrate: Callable[[], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(None)
        self.on_toggle_master = on_toggle_master
        self.on_toggle_white = on_toggle_white
        self.on_toggle_black = on_toggle_black
        self.on_toggle_defense = on_toggle_defense
        self.on_flip = on_flip
        self.on_toggle_highlights = on_toggle_highlights
        self.on_recalibrate = on_recalibrate
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
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main floating pill frame
        self.pill = QFrame()
        self.pill.setObjectName("pill")
        self.pill.setStyleSheet("""
            QFrame#pill {
                background-color: rgba(18, 20, 24, 245);
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 10px;
            }
        """)

        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(14, 4, 8, 4)
        pill_layout.setSpacing(6)

        # -----------------------------------------------------------------
        # Drag Grip & Title (Comfortable empty space to grab and move)
        # -----------------------------------------------------------------
        self.grip = QLabel("♟")
        self.grip.setStyleSheet("color: #58a6ff; font-size: 14px; font-weight: bold;")
        self.grip.setCursor(Qt.CursorShape.SizeAllCursor)
        pill_layout.addWidget(self.grip)

        # Clean drag spacer
        self.spacer = QLabel("")
        self.spacer.setFixedWidth(12)
        self.spacer.setCursor(Qt.CursorShape.SizeAllCursor)
        pill_layout.addWidget(self.spacer)

        # -----------------------------------------------------------------
        # Clean Pill Buttons
        # -----------------------------------------------------------------

        # Master toggle
        self.btn_master = QPushButton("👁 ON")
        self.btn_master.setCheckable(True)
        self.btn_master.setChecked(True)
        self.btn_master.setToolTip("Toggle Overlay Visibility (Ctrl+Alt+X)")
        self.btn_master.clicked.connect(self.on_toggle_master)
        self._style_button(self.btn_master, active_bg="#1f6feb", active_color="#ffffff")
        pill_layout.addWidget(self.btn_master)

        # You (Blue)
        self.btn_player = QPushButton("🔵 You")
        self.btn_player.setCheckable(True)
        self.btn_player.setChecked(True)
        self.btn_player.setToolTip("Toggle Your Influence (Ctrl+Alt+A)")
        self.btn_player.clicked.connect(self.on_toggle_white)
        self._style_button(self.btn_player, active_bg="#238636", active_color="#ffffff")
        pill_layout.addWidget(self.btn_player)

        # Enemy (Red)
        self.btn_enemy = QPushButton("🔴 Enemy")
        self.btn_enemy.setCheckable(True)
        self.btn_enemy.setChecked(True)
        self.btn_enemy.setToolTip("Toggle Enemy Influence (Ctrl+Alt+S)")
        self.btn_enemy.clicked.connect(self.on_toggle_black)
        self._style_button(self.btn_enemy, active_bg="#da3633", active_color="#ffffff")
        pill_layout.addWidget(self.btn_enemy)

        # Defend (Purple)
        self.btn_defense = QPushButton("🛡 Defend")
        self.btn_defense.setCheckable(True)
        self.btn_defense.setChecked(True)
        self.btn_defense.setToolTip("Toggle Defending Friendly Pieces (Ctrl+Alt+D)")
        self.btn_defense.clicked.connect(self.on_toggle_defense)
        self._style_button(self.btn_defense, active_bg="#8957e5", active_color="#ffffff")
        pill_layout.addWidget(self.btn_defense)

        # Flip perspective
        self.btn_flip = QPushButton("🔄 Flip")
        self.btn_flip.setToolTip("Flip Perspective White ↔ Black (Ctrl+Alt+F)")
        self.btn_flip.clicked.connect(self.on_flip)
        self._style_button(self.btn_flip, active_bg="#21262d", active_color="#c9d1d9")
        pill_layout.addWidget(self.btn_flip)

        # Highlights toggle
        self.btn_hl = QPushButton("🎨 Grid")
        self.btn_hl.setCheckable(True)
        self.btn_hl.setChecked(True)
        self.btn_hl.setToolTip("Toggle Square Highlights (Ctrl+Alt+H)")
        self.btn_hl.clicked.connect(self.on_toggle_highlights)
        self._style_button(self.btn_hl, active_bg="#30363d", active_color="#c9d1d9")
        pill_layout.addWidget(self.btn_hl)

        # Calibrate
        self.btn_cal = QPushButton("🎯 Calibrate")
        self.btn_cal.setToolTip("Recalibrate Board Region (Ctrl+Alt+C)")
        self.btn_cal.clicked.connect(self.on_recalibrate)
        self._style_button(self.btn_cal, active_bg="#9e6a03", active_color="#ffffff")
        pill_layout.addWidget(self.btn_cal)

        # Close
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(22, 22)
        btn_close.setToolTip("Close Visualizer (Ctrl+Alt+Q)")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #6e7681;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(248, 81, 73, 40);
                color: #f85149;
            }
        """)
        btn_close.clicked.connect(self.on_close)
        pill_layout.addWidget(btn_close)

        layout.addWidget(self.pill)
        self.adjustSize()

    # -------------------------------------------------------------------------
    # State update
    # -------------------------------------------------------------------------

    def update_states(
        self,
        overlay_visible: bool,
        show_player: bool,
        show_enemy: bool,
        show_defense: bool,
        show_highlights: bool,
        flipped: bool,
    ) -> None:
        # Master toggle
        self.btn_master.setChecked(overlay_visible)
        self.btn_master.setText("👁 ON" if overlay_visible else "👁 OFF")
        self._style_button(
            self.btn_master,
            active_bg="#1f6feb" if overlay_visible else "#21262d",
            active_color="#ffffff" if overlay_visible else "#6e7681",
        )

        # Player & Enemy
        self.btn_player.setChecked(show_player)
        self.btn_enemy.setChecked(show_enemy)
        if not flipped:
            self.btn_player.setText("🔵 White")
            self.btn_enemy.setText("🔴 Black")
            self.btn_flip.setText("🔄 White")
        else:
            self.btn_player.setText("🔵 Black")
            self.btn_enemy.setText("🔴 White")
            self.btn_flip.setText("🔄 Black")

        # Defend
        self.btn_defense.setChecked(show_defense)

        # Highlights
        self.btn_hl.setChecked(show_highlights)

    def position_above_board(self, left: int, top: int, width: int) -> None:
        """Position the control bar centered right above the board."""
        bar_w = self.sizeHint().width()
        bar_x = max(10, left + (width - bar_w) // 2)
        bar_y = max(8, top - 48)
        self.move(bar_x, bar_y)

    def _style_button(self, btn: QPushButton, active_bg: str, active_color: str) -> None:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 10);
                color: #8b949e;
                border: 1px solid rgba(255, 255, 255, 20);
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 25);
                color: #c9d1d9;
                border-color: rgba(255, 255, 255, 40);
            }}
            QPushButton:checked {{
                background-color: {active_bg};
                border-color: {active_bg};
                color: {active_color};
            }}
        """)

    # -------------------------------------------------------------------------
    # Drag Handling (Click and drag anywhere on the bar)
    # -------------------------------------------------------------------------

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:
        self._drag_pos = QPoint()
        event.accept()
