"""
_control_bar.py
===============
Minimalist floating toolbar for Chess Capture Visualizer.

Clean, monochromatic single-row design with singular word buttons
and zero emojis or bright colored accents.
"""

from __future__ import annotations

from typing import Callable
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel, QFrame,
)

from chess_visualizer.capture import set_window_capture_exclusion


class ControlBar(QWidget):
    """Monochrome floating toolbar with singular-word minimalist buttons."""

    def __init__(
        self,
        on_toggle_master: Callable[[], None],
        on_toggle_mode: Callable[[], None],
        on_toggle_white: Callable[[], None],
        on_toggle_black: Callable[[], None],
        on_toggle_defense: Callable[[], None],
        on_flip: Callable[[], None],
        on_toggle_highlights: Callable[[], None],
        on_toggle_hud: Callable[[], None],
        on_toggle_auto: Callable[[], None],
        on_recalibrate: Callable[[], None],
        on_close: Callable[[], None],
        on_toggle_turn: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(None)
        self.on_toggle_master = on_toggle_master
        self.on_toggle_mode = on_toggle_mode
        self.on_toggle_white = on_toggle_white
        self.on_toggle_black = on_toggle_black
        self.on_toggle_defense = on_toggle_defense
        self.on_flip = on_flip
        self.on_toggle_highlights = on_toggle_highlights
        self.on_toggle_hud = on_toggle_hud
        self.on_toggle_auto = on_toggle_auto
        self.on_recalibrate = on_recalibrate
        self.on_close = on_close
        self.on_toggle_turn = on_toggle_turn or (lambda: None)

        self._drag_pos = QPoint()
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("Chess Analysis Overlay")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedHeight(38)
        set_window_capture_exclusion(self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main floating pill frame
        self.pill = QFrame()
        self.pill.setObjectName("pill")
        self.pill.setStyleSheet("""
            QFrame#pill {
                background-color: rgba(20, 22, 26, 245);
                border: 1px solid rgba(255, 255, 255, 22);
                border-radius: 6px;
            }
        """)

        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(10, 3, 6, 3)
        pill_layout.setSpacing(5)

        # -----------------------------------------------------------------
        # Minimal Drag Grip & Status Indicator
        # -----------------------------------------------------------------
        self.grip = QLabel("::")
        self.grip.setStyleSheet("color: #4b5260; font-size: 13px; font-weight: bold; margin-right: 4px;")
        self.grip.setCursor(Qt.CursorShape.SizeAllCursor)
        pill_layout.addWidget(self.grip)

        self.lbl_status = QLabel("● Ready")
        self.lbl_status.setStyleSheet("color: #e3b341; font-size: 10px; font-weight: 600; margin-right: 6px;")
        pill_layout.addWidget(self.lbl_status)

        # -----------------------------------------------------------------
        # Minimalist Singular-Word Buttons (Pure Monochrome)
        # -----------------------------------------------------------------

        # Master visibility
        self.btn_master = QPushButton("Overlay")
        self.btn_master.setCheckable(True)
        self.btn_master.setChecked(True)
        self.btn_master.setToolTip("Toggle Overlay Visibility (Ctrl+Alt+X)")
        self.btn_master.clicked.connect(self.on_toggle_master)
        self._style_button(self.btn_master)
        pill_layout.addWidget(self.btn_master)

        # Mode switch: Captures vs Tactics
        self.btn_mode = QPushButton("Tactics")
        self.btn_mode.setToolTip("Switch Mode: Legal Captures vs Tactical Analysis (Ctrl+Alt+M)")
        self.btn_mode.clicked.connect(self.on_toggle_mode)
        self._style_mode_button(self.btn_mode, is_tactics=True)
        pill_layout.addWidget(self.btn_mode)

        # Active turn toggle (Explicit override for White / Black to move)
        self.btn_turn = QPushButton("Turn: White")
        self.btn_turn.setToolTip("Toggle Active Turn: White / Black to move (Ctrl+Alt+W)")
        self.btn_turn.clicked.connect(self.on_toggle_turn)
        self._style_turn_button(self.btn_turn, is_white=True)
        pill_layout.addWidget(self.btn_turn)

        # Player toggle
        self.btn_player = QPushButton("Player")
        self.btn_player.setCheckable(True)
        self.btn_player.setChecked(True)
        self.btn_player.setToolTip("Toggle Player Moves (Ctrl+Alt+A)")
        self.btn_player.clicked.connect(self.on_toggle_white)
        self._style_button(self.btn_player)
        pill_layout.addWidget(self.btn_player)

        # Enemy toggle
        self.btn_enemy = QPushButton("Enemy")
        self.btn_enemy.setCheckable(True)
        self.btn_enemy.setChecked(True)
        self.btn_enemy.setToolTip("Toggle Enemy Moves (Ctrl+Alt+S)")
        self.btn_enemy.clicked.connect(self.on_toggle_black)
        self._style_button(self.btn_enemy)
        pill_layout.addWidget(self.btn_enemy)

        # Defense toggle
        self.btn_defense = QPushButton("Defense")
        self.btn_defense.setCheckable(True)
        self.btn_defense.setChecked(True)
        self.btn_defense.setToolTip("Toggle Defending Friendly Pieces (Ctrl+Alt+D)")
        self.btn_defense.clicked.connect(self.on_toggle_defense)
        self._style_button(self.btn_defense)
        pill_layout.addWidget(self.btn_defense)

        # Flip perspective
        self.btn_flip = QPushButton("Flip")
        self.btn_flip.setToolTip("Flip Colors / Perspective (Ctrl+Alt+F)")
        self.btn_flip.clicked.connect(self.on_flip)
        self._style_button(self.btn_flip)
        pill_layout.addWidget(self.btn_flip)

        # Highlights toggle
        self.btn_hl = QPushButton("Highlights")
        self.btn_hl.setCheckable(True)
        self.btn_hl.setChecked(True)
        self.btn_hl.setToolTip("Toggle Square Highlights (Ctrl+Alt+H)")
        self.btn_hl.clicked.connect(self.on_toggle_highlights)
        self._style_button(self.btn_hl)
        pill_layout.addWidget(self.btn_hl)

        # Tactical HUD toggle
        self.btn_hud = QPushButton("HUD")
        self.btn_hud.setCheckable(True)
        self.btn_hud.setChecked(True)
        self.btn_hud.setToolTip("Toggle Tactical Analysis HUD (Ctrl+Alt+T)")
        self.btn_hud.clicked.connect(self.on_toggle_hud)
        self._style_button(self.btn_hud)
        pill_layout.addWidget(self.btn_hud)

        # Auto-Detect / Auto-Track toggle
        self.btn_auto = QPushButton("Auto")
        self.btn_auto.setCheckable(True)
        self.btn_auto.setChecked(True)
        self.btn_auto.setToolTip("Auto-detect board & hide when absent (Ctrl+Alt+B)")
        self.btn_auto.clicked.connect(self.on_toggle_auto)
        self._style_button(self.btn_auto)
        pill_layout.addWidget(self.btn_auto)

        # Calibrate (Manual fallback)
        self.btn_cal = QPushButton("Calibrate")
        self.btn_cal.setToolTip("Manual Calibration Fallback (Ctrl+Alt+C)")
        self.btn_cal.clicked.connect(self.on_recalibrate)
        self._style_button(self.btn_cal)
        pill_layout.addWidget(self.btn_cal)

        # Close
        btn_close = QPushButton("Close")
        btn_close.setToolTip("Close Visualizer (Ctrl+Alt+Q)")
        self._style_button(btn_close)
        btn_close.clicked.connect(self.on_close)
        pill_layout.addWidget(btn_close)

        layout.addWidget(self.pill)
        self.adjustSize()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        set_window_capture_exclusion(self)

    # -------------------------------------------------------------------------
    # State update
    # -------------------------------------------------------------------------

    def update_states(
        self,
        overlay_visible: bool,
        mode: str,
        show_player: bool,
        show_enemy: bool,
        show_defense: bool,
        show_highlights: bool,
        show_hud: bool,
        auto_track: bool,
        flipped: bool,
        active_turn: bool = True,
    ) -> None:
        self.btn_master.setChecked(overlay_visible)
        is_tac = (mode == "tactics")
        self.btn_mode.setText("Tactics" if is_tac else "Captures")
        self._style_mode_button(self.btn_mode, is_tactics=is_tac)

        # STRICT FEATURE SEPARATION:
        # Hide capture-specific controls in Tactics mode
        self.btn_player.setVisible(not is_tac)
        self.btn_enemy.setVisible(not is_tac)
        self.btn_defense.setVisible(not is_tac)
        self.btn_flip.setVisible(not is_tac)
        self.btn_hl.setVisible(not is_tac)

        # In Tactics mode, display Turn toggle and HUD toggle
        self.btn_hud.setVisible(is_tac)
        self.btn_turn.setVisible(is_tac)
        self.btn_turn.setText("Turn: White" if active_turn else "Turn: Black")
        self._style_turn_button(self.btn_turn, is_white=active_turn)

        self.btn_player.setChecked(show_player)
        self.btn_enemy.setChecked(show_enemy)
        self.btn_defense.setChecked(show_defense)
        self.btn_hl.setChecked(show_highlights)
        self.btn_hud.setChecked(show_hud)
        self.btn_auto.setChecked(auto_track)
        self.adjustSize()

    def _style_turn_button(self, btn: QPushButton, is_white: bool) -> None:
        if is_white:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(255, 255, 255, 28);
                    color: #ffffff;
                    border: 1px solid rgba(255, 255, 255, 90);
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 45);
                    border-color: #ffffff;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(30, 32, 38, 220);
                    color: #e6edf3;
                    border: 1px solid rgba(255, 100, 100, 90);
                    border-radius: 4px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(45, 48, 56, 240);
                    border-color: rgba(255, 120, 120, 160);
                }
            """)

    def _style_mode_button(self, btn: QPushButton, is_tactics: bool) -> None:
        if is_tactics:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(187, 134, 252, 35);
                    color: #d7b7fd;
                    border: 1px solid rgba(187, 134, 252, 100);
                    border-radius: 4px;
                    padding: 3px 9px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(187, 134, 252, 55);
                    color: #ffffff;
                    border-color: rgba(187, 134, 252, 160);
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(45, 145, 255, 35);
                    color: #82bdfb;
                    border: 1px solid rgba(45, 145, 255, 100);
                    border-radius: 4px;
                    padding: 3px 9px;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background-color: rgba(45, 145, 255, 55);
                    color: #ffffff;
                    border-color: rgba(45, 145, 255, 160);
                }
            """)

    def set_status(self, text: str, mode: str = "searching") -> None:
        """Update live status indicator on the toolbar."""
        colors = {
            "searching": "#e3b341",  # amber
            "locked": "#3fb950",     # green
            "manual": "#58a6ff",     # blue
        }
        c = colors.get(mode, "#8b949e")
        self.lbl_status.setStyleSheet(f"color: {c}; font-size: 10px; font-weight: 600; margin-right: 6px;")
        self.lbl_status.setText(f"● {text}")
        self.adjustSize()

    def position_above_board(self, left: int, top: int, width: int) -> None:
        """Position the control bar centered right above the board."""
        bar_w = self.sizeHint().width()
        bar_x = max(10, left + (width - bar_w) // 2)
        bar_y = max(8, top - 44)
        self.move(bar_x, bar_y)

    def _style_button(self, btn: QPushButton) -> None:
        btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #8b929e;
                border: 1px solid rgba(255, 255, 255, 18);
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 18);
                color: #e6edf3;
                border-color: rgba(255, 255, 255, 35);
            }
            QPushButton:checked {
                background-color: rgba(255, 255, 255, 28);
                border-color: rgba(255, 255, 255, 50);
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 38);
                color: #ffffff;
            }
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
