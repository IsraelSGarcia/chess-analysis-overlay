"""
_control_bar.py
===============
Floating Control Panel for Chess Capture Visualizer.

Features:
- Generous, spacious drag header with empty space for effortless moving.
- Dedicated button for EVERY shortcut with shortcut key badges.
- Master toggle button (Ctrl+Space / F1).
- Defending pieces toggle (F5).
- Arrow size toggle (F8).
- Board nudge buttons (fine-tune position without recalibrating).
- Clean, modern dark glassmorphism styling.
"""

from __future__ import annotations

from typing import Callable, Tuple, Optional
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel, QFrame,
)


class ControlBar(QWidget):
    """Floating control panel with spacious drag area and complete button system."""

    def __init__(
        self,
        on_toggle_master: Callable[[], None],
        on_toggle_white: Callable[[], None],
        on_toggle_black: Callable[[], None],
        on_toggle_defense: Callable[[], None],
        on_flip: Callable[[], None],
        on_toggle_highlights: Callable[[], None],
        on_toggle_arrow_size: Callable[[], None],
        on_recalibrate: Callable[[], None],
        on_nudge_board: Callable[[int, int], None],
        on_close: Callable[[], None],
    ) -> None:
        super().__init__(None)
        self.on_toggle_master = on_toggle_master
        self.on_toggle_white = on_toggle_white
        self.on_toggle_black = on_toggle_black
        self.on_toggle_defense = on_toggle_defense
        self.on_flip = on_flip
        self.on_toggle_highlights = on_toggle_highlights
        self.on_toggle_arrow_size = on_toggle_arrow_size
        self.on_recalibrate = on_recalibrate
        self.on_nudge_board = on_nudge_board
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
        self.setFixedWidth(560)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(0)

        # Outer card frame
        self.card = QFrame()
        self.card.setStyleSheet("""
            QFrame#card {
                background-color: rgba(20, 24, 32, 245);
                border: 1px solid rgba(75, 95, 125, 200);
                border-radius: 8px;
            }
        """)
        self.card.setObjectName("card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(10, 8, 10, 8)
        card_layout.setSpacing(8)

        # =====================================================================
        # 1. TOP DRAG HEADER (Spacious, easy to grab and move anywhere)
        # =====================================================================
        self.drag_header = QFrame()
        self.drag_header.setFixedHeight(36)
        self.drag_header.setStyleSheet("""
            QFrame {
                background-color: rgba(30, 36, 48, 180);
                border: 1px dashed rgba(80, 110, 150, 150);
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: rgba(40, 48, 64, 220);
                border-color: #58a6ff;
            }
        """)
        self.drag_header.setCursor(Qt.CursorShape.SizeAllCursor)

        header_layout = QHBoxLayout(self.drag_header)
        header_layout.setContentsMargins(12, 0, 8, 0)
        header_layout.setSpacing(8)

        # Title
        title = QLabel("♟ CAPTURE VISUALIZER")
        title.setStyleSheet("color: #58a6ff; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        header_layout.addWidget(title)

        # Wide drag instructions (empty space to click & drag)
        self.drag_hint = QLabel("::: Drag anywhere here to move window :::")
        self.drag_hint.setStyleSheet("color: #8b949e; font-size: 10px; font-style: italic;")
        self.drag_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.drag_hint, stretch=1)

        # Close button
        btn_close = QPushButton("✖")
        btn_close.setFixedSize(22, 22)
        btn_close.setToolTip("Close Visualizer (Esc / F9)")
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(248, 81, 73, 30);
                color: #f85149;
                border: 1px solid rgba(248, 81, 73, 100);
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f85149;
                color: #ffffff;
            }
        """)
        btn_close.clicked.connect(self.on_close)
        header_layout.addWidget(btn_close)

        card_layout.addWidget(self.drag_header)

        # =====================================================================
        # 2. BUTTON GRID (Dedicated button for every shortcut)
        # =====================================================================
        grid = QGridLayout()
        grid.setSpacing(6)

        # Row 1: Primary Action Toggles
        self.btn_master = QPushButton("👁️ Overlay: ON [Ctrl+Space]")
        self.btn_master.setCheckable(True)
        self.btn_master.setChecked(True)
        self.btn_master.clicked.connect(self.on_toggle_master)
        self._style_button(self.btn_master, active_color="#238636", text_color="#ffffff")
        grid.addWidget(self.btn_master, 0, 0)

        self.btn_player = QPushButton("🔵 You (White) [F3]")
        self.btn_player.setCheckable(True)
        self.btn_player.setChecked(True)
        self.btn_player.clicked.connect(self.on_toggle_white)
        self._style_button(self.btn_player, active_color="#388bfd", text_color="#ffffff")
        grid.addWidget(self.btn_player, 0, 1)

        self.btn_enemy = QPushButton("🔴 Enemy (Black) [F4]")
        self.btn_enemy.setCheckable(True)
        self.btn_enemy.setChecked(True)
        self.btn_enemy.clicked.connect(self.on_toggle_black)
        self._style_button(self.btn_enemy, active_color="#f85149", text_color="#ffffff")
        grid.addWidget(self.btn_enemy, 0, 2)

        self.btn_defense = QPushButton("🛡️ Defend: ON [F5]")
        self.btn_defense.setCheckable(True)
        self.btn_defense.setChecked(True)
        self.btn_defense.clicked.connect(self.on_toggle_defense)
        self._style_button(self.btn_defense, active_color="#a371f7", text_color="#ffffff")
        grid.addWidget(self.btn_defense, 0, 3)

        # Row 2: Secondary / View Toggles
        self.btn_flip = QPushButton("🔄 Playing: White [F6]")
        self.btn_flip.clicked.connect(self.on_flip)
        self._style_button(self.btn_flip, active_color="#30363d", text_color="#e6edf3")
        grid.addWidget(self.btn_flip, 1, 0)

        self.btn_hl = QPushButton("🎨 Highlights: ON [F7]")
        self.btn_hl.setCheckable(True)
        self.btn_hl.setChecked(True)
        self.btn_hl.clicked.connect(self.on_toggle_highlights)
        self._style_button(self.btn_hl, active_color="#30363d", text_color="#e6edf3")
        grid.addWidget(self.btn_hl, 1, 1)

        self.btn_size = QPushButton("↕ Arrows: Small [F8]")
        self.btn_size.clicked.connect(self.on_toggle_arrow_size)
        self._style_button(self.btn_size, active_color="#30363d", text_color="#e6edf3")
        grid.addWidget(self.btn_size, 1, 2)

        self.btn_cal = QPushButton("🎯 Calibrate [F2]")
        self.btn_cal.clicked.connect(self.on_recalibrate)
        self._style_button(self.btn_cal, active_color="#d29922", text_color="#ffffff")
        grid.addWidget(self.btn_cal, 1, 3)

        card_layout.addLayout(grid)

        # =====================================================================
        # 3. BOTTOM BAR (Board Nudge Controls & Status)
        # =====================================================================
        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(2, 2, 2, 0)
        bottom_row.setSpacing(6)

        # Nudge label
        lbl_nudge = QLabel("Nudge Board:")
        lbl_nudge.setStyleSheet("color: #8b949e; font-size: 10px;")
        bottom_row.addWidget(lbl_nudge)

        # Nudge buttons
        for text, dx, dy in [("◀", -2, 0), ("▲", 0, -2), ("▼", 0, 2), ("▶", 2, 0)]:
            b = QPushButton(text)
            b.setFixedSize(22, 20)
            b.setStyleSheet("""
                QPushButton {
                    background-color: rgba(48, 54, 61, 180);
                    color: #c9d1d9;
                    border: 1px solid rgba(80, 100, 130, 120);
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: rgba(56, 139, 253, 60);
                    border-color: #58a6ff;
                }
            """)
            b.clicked.connect(lambda _, x=dx, y=dy: self.on_nudge_board(x, y))
            bottom_row.addWidget(b)

        bottom_row.addSpacing(10)

        # Status Label
        self.lbl_status = QLabel("● Live • Ready")
        self.lbl_status.setStyleSheet("color: #3fb950; font-size: 10px; font-weight: bold;")
        bottom_row.addWidget(self.lbl_status, stretch=1)

        card_layout.addLayout(bottom_row)

        main_layout.addWidget(self.card)
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
        arrow_size_mode: str,
        flipped: bool,
    ) -> None:
        # Master toggle
        self.btn_master.setChecked(overlay_visible)
        master_text = "👁️ Overlay: ON [Ctrl+Space]" if overlay_visible else "👁️ Overlay: OFF [Ctrl+Space]"
        self.btn_master.setText(master_text)
        self._style_button(
            self.btn_master,
            active_color="#238636" if overlay_visible else "#30363d",
            text_color="#ffffff" if overlay_visible else "#8b949e",
        )

        # Player & Enemy buttons
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

        # Defending
        self.btn_defense.setChecked(show_defense)
        self.btn_defense.setText("🛡️ Defend: ON [F5]" if show_defense else "🛡️ Defend: OFF [F5]")

        # Highlights
        self.btn_hl.setChecked(show_highlights)
        self.btn_hl.setText("🎨 Highlights: ON [F7]" if show_highlights else "🎨 Highlights: OFF [F7]")

        # Arrow size
        size_name = "Small" if arrow_size_mode == "small" else "Medium"
        self.btn_size.setText(f"↕ Arrows: {size_name} [F8]")

    def set_status_text(self, text: str, ok: bool = True) -> None:
        color = "#3fb950" if ok else "#f85149"
        self.lbl_status.setText(text)
        self.lbl_status.setStyleSheet(f"color: {color}; font-size: 10px; font-weight: bold;")

    def position_above_board(self, left: int, top: int, width: int) -> None:
        """Position the control bar centered above the board."""
        bar_w = self.sizeHint().width()
        bar_x = max(10, left + (width - bar_w) // 2)
        bar_y = max(10, top - self.sizeHint().height() - 10)
        self.move(bar_x, bar_y)

    def _style_button(self, btn: QPushButton, active_color: str, text_color: str) -> None:
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(35, 42, 54, 220);
                color: #c9d1d9;
                border: 1px solid rgba(80, 100, 130, 140);
                border-radius: 5px;
                padding: 6px 10px;
                font-size: 10px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(56, 139, 253, 50);
                border-color: #58a6ff;
                color: #ffffff;
            }}
            QPushButton:checked {{
                background-color: {active_color};
                border-color: {active_color};
                color: {text_color};
            }}
        """)

    # -------------------------------------------------------------------------
    # Drag Handling (Allows clicking & dragging anywhere on the header or card)
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
